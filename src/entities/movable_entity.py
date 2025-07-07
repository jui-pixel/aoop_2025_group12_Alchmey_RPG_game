# src/entities/movable_entity.py
import pygame
from typing import Tuple, Optional, Dict, Callable
from src.config import TILE_SIZE
from src.dungeon.dungeon import Dungeon

class Buff:
    def __init__(self, name: str, duration: float, effects: Dict[str, float], on_apply: Optional[Callable[['MovableEntity'], None]] = None, on_remove: Optional[Callable[['MovableEntity'], None]] = None):
        self.name = name
        self.duration = duration  # Duration in seconds
        self.remaining_time = duration
        self.effects = effects  # e.g., {"speed_multiplier": 1.5, "health_regen_per_second": 5}
        self.on_apply = on_apply  # Optional callback when buff is applied
        self.on_remove = on_remove  # Optional callback when buff is removed

class MovableEntity(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], game: 'Game', size: int, color: Tuple[int, int, int]):
        super().__init__()
        self.pos = list(pos)
        self.game = game
        self.dungeon: Dungeon = game.dungeon
        self.base_speed = 100.0  # Base movement speed
        self.speed = self.base_speed  # Effective speed after buffs
        self.base_health = 100
        self.health = self.base_health
        self.base_defense = 0  # Base defense value
        self.defense = self.base_defense  # Effective defense after buffs
        self.max_health = 100
        self.size = size
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=self.pos)
        self.buffs: list[Buff] = []  # List of active buffs
        self.buff_modifiers: Dict[str, float] = {"speed_multiplier": 1.0}  # Tracks cumulative buff effects

    def apply_buff(self, buff: Buff) -> None:
        """Apply a buff to the entity."""
        self.buffs.append(buff)
        if buff.on_apply:
            buff.on_apply(self)
        self._update_modifiers()

    def remove_buff(self, buff: Buff) -> None:
        """Remove a buff from the entity."""
        if buff in self.buffs:
            self.buffs.remove(buff)
            if buff.on_remove:
                buff.on_remove(self)
            self._update_modifiers()

    def _update_modifiers(self) -> None:
        """Recalculate cumulative buff effects."""
        speed_multiplier = 1.0
        for buff in self.buffs:
            speed_multiplier *= buff.effects.get("speed_multiplier", 1.0)
        self.buff_modifiers["speed_multiplier"] = speed_multiplier
        self.speed = self.base_speed * self.buff_modifiers["speed_multiplier"]

    def update_buffs(self, dt: float) -> None:
        """Update buff durations and apply ongoing effects."""
        for buff in self.buffs[:]:  # Copy to avoid modifying list during iteration
            buff.remaining_time -= dt
            if buff.remaining_time <= 0:
                self.remove_buff(buff)
            else:
                # Apply ongoing effects like health regeneration
                health_regen = buff.effects.get("health_regen_per_second", 0.0)
                if health_regen > 0:
                    self.health = min(self.max_health, self.health + health_regen * dt)

    def move(self, dx: float, dy: float, dt: float) -> None:
        """Move the entity in the given direction, respecting dungeon boundaries and collisions."""
        if not self.game or not self.dungeon:
            return

        # Normalize direction
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length == 0:
            return
        dx, dy = dx / length, dy / length

        new_x = self.pos[0] + dx * self.speed * dt
        new_y = self.pos[1] + dy * self.speed * dt
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)

        # Dynamic grid expansion
        if tile_x < 0 or tile_y < 0 or tile_x >= self.dungeon.grid_width or tile_y >= self.dungeon.grid_height:
            max_x = max(self.dungeon.grid_width, tile_x + 1)
            max_y = max(self.dungeon.grid_height, tile_y + 1)
            self.dungeon.expand_grid(max_x, max_y)

        # Check for collision with walls
        if (0 <= tile_x < self.dungeon.grid_width and 0 <= tile_y < self.dungeon.grid_height):
            tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
            if tile in ('Room_floor', 'Bridge_floor', 'End_room_floor', 'End_room_portal'):
                self.pos = [new_x, new_y]
                self.rect.center = self.pos
            else:
                # Try moving only in x or y direction to slide along walls
                tile_x = int(self.pos[0] // TILE_SIZE)
                tile_y = int(new_y // TILE_SIZE)
                if (0 <= tile_y < self.dungeon.grid_height and 
                    self.dungeon.dungeon_tiles[tile_y][tile_x] not in ('Border_wall', 'Outside')):
                    self.pos[1] = new_y
                    self.rect.centery = self.pos[1]
                else:
                    tile_x = int(new_x // TILE_SIZE)
                    tile_y = int(self.pos[1] // TILE_SIZE)
                    if (0 <= tile_x < self.dungeon.grid_width and 
                        self.dungeon.dungeon_tiles[tile_y][tile_x] not in ('Border_wall', 'Outside')):
                        self.pos[0] = new_x
                        self.rect.centerx = self.pos[0]

    def take_damage(self, damage: int) -> bool:
        """Apply damage to the entity. Returns True if entity is killed."""
        damage = max(1, damage - self.defense)
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        return False

    def update(self, dt: float, current_time: float) -> None:
        """Update entity state, including buffs."""
        self.update_buffs(dt)