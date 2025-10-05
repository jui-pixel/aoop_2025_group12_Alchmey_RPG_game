# src/entities/bullet/bullet.py
from typing import Tuple, Optional, Dict, List
import pygame
import math
from ..movement_entity import MovementEntity
from ..attack_entity import AttackEntity
from ..damage_text import DamageText
from ..buff.buff import Buff
from ...config import TILE_SIZE, PASSABLE_TILES
from ..basic_entity import BasicEntity  # 添加 import

class Bullet(MovementEntity, AttackEntity):
    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 w: int = TILE_SIZE // 4,
                 h: int = TILE_SIZE // 4,
                 image: Optional[pygame.Surface] = None,
                 shape: str = "rect",
                 game: 'Game' = None,
                 tag: str = "player",
                 max_speed: float = 300.0,
                 direction: Tuple[float, float] = (0.0, 0.0),
                 can_move: bool = True,
                 can_attack: bool = True,
                 buffs: List['Buff'] = None,
                 damage_to_element: Optional[Dict[str, float]] = None,
                 atk_element: str = "untyped",
                 damage: int = 10,
                 max_hp_percentage_damage: int = 0,
                 current_hp_percentage_damage: int = 0,
                 lose_hp_percentage_damage: int = 0,
                 cause_death: bool = True,
                 max_penetration_count: int = 0,
                 collision_cooldown: float = 0.2,
                 explosion_range: float = 0.0,
                 explosion_damage: int = 0,
                 explosion_max_hp_percentage_damage : int = 0,
                 explosion_current_hp_percentage_damage : int = 0,
                 explosion_lose_hp_percentage_damage : int = 0,
                 explosion_element: str = "untyped",
                 explosion_buffs: List['Buff'] = None,
                 pass_wall: bool = False):
        # Initialize BasicEntity first
        BasicEntity.__init__(self, x, y, w, h, image, shape, game, tag)
        
        # Initialize mixins without basic init
        MovementEntity.__init__(self, x, y, w, h, image, shape, game, tag, max_speed, can_move, pass_wall, init_basic=False)
        AttackEntity.__init__(self, x, y, w, h, image, shape, game, tag, can_attack, damage_to_element,
                              atk_element, damage, max_hp_percentage_damage, current_hp_percentage_damage, lose_hp_percentage_damage, True, buffs, max_penetration_count,
                              collision_cooldown, explosion_range, explosion_damage, explosion_element,
                              explosion_buffs if explosion_buffs else [], explosion_max_hp_percentage_damage, explosion_max_hp_percentage_damage, explosion_max_hp_percentage_damage, init_basic=False)

        self.tag = tag
        # Bullet-specific attributes (無變動)
        self.direction = direction  # Normalized direction vector
        self.velocity = (direction[0] * max_speed, direction[1] * max_speed)
        self.lifetime = 5.0  # Bullet expires after 5 seconds
        self.current_penetration_count = 0

        # Hit tracking (無變動)
        self.hitted_entities = set()  # Set of hit enemy IDs
        self.last_hit_times = {}  # Dict: enemy_id -> last_hit_time

        # Default image if none provided (無變動)
        if not image:
            self.image = pygame.Surface((w, h))
            self.image.fill((255, 255, 0))  # Yellow bullet
            self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt: float, current_time: float) -> None:
        """Update bullet position, check collisions, and handle lifetime."""
        # Update parent classes
        # AttackEntity.update(self, dt, current_time)

        if self.can_move:
            self.move(self.direction[0], self.direction[1], dt)
        
        # Update lifetime
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.explode(self.game.entity_manager.entity_group)
            self.kill()
            return

        # Check collisions with enemies
        if self.can_attack:
            for enemy in self.game.entity_manager.entity_group:
                if self.rect.colliderect(enemy.rect):
                    self._handle_collision(enemy, current_time)

        # Check collision with walls (if not pass_wall)
        if not self._pass_wall:
            tile_x, tile_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile not in PASSABLE_TILES:
                    self.explode(self.game.entity_manager.entity_group)
                    self.kill()

    def _handle_collision(self, enemy: 'BasicEnemy', current_time: float) -> None:
        """Handle collision with an enemy, with hit tracking and cooldown."""
        enemy_id = id(enemy)  # Use enemy ID for tracking

        if enemy.tag == self.tag:
            return  # Skip if same tag (e.g., player bullet hitting player)
        # Check if already hit this enemy
        if enemy_id in self.hitted_entities:
            return  # Skip if already hit

        # Check cooldown for this enemy
        if enemy_id in self.last_hit_times:
            time_since_last_hit = current_time - self.last_hit_times[enemy_id]
            if time_since_last_hit < self.collision_cooldown:
                return  # Skip if cooldown not expired

        # Mark as hit and record time
        self.hitted_entities.add(enemy_id)
        self.last_hit_times[enemy_id] = current_time

        if not hasattr(enemy, 'take_damage'):
            return

        # Apply damage
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
        if self.current_penetration_count >= self.max_penetration_count and self.max_penetration_count > 0:
            self.explode(self.game.entity_manager.entity_group)
            self.kill()

    def explode(self, entities: pygame.sprite.Group) -> None:
        """Trigger explosion and damage nearby entities."""
        if self.explosion_range <= 0:
            return
        
        explosion_center = (self.x + self.w / 2, self.y + self.h / 2)
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')

        for entity in entities:
            if not hasattr(entity, 'take_damage'):
                continue
            if self.tag == entity.tag:
                continue  # Prevent self-damage or friendly fire

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

                if self.explosion_buffs and hasattr(entity, 'add_buff'):
                    for buff in self.explosion_buffs:
                        entity.add_buff(buff.deepcopy())

        # Clear hit tracking after explosion
        self.hitted_entities.clear()
        self.last_hit_times.clear()
        
    def move(self, dx: float, dy: float, dt: float) -> None:
        """Update velocity based on input direction and handle movement."""  # 無變動
        if dx != 0 or dy != 0:
            magnitude = math.sqrt(dx**2 + dy**2)
            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude
            self.velocity = (dx * self.max_speed, dy * self.max_speed)

        new_x = self.x + self.velocity[0] * dt
        new_y = self.y + self.velocity[1] * dt
        
        if not self._pass_wall:
            tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile in PASSABLE_TILES:
                    self.set_position(new_x, new_y)
                else:
                    self.kill()
        else:
            self.set_position(new_x, new_y)