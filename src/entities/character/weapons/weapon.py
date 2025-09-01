import pygame
from typing import Tuple, Optional, Set
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
from src.dungeon.dungeon import Dungeon
from src.entities.buff import Buff
from src.entities.element_buff_library import ELEMENTBUFFLIBRARY
import math


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], direction: Tuple[float, float], speed: float, damage: int, 
                 fire_time: float, dungeon: 'Dungeon', shooter: Optional['pygame.sprite.Sprite'] = None, 
                 lifetime: float = 2.0, penetrating: bool = False, effects: Optional[list[Buff]] = None,
                 cooldown: float = 1.0):
        super().__init__()
        self.pos = list(pos)
        self.direction = direction
        self.base_speed = speed
        self.speed = speed
        self.base_damage = damage
        self.damage = damage
        self.fire_time = fire_time
        self.dungeon = dungeon
        self.shooter = shooter
        self.lifetime = lifetime
        self.elapsed_time = 0.0
        self.element = 'untyped'
        self.effects = effects if effects is not None else []
        self.penetrating = penetrating  # Default to non-penetrating bullet
        self.image = pygame.Surface((4, 5))
        self.image.fill((255, 255, 0))  # Yellow color for bullet
        self.rect = self.image.get_rect(center=self.pos)
        self.hit_enemies: dict[int, float] = dict()
        self.cooldown = cooldown

    def update(self, dt: float) -> bool:
        """Update bullet position and buffs. Return False if bullet should be removed."""
        self.elapsed_time += dt
        if self.elapsed_time >= self.lifetime:
            return False

        # 計算新位置
        dx = self.direction[0] * self.speed * dt
        dy = self.direction[1] * self.speed * dt
        new_x = self.pos[0] + dx
        new_y = self.pos[1] + dy

        # 檢查與牆壁的碰撞
        if not self.check_wall_collision(self.pos, [new_x, new_y]):
            return False

        # 更新位置
        self.pos = [new_x, new_y]
        self.rect.center = self.pos

        # 檢查是否在屏幕範圍內
        camera_offset = getattr(self.dungeon.game, 'camera_offset', [0, 0]) if hasattr(self.dungeon, 'game') else [0, 0]
        screen_left = -camera_offset[0]
        screen_right = screen_left + SCREEN_WIDTH
        screen_top = -camera_offset[1]
        screen_bottom = screen_top + SCREEN_HEIGHT

        if screen_left <= new_x <= screen_right and screen_top <= new_y <= screen_bottom:
            return True
        return False

    def check_wall_collision(self, start_pos: list, end_pos: list) -> bool:
        """檢查子彈移動路徑是否與牆壁碰撞"""
        # 計算移動向量
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        steps = max(abs(dx), abs(dy)) / (TILE_SIZE / 4)  # 每1/4格子檢查一次
        if steps == 0:
            return True

        step_x = dx / steps
        step_y = dy / steps

        # 沿路徑檢查每個點
        current_x, current_y = start_pos
        for _ in range(int(steps) + 1):
            tile_x = int(current_x // TILE_SIZE)
            tile_y = int(current_y // TILE_SIZE)

            if (0 <= tile_x < self.dungeon.grid_width and 0 <= tile_y < self.dungeon.grid_height):
                if self.dungeon.dungeon_tiles[tile_y][tile_x] in ('Border_wall', 'Outside'):
                    return False
            else:
                return False

            current_x += step_x
            current_y += step_y

        return True
    
    def check_collision(self, enemy: 'pygame.sprite.Sprite', current_time: float) -> Tuple[bool, int]:
        """Check if bullet collides with an enemy and hasn't hit it recently."""
        enemy_id = id(enemy)
        if enemy_id in self.hit_enemies and current_time - self.hit_enemies[enemy_id] < self.cooldown:
            return False, 0
        if self.rect.colliderect(enemy.rect):
            self.hit_enemies[enemy_id] = current_time
            hitted, damage = enemy.take_hit(self)
            return hitted, damage
        return False, 0


class ParabolicBullet(Bullet):
    def __init__(self, pos: Tuple[float, float], target_pos: Tuple[float, float], speed: float, damage: int, 
                 fire_time: float, dungeon: 'Dungeon', shooter: Optional['pygame.sprite.Sprite'] = None, 
                 lifetime: float = 2.0, penetrating: bool = False, effects: Optional[list[Buff]] = None,
                 explosion_radius: float = 50.0, cooldown: float = 1.0):
        super().__init__(pos, (0, 0), speed, damage, fire_time, dungeon, shooter, lifetime, penetrating, effects, cooldown)
        self.target_pos = target_pos
        self.gravity = 980.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.initialized = False
        self.reached_target = False
        self.explosion_radius = explosion_radius
        self.travel_time = 0.0
        self.effect_duration = lifetime
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 100, 0))
        self.rect = self.image.get_rect(center=self.pos)
        self.initialize_trajectory()

    def initialize_trajectory(self):
        """Calculate initial velocity for parabolic trajectory and set lifetime."""
        dx = self.target_pos[0] - self.pos[0]
        dy = self.target_pos[1] - self.pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            self.velocity_x = 0
            self.velocity_y = 0
            self.travel_time = 0.0
            self.lifetime = self.effect_duration
            return

        self.travel_time = distance / 400.0
        self.velocity_x = dx / self.travel_time
        self.velocity_y = (dy - 0.5 * self.gravity * self.travel_time**2) / self.travel_time
        self.lifetime = self.travel_time + self.effect_duration
        self.initialized = True

    def update(self, dt: float) -> bool:
        """Update fireball position with parabolic motion and handle fire sea effect."""
        if not self.initialized:
            return False

        self.elapsed_time += dt
        if self.elapsed_time >= self.lifetime:
            return False
        if self.elapsed_time >= self.travel_time and not self.reached_target:
            self.reached_target = True
            self.pos = list(self.target_pos)  # Snap to target position
            self.velocity_x = 0
            self.velocity_y = 0
            # Enlarge for fire sea effect, align with explosion_radius
            sprite_size = int(self.explosion_radius * 2)  # Diameter = 2 * radius
            self.image = pygame.Surface((sprite_size, sprite_size))
            self.image.fill((255, 100, 0))
            self.rect = self.image.get_rect(center=self.pos)


        if not self.reached_target:
            # Move in parabolic trajectory
            self.pos[0] += self.velocity_x * dt
            self.velocity_y += self.gravity * dt
            self.pos[1] += self.velocity_y * dt
            
        # Keep fireball on screen during effect_duration
        camera_offset = getattr(self.dungeon.game, 'camera_offset', [0, 0]) if hasattr(self.dungeon, 'game') else [0, 0]
        screen_left = -camera_offset[0]
        screen_right = screen_left + SCREEN_WIDTH
        screen_top = -camera_offset[1]
        screen_bottom = screen_top + SCREEN_HEIGHT

        if screen_left <= self.pos[0] <= screen_right and screen_top <= self.pos[1] <= screen_bottom:
            self.rect.center = self.pos
            return True
        return True

    def check_collision(self, enemy: 'pygame.sprite.Sprite', current_time: float) -> Tuple[bool, int]:
        """Check if enemy is within explosion radius when target is reached."""
        if not self.reached_target:
            return False, 0
        enemy_id = id(enemy)
        if enemy_id in self.hit_enemies and current_time - self.hit_enemies[enemy_id] < self.cooldown:
            return False, 0
        distance = math.sqrt((self.pos[0] - enemy.rect.centerx)**2 + (self.pos[1] - enemy.rect.centery)**2)
        if distance <= self.explosion_radius:
            self.hit_enemies[enemy_id] = current_time
            hitted, damage = enemy.take_hit(self)
            return hitted, damage
        return False, 0
    

