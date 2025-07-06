# src/weapons/weapon.py
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
    def __init__(self, name: str, fire_rate: float, bullet_speed: float, damage: int, max_ammo: int, is_melee: bool = False, melee_range: int = 1):
        self.name = name
        self.fire_rate = fire_rate
        self.bullet_speed = bullet_speed
        self.damage = damage
        self.max_ammo = max_ammo
        self.ammo = max_ammo if not is_melee else float('inf')
        self.is_melee = is_melee
        self.melee_range = melee_range  # Melee range in tiles
        self.last_fired = 0.0  # Last fired time

    def can_fire(self, last_fired: float, current_time: float) -> bool:
        return current_time - last_fired >= self.fire_rate and (self.is_melee or self.ammo > 0)

    def fire(self, pos: Tuple[float, float], direction: Tuple[float, float], current_time: float, dungeon: Dungeon, shooter: Optional['pygame.sprite.Sprite'] = None) -> Optional['Bullet']:
        if not self.can_fire(last_fired=self.last_fired, current_time=current_time):
            return None
        if self.is_melee:
            self.apply_melee_damage(pos, dungeon, shooter)
            return None
        self.ammo -= 1
        self.last_fired = current_time
        return Bullet(pos, direction, self.bullet_speed, self.damage, current_time, dungeon, shooter)

    def apply_melee_damage(self, pos: Tuple[float, float], dungeon: Dungeon, shooter: Optional['pygame.sprite.Sprite'] = None):
        tile_x = int(pos[0] // TILE_SIZE)
        tile_y = int(pos[1] // TILE_SIZE)
        game = dungeon.game
        if not game:
            return
        for dx in range(-self.melee_range, self.melee_range + 1):
            for dy in range(-self.melee_range, self.melee_range + 1):
                check_x = tile_x + dx
                check_y = tile_y + dy
                if 0 <= check_x < dungeon.grid_width and 0 <= check_y < dungeon.grid_height:
                    # Check for enemies in range
                    for enemy in game.enemy_group:
                        enemy_tile_x = int(enemy.pos[0] // TILE_SIZE)
                        enemy_tile_y = int(enemy.pos[1] // TILE_SIZE)
                        if enemy_tile_x == check_x and enemy_tile_y == check_y:
                            enemy.take_damage(self.damage)
                            print(f"Melee hit enemy at ({check_x}, {check_y}) dealing {self.damage} damage")

class Gun(Weapon):
    def __init__(self):
        super().__init__(name="Gun", fire_rate=0.2, bullet_speed=400.0, damage=10, max_ammo=30)

class Bow(Weapon):
    def __init__(self):
        super().__init__(name="Bow", fire_rate=0.5, bullet_speed=300.0, damage=15, max_ammo=20)

class Staff(Weapon):
    def __init__(self):
        super().__init__(name="Staff", fire_rate=1.0, bullet_speed=200.0, damage=20, max_ammo=10)

class Knife(Weapon):
    def __init__(self):
        super().__init__(name="Knife", fire_rate=0.1, bullet_speed=0.0, damage=8, max_ammo=0, is_melee=True, melee_range=2)