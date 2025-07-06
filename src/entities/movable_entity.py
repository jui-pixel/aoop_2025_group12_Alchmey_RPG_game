# src/entities/movable_entity.py
import pygame
from typing import Tuple, Optional
from src.config import TILE_SIZE
from src.dungeon.dungeon import Dungeon

class MovableEntity(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], game: 'Game', size: int, color: Tuple[int, int, int]):
        super().__init__()
        self.pos = list(pos)  # Starting position as a list for mutability
        self.game = game
        self.dungeon: Dungeon = game.dungeon
        self.speed = 100.0  # Default movement speed in pixels per second
        self.health = 100  # Default health
        self.max_health = 100
        self.size = size
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=self.pos)

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
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        return False