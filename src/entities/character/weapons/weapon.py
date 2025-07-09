import pygame
from typing import Tuple, Optional
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
from src.dungeon.dungeon import Dungeon

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], direction: Tuple[float, float], speed: float, damage: int, fire_time: float, dungeon: Dungeon, shooter: Optional['pygame.sprite.Sprite'] = None):
        super().__init__()
        self.pos = list(pos)  # Convert to list for modification
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.fire_time = fire_time
        self.dungeon = dungeon
        self.shooter = shooter
        self.image = pygame.Surface((4, 5))
        self.image.fill((255, 255, 0))  # Yellow color for bullet
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt: float) -> bool:
        # Update bullet position
        new_x = self.pos[0] + self.direction[0] * self.speed * dt
        new_y = self.pos[1] + self.direction[1] * self.speed * dt
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)

        # Check for collision with walls or out-of-bounds
        if (0 <= tile_x < self.dungeon.grid_width and 0 <= tile_y < self.dungeon.grid_height):
            if self.dungeon.dungeon_tiles[tile_y][tile_x] in ('Border_wall', 'Outside'):
                return False
        else:
            return False

        # Check if bullet is within screen bounds
        camera_offset = getattr(self.dungeon.game, 'camera_offset', [0, 0]) if hasattr(self.dungeon, 'game') else [0, 0]
        screen_left = -camera_offset[0]
        screen_right = screen_left + SCREEN_WIDTH
        screen_top = -camera_offset[1]
        screen_bottom = screen_top + SCREEN_HEIGHT

        if screen_left <= new_x <= screen_right and screen_top <= new_y <= screen_bottom:
            self.pos = [new_x, new_y]
            self.rect.center = self.pos
            return True
        return False

class Weapon:
    def __init__(self, name: str, fire_rate: float, bullet_speed: float, damage: int, energy_cost: float):
        self.name = name
        self.fire_rate = fire_rate
        self.bullet_speed = bullet_speed
        self.damage = damage
        self.energy_cost = energy_cost
        self.last_fired = 0.0  # Last fired time

    def can_fire(self, last_fired: float, current_time: float, player_energy: float) -> bool:
        return current_time - last_fired >= self.fire_rate and (player_energy >= self.energy_cost)

    def fire(self, pos: Tuple[float, float], direction: Tuple[float, float], current_time: float, dungeon: Dungeon, shooter: Optional['pygame.sprite.Sprite'] = None) -> Optional['Bullet']:
        if not self.can_fire(last_fired=self.last_fired, current_time=current_time, player_energy=shooter.energy if shooter else 0):
            return None
        self.last_fired = current_time
        return Bullet(pos, direction, self.bullet_speed, self.damage, current_time, dungeon, shooter)

class Gun(Weapon):
    def __init__(self):
        super().__init__(name="Gun", fire_rate=0.2, bullet_speed=400.0, damage=10, energy_cost=5.0)

class Staff(Weapon):
    def __init__(self):
        super().__init__(name="Staff", fire_rate=1.0, bullet_speed=200.0, damage=20, energy_cost=12.0)