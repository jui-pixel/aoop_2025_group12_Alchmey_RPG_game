from typing import Tuple, Optional, Dict, List
import pygame
import math
from ..movement_entity import MovementEntity
from ..attack_entity import AttackEntity
from ..damage_text import DamageText
from ..buff.buff import Buff
from ...config import TILE_SIZE, PASSABLE_TILES
from ..basic_entity import BasicEntity  # 添加 import

class ExpandingCircleBullet(MovementEntity, AttackEntity):
    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 w: int = TILE_SIZE // 2,
                 h: int = TILE_SIZE // 2,
                 game: 'Game' = None,
                 tag: str = "player_bullet",
                 max_speed: float = 300.0,
                 direction: Tuple[float, float] = (0.0, 0.0),
                 can_move: bool = True,
                 can_attack: bool = True,
                 damage_to_element: Optional[Dict[str, float]] = None,
                 atk_element: str = "untyped",
                 damage: int = 10,
                 max_penetration_count: int = 0,
                 collision_cooldown: float = 0.2,
                 explosion_range: float = 0.0,
                 explosion_damage: int = 0,
                 explosion_element: str = "untyped",
                 explosion_buffs: List['Buff'] = None,
                 outer_radius: float = TILE_SIZE,
                 expansion_duration: float = 1.0):
        # Initialize BasicEntity first
        BasicEntity.__init__(self, x, y, w, h, None, "circle", game, tag)
        
        # Initialize mixins without basic init
        MovementEntity.__init__(self, x, y, w, h, None, "circle", game, tag, max_speed, can_move, pass_wall=True, init_basic=False)
        AttackEntity.__init__(self, x, y, w, h, None, "circle", game, tag, can_attack, damage_to_element,
                              atk_element, damage, 0, 0, 0, True, [], max_penetration_count,
                              collision_cooldown, explosion_range, explosion_damage, explosion_element,
                              explosion_buffs if explosion_buffs else [], init_basic=False)

        # Bullet-specific attributes (無變動)
        self.direction = direction
        self.velocity = (direction[0] * max_speed, direction[1] * max_speed)
        self.lifetime = 5.0
        self.current_penetration_count = 0

        # Circle-specific attributes (無變動)
        self.outer_radius = outer_radius
        self.initial_inner_radius = outer_radius * 0.1
        self.inner_radius = self.initial_inner_radius
        self.expansion_duration = expansion_duration
        self.expansion_time = 0.0
        self.expanded = False  # Tracks if damage has been triggered

        # Create surface for drawing (無變動)
        self.image = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt: float, current_time: float) -> None:
        """Update bullet position, expansion, and check collisions."""
        # Update parent classes
        MovementEntity.update(self, dt, current_time)
        AttackEntity.update(self, dt, current_time)

        # Update lifetime
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.explode(self.game.entity_manager.enemy_group)
            self.kill()
            return

        # Update inner circle expansion
        if not self.expanded:
            self.expansion_time += dt
            expansion_progress = min(self.expansion_time / self.expansion_duration, 1.0)
            self.inner_radius = self.initial_inner_radius + (self.outer_radius - self.initial_inner_radius) * expansion_progress

            # Trigger damage when inner circle reaches outer circle
            if expansion_progress >= 1.0 and not self.expanded:
                self.expanded = True
                self._trigger_area_damage()

        # Update image and rect
        self._update_image()

        # Check collision with walls (if not pass_wall)
        if not self.pass_wall:
            tile_x, tile_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile not in PASSABLE_TILES:
                    self.explode(self.game.entity_manager.enemy_group)
                    self.kill()

    def _update_image(self) -> None:
        """Update the bullet's image with expanding inner circle and fixed outer circle."""
        self.image.fill((0, 0, 0, 0))  # Clear surface with transparent background
        # Draw outer circle (white border, transparent fill)
        pygame.draw.circle(self.image, (255, 255, 255, 128), (self.outer_radius, self.outer_radius), self.outer_radius, 2)
        # Draw inner circle (solid red)
        pygame.draw.circle(self.image, (255, 0, 0), (self.outer_radius, self.outer_radius), self.inner_radius)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def _trigger_area_damage(self) -> None:
        """Trigger damage when inner circle reaches outer circle size."""
        if not self.can_attack:
            return

        center = (self.x, self.y)

        for enemy in self.game.entity_manager.enemy_group:
            if not hasattr(enemy, 'take_damage'):
                continue

            enemy_center = (enemy.x + enemy.w / 2, enemy.y + enemy.h / 2)
            distance = math.sqrt((center[0] - enemy_center[0])**2 + (center[1] - enemy_center[1])**2)

            if distance <= self.outer_radius:
                multiplier = self._damage_to_element.get(self.atk_element, 1.0)
                effective_damage = int(self.damage * multiplier)
                killed, actual_damage = enemy.take_damage(
                    factor=1.0,
                    element=self.atk_element,
                    base_damage=effective_damage,
                    max_hp_percentage_damage=self.max_hp_percentage_damage,
                    current_hp_percentage_damage=self.current_hp_percentage_damage,
                    lose_hp_percentage_damage=self.lose_hp_percentage_damage,
                    cause_death=self.cause_death
                )

                # Add damage text
                if actual_damage > 0:
                    damage_text = DamageText((enemy.x + enemy.w / 2, enemy.y), actual_damage)
                    self.game.entity_manager.damage_text_group.add(damage_text)

                # Apply buffs
                if self.buffs and hasattr(enemy, 'add_buff'):
                    for buff in self.buffs:
                        enemy.add_buff(buff.deepcopy())

        # Increment penetration count
        self.current_penetration_count += 1
        if self.max_penetration_count > 0 and self.current_penetration_count >= self.max_penetration_count:
            self.explode(self.game.entity_manager.enemy_group)
            self.kill()
        else:
            # Reset expansion for next cycle
            self.inner_radius = self.initial_inner_radius
            self.expansion_time = 0.0
            self.expanded = False

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw the bullet with camera offset."""
        screen_x = self.x - camera_offset[0] - self.outer_radius
        screen_y = self.y - camera_offset[1] - self.outer_radius
        screen.blit(self.image, (screen_x, screen_y))

    def explode(self, entities: pygame.sprite.Group) -> None:
        """Trigger explosion and damage nearby entities."""
        if self.explosion_range <= 0:
            return

        explosion_center = (self.x, self.y)
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')

        for entity in entities:
            if not hasattr(entity, 'take_damage'):
                continue

            entity_center = (entity.x + entity.w / 2, entity.y + entity.h / 2)
            distance = math.sqrt(
                (explosion_center[0] - entity_center[0])**2 +
                (explosion_center[1] - entity_center[1])**2
            )

            if distance <= self.explosion_range:
                multiplier = self._damage_to_element.get(self.explosion_element, 1.0)
                effective_explosion_damage = int(self.explosion_damage * multiplier * damage_mult)
                killed, actual_damage = entity.take_damage(
                    factor=1.0,
                    element=self.explosion_element,
                    base_damage=effective_explosion_damage,
                    max_hp_percentage_damage=self.explosion_max_hp_percentage_damage,
                    current_hp_percentage_damage=self.explosion_current_hp_percentage_damage,
                    lose_hp_percentage_damage=self.explosion_lose_hp_percentage_damage,
                    cause_death=self.cause_death
                )
                if actual_damage > 0:
                    damage_text = DamageText((entity.x + entity.w / 2, entity.y), actual_damage)
                    self.game.entity_manager.damage_text_group.add(damage_text)

                if self.explosion_buffs and hasattr(entity, 'add_buff'):
                    for buff in self.explosion_buffs:
                        entity.add_buff(buff.deepcopy())