class Weapon:
    def __init__(self, name: str, fire_rate: float, bullet_speed: float, damage: int, 
                 energy_cost: float, penetrating: bool = False, bullet_type: type = Bullet, effects: Optional[list[Buff]] = None):
        self.name = name
        self.original_fire_rate = fire_rate
        self.fire_rate = fire_rate
        self.bullet_speed = bullet_speed
        self.damage = damage
        self.energy_cost = energy_cost
        self.bullet_type = bullet_type
        self.penetrating = penetrating  # Default to non-penetrating bullets
        self.last_fired = 0.0
        self.effects = effects if effects is not None else []  # Optional effect to apply when firing

    def can_fire(self, current_time: float, player_energy: float) -> bool:
        return current_time - self.last_fired >= self.fire_rate and player_energy >= self.energy_cost

    def fire(self, pos: Tuple[float, float], direction: Tuple[float, float], current_time: float, 
             dungeon: Dungeon, shooter: Optional['pygame.sprite.Sprite'] , target_position: Tuple[float, float]) -> Optional['Bullet']:
        if not self.can_fire(current_time=current_time, player_energy=shooter.energy if shooter else 0):
            return None
        self.last_fired = current_time
        return self.bullet_type(pos, direction, self.bullet_speed, self.damage, current_time, dungeon, shooter, penetrating = self.penetrating, effects=self.effects)

class Gun(Weapon):
    def __init__(self):
        super().__init__(name="Gun", fire_rate=0.2, bullet_speed=600.0, damage=100, energy_cost=5.0, bullet_type=Bullet)

class Staff(Weapon):
    def __init__(self):
        super().__init__(name="Staff", fire_rate=0.1, bullet_speed=200.0, damage=20, energy_cost=1.0, bullet_type=Bullet)

class WaterGun(Weapon):
    def __init__(self):
        super().__init__(name="Water Gun", fire_rate=0.3, bullet_speed=500.0, damage=0, 
                        energy_cost=7.0, bullet_type=Bullet, penetrating=True, effects=[ELEMENTBUFFLIBRARY['Humid']])
        
class IceGun(Weapon):
    def __init__(self):
        super().__init__(name="Ice Gun", fire_rate=0.3, bullet_speed=500.0, damage=0, 
                        energy_cost=7.0, bullet_type=Bullet, penetrating=True, effects=[ELEMENTBUFFLIBRARY['Cold']])
        
class Fireball(Weapon):
    def __init__(self):
        super().__init__(
            name="Fireball",
            fire_rate=0.5,
            bullet_speed=0.0,
            damage=6,
            energy_cost=10.0,
            bullet_type=ParabolicBullet,
            penetrating=True,
            effects=[ELEMENTBUFFLIBRARY['Burn']]
        )
        self.explosion_radius = 50.0

    def fire(self, pos: Tuple[float, float], direction: Tuple[float, float], current_time: float, 
             dungeon: Dungeon, shooter: Optional['pygame.sprite.Sprite'], target_position: Tuple[float, float]) -> Optional['ParabolicBullet']:
        if not self.can_fire(current_time=current_time, player_energy=shooter.energy if shooter else 0):
            return None
        self.last_fired = current_time
        return self.bullet_type(
            pos=pos,
            target_pos=target_position,
            speed=0.0,
            damage=self.damage,
            fire_time=current_time,
            dungeon=dungeon,
            shooter=shooter,
            lifetime=1.0,  # Will be overridden in initialize_trajectory
            penetrating=self.penetrating,
            effects=self.effects,
            explosion_radius=self.explosion_radius,
            cooldown=0.1,
        )