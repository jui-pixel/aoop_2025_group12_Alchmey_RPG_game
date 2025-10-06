import pygame
import math
from typing import Tuple, Optional, Dict, List
import os
from ..movement_entity import MovementEntity
from ..attack_entity import AttackEntity
from ..damage_text import DamageText
from ..buff.buff import Buff
from ...config import TILE_SIZE, PASSABLE_TILES
from ..basic_entity import BasicEntity

def get_project_path(*subpaths):
    """Get the absolute path to the project root (roguelike_dungeon/) and join subpaths."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(project_root, *subpaths)

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
                 explosion_max_hp_percentage_damage: int = 0,
                 explosion_current_hp_percentage_damage: int = 0,
                 explosion_lose_hp_percentage_damage: int = 0,
                 explosion_element: str = "untyped",
                 explosion_buffs: List['Buff'] = None,
                 outer_radius: float = TILE_SIZE,
                 expansion_duration: float = 1.0,
                 wait_time: float = 0.0,
                 lifetime: float = 5.0,
                 hide_time: float = 0.0):
        # Initialize BasicEntity first
        BasicEntity.__init__(self, x, y, w, h, None, "circle", game, tag)
        
        # Initialize mixins without basic init
        MovementEntity.__init__(self, x, y, w, h, None, "circle", game, tag, max_speed, can_move, pass_wall=True, init_basic=False)
        AttackEntity.__init__(self, x, y, w, h, None, "circle", game, tag, can_attack, damage_to_element,
                              atk_element, damage, 0, 0, 0, True, [], max_penetration_count,
                              collision_cooldown, explosion_range, explosion_damage, explosion_element,
                              explosion_buffs if explosion_buffs else [], explosion_max_hp_percentage_damage, 
                              explosion_current_hp_percentage_damage, explosion_lose_hp_percentage_damage, init_basic=False)

        self._pass_wall = True  # Bullets can pass through walls
        self.tag = tag
        # Bullet-specific attributes
        self.direction = direction
        self.velocity = (direction[0] * max_speed, direction[1] * max_speed)
        self.hide_time = hide_time  # Hidden time before wait_time starts
        self.is_hidden = hide_time > 0  # Tracks if bullet is hidden
        self.wait_time = wait_time
        self.lifetime = lifetime

        # Circle-specific attributes
        self.outer_radius = outer_radius
        self.initial_inner_radius = outer_radius * 0.1
        self.inner_radius = self.initial_inner_radius
        self.expansion_duration = expansion_duration
        self.expansion_time = 0.0
        self.expanded = False  # Tracks if expansion is complete
        self.explosion_animation_time = 0.0  # Tracks explosion animation progress
        self.explosion_animation_done = False  # Tracks if explosion animation is complete

        # Load animation frames
        self.animation_frames = []
        for i in range(9):  # effect2_5_0 to effect2_5_8
            frame_path = get_project_path("src", "assets", "bullets", f"effect2_5_{i}.png")
            try:
                frame = pygame.image.load(frame_path).convert_alpha()
                frame = pygame.transform.scale(frame, (int(outer_radius * 2), int(outer_radius * 2)))
                self.animation_frames.append(frame)
            except Exception as e:
                print(f"無法載入動畫圖片 {frame_path}: {e}")
                self.animation_frames.append(pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA))

        # Initialize surface for drawing
        self.image = pygame.Surface((outer_radius * 2, outer_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt: float, current_time: float) -> None:
        """Update bullet position, expansion, explosion animation, and check collisions."""
        if self.is_hidden:
            self.hide_time -= dt
            if self.hide_time <= 0:
                self.is_hidden = False
            return

        if self.wait_time > 0:
            self.wait_time -= dt
            self._update_image()
            return

        # Update parent classes
        MovementEntity.update(self, dt, current_time)
        AttackEntity.update(self, dt, current_time)

        # Update lifetime
        self.lifetime -= dt
        if self.lifetime <= 0:
            if not self.expanded:
                self.expanded = True
                self.explode()
            if self.explosion_animation_done:
                self.kill()
                return

        # Update inner circle expansion or explosion animation
        if not self.expanded:
            self.expansion_time += dt
            expansion_progress = min(self.expansion_time / self.expansion_duration, 1.0)
            self.inner_radius = self.initial_inner_radius + (self.outer_radius - self.initial_inner_radius) * expansion_progress

            if expansion_progress >= 1.0:
                self.expanded = True
                self.explode()

        elif not self.explosion_animation_done:
            self.explosion_animation_time += dt
            if self.explosion_animation_time >= self.expansion_duration:
                self.explosion_animation_done = True
                self.kill()
                return

        # Update image and rect
        self._update_image()

        # Check collision with walls (if not pass_wall)
        if not self._pass_wall:
            tile_x, tile_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile not in PASSABLE_TILES:
                    if not self.expanded:
                        self.expanded = True
                        self.explode()
                    if self.explosion_animation_done:
                        self.kill()

    def _update_image(self) -> None:
        """Update the bullet's image with animation frames based on expansion or explosion progress."""
        self.image.fill((0, 0, 0, 0))  # Clear surface with transparent background

        if not self.expanded:
            # Expansion phase: map expansion_progress [0, 1] to frames 0-3
            expansion_progress = min(self.expansion_time / self.expansion_duration, 1.0)
            frame_index = int(expansion_progress * 4)  # 0 to 3
            frame_index = min(frame_index, 3)  # Ensure not to exceed frame 3
        else:
            # Explosion phase: map explosion_animation_time [0, expansion_duration] to frames 4-8
            explosion_progress = min(self.explosion_animation_time / self.expansion_duration, 1.0)
            frame_index = 4 + int(explosion_progress * 5)  # 4 to 8
            frame_index = min(frame_index, 8)  # Ensure not to exceed frame 8

        # Draw the selected frame
        self.image.blit(self.animation_frames[frame_index], (0, 0))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw the bullet with camera offset, skip if hidden."""
        if self.is_hidden:
            return
        screen_x = self.x - camera_offset[0] - self.outer_radius
        screen_y = self.y - camera_offset[1] - self.outer_radius
        screen.blit(self.image, (screen_x, screen_y))

    def explode(self) -> None:
        """Trigger explosion and damage nearby entities."""
        if self.explosion_range <= 0:
            return
        entities = self.game.entity_manager.entity_group
        explosion_center = (self.x, self.y)
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
                print(f"ExpandingCircleBullet: {self.tag} explosion hits {entity.tag} at distance {distance:.2f}")
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