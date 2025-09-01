import pygame
import copy
import math
from typing import Tuple, Optional, Dict, Callable, List
from src.config import TILE_SIZE, PASSABLE_TILES
from src.dungeon.dungeon import Dungeon
from src.entities.buff import Buff
from src.entities.element_buff_library import ELEMENTBUFFLIBRARY

class MovableEntity(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], game: 'Game', size: int, color: Tuple[int, int, int], 
                 base_speed: float = 100.0, base_health: int = 100, base_defense: int = 0, base_vision_radius: int = 8,
                 element: str = 'untyped', untyped_resistance: float = 0.0, light_resistance: float = 0.0, 
                 dark_resistance: float = 0.0, metal_resistance: float = 0.0, wood_resistance: float = 0.0, 
                 water_resistance: float = 0.0, fire_resistance: float = 0.0, earth_resistance: float = 0.0, 
                 ice_resistance: float = 0.0, electric_resistance: float = 0.0, wind_resistance: float = 0.0):
        super().__init__()
        self.pos = list(pos)
        self.game = game
        self.dungeon: Dungeon = game.dungeon
        self.base_speed = base_speed  # Base maximum movement speed
        self.speed = self.base_speed  # Effective speed after buffs
        self.base_health = base_health
        self.health = self.base_health
        self.base_defense = base_defense  # Base defense value
        self.eff_defense = self.base_defense  # Effective defense after buffs
        self.max_health = self.base_health
        self.size = size
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=self.pos)
        self.buffs: list[Buff] = []  # List of active buffs
        self.buff_modifiers: Dict[str, float] = {"speed_multiplier": 1.0}  # Tracks cumulative buff effects
        self.base_vision_radius = base_vision_radius  # Base vision radius
        self.vision_radius = self.base_vision_radius
        self.invulnerable: float = 0.0
        self.element = element
        self.paralysis = False  # Paralysis state
        self.freeze = False  # Freeze state
        self.petrochemical = False
        self.canfire = lambda: not (self.paralysis or self.freeze or self.petrochemical)
        self.untyped_resistance = untyped_resistance
        self.light_resistance = light_resistance
        self.dark_resistance = dark_resistance
        self.metal_resistance = metal_resistance
        self.wood_resistance = wood_resistance
        self.water_resistance = water_resistance
        self.fire_resistance = fire_resistance
        self.earth_resistance = earth_resistance
        self.ice_resistance = ice_resistance
        self.electric_resistance = electric_resistance
        self.wind_resistance = wind_resistance
        self.id = id(self)  # Unique identifier for the entity
        # Acceleration-related attributes
        self.velocity = [0.0, 0.0]  # Current velocity (x, y)
        self.acceleration = 1000.0  # Acceleration rate (pixels/s^2)
        self.deceleration = 1000.0  # Deceleration rate (pixels/s^2) for friction
        self.turn_boost = 2.0  # Multiplier for acceleration when reversing direction

    def draw_health_bar(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw a health bar above the entity."""
        if self.health <= 0:
            return
        # Health bar dimensions
        bar_width = self.size
        bar_height = 5
        bar_x = self.rect.x + camera_offset[0]
        bar_y = self.rect.y + camera_offset[1] - 10  # 10 pixels above entity
        # Background (red)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Foreground (green), scaled by health percentage
        health_ratio = max(0, self.health / self.max_health)
        health_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))

    def elemental_buff_merge(self) -> None:
        humid = ELEMENTBUFFLIBRARY.get("Humid", None)
        for buff in self.buffs:
            if buff.name == "Humid":
                humid = buff
                break
        if humid and humid in self.buffs:
            dist = ELEMENTBUFFLIBRARY.get("Dist", None)
            cold = ELEMENTBUFFLIBRARY.get("Cold", None)
            for buff in self.buffs:
                if buff.name == "Dist":
                    dist = buff
                elif buff.name == "Cold":
                    cold = buff
            if dist and dist in self.buffs:
                self.remove_buff(dist)
                self.remove_buff(humid)
                self.apply_buff(ELEMENTBUFFLIBRARY["Mud"].deepcopy())
                print("Merge Humid and Dist to Mud")
            elif cold and cold in self.buffs:
                self.remove_buff(cold)
                self.remove_buff(humid)
                self.apply_buff(ELEMENTBUFFLIBRARY["Freeze"].deepcopy())
                print("Merge Humid and Cold to Freeze")
                
        mud = ELEMENTBUFFLIBRARY.get("Mud", None)
        for buff in self.buffs:
            if buff.name == "Mud":
                mud = buff
                break
        if mud and mud in self.buffs:
            burn = ELEMENTBUFFLIBRARY.get("Burn", None)
            for buff in self.buffs:
                if buff.name == "Burn":
                    burn = buff
            if burn and burn in self.buffs:
                self.remove_buff(mud)
                self.remove_buff(burn)
                self.apply_buff(ELEMENTBUFFLIBRARY["Petrochemical"].deepcopy())
                print("Merge Mud and Burn to Petrochemical")

    def apply_buff(self, buff: Buff) -> None:
        """Apply a buff to the entity, replacing any existing buff with the same name, using a copy to avoid modifying the original."""
        buff_copy = copy.deepcopy(buff)
        for existing_buff in self.buffs[:]:
            if existing_buff.name == buff_copy.name:
                self.buffs.remove(existing_buff)
                if existing_buff.on_remove:
                    existing_buff.on_remove(self)
                print(f"Removed existing buff {existing_buff.name} before applying new one")
        self.buffs.append(buff_copy)
        if buff_copy.on_apply:
            buff_copy.on_apply(self)
        self.update_modifiers()
        print(f"Applied new buff {buff_copy.name} with duration {buff_copy.remaining_time}")

    def remove_buff(self, buff: Buff) -> None:
        """Remove a buff from the entity."""
        if buff in self.buffs:
            self.buffs.remove(buff)
            if buff.on_remove:
                buff.on_remove(self)
            self.update_modifiers()
            print(f"Removed buff {buff.name}")

    def update_modifiers(self) -> None:
        """Recalculate cumulative buff effects."""
        vision_radius_multiplier = 1.0
        speed_multiplier = 1.0
        defense_multiplier = 1.0
        for buff in self.buffs:
            vision_radius_multiplier *= buff.effects.get("vision_radius_multiplier", 1.0)
            speed_multiplier *= buff.effects.get("speed_multiplier", 1.0)
            defense_multiplier *= buff.effects.get("defense_multiplier", 1.0)
        self.vision_radius = int(self.base_vision_radius * vision_radius_multiplier)
        self.speed = self.base_speed * speed_multiplier
        self.eff_defense = int(self.base_defense * defense_multiplier)
        
    def update_buffs(self, dt: float) -> None:
        """Update buff durations and apply ongoing effects."""
        self.elemental_buff_merge()
        for buff in self.buffs[:]:
            print(f"Updating buff {buff.name}, remaining time: {buff.remaining_time}")
            buff.remaining_time -= dt
            if buff.remaining_time <= 0:
                self.remove_buff(buff)
                print(f"Buff {buff.name} expired")
            else:
                health_regen = buff.effects.get("health_regen_per_second", 0.0)
                if health_regen > 0:
                    self.health = max(1, min(self.max_health, self.health + health_regen * dt))
                    print(f"Applied health regen from {buff.name}: {health_regen * dt} HP")
                elif health_regen < 0 and self.invulnerable < 0.001:
                    self.health = max(1, min(self.max_health, self.health + health_regen * dt))
                    print(f"Applied health regen from {buff.name}: {health_regen * dt} HP")

    def move(self, dx: float, dy: float, dt: float) -> None:
        """以加速運動移動實體，考慮地牢邊界、地塊碰撞與實體碰撞，加強反向轉向速度。"""
        if not self.game or not self.dungeon or self.paralysis or self.freeze or self.petrochemical:
            self.velocity = [0.0, 0.0]
            return

        # 無輸入時減速
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length == 0:
            vel_length = (self.velocity[0] ** 2 + self.velocity[1] ** 2) ** 0.5
            if vel_length > 0:
                new_vel_length = max(0, vel_length - self.deceleration * dt)
                self.velocity = [self.velocity[0] * new_vel_length / vel_length if vel_length > 0 else 0.0,
                                self.velocity[1] * new_vel_length / vel_length if vel_length > 0 else 0.0]
        else:
            # 施加加速，檢查是否反向
            dx, dy = dx / length, dy / length
            vel_length = (self.velocity[0] ** 2 + self.velocity[1] ** 2) ** 0.5
            if vel_length > 0:
                # 計算輸入方向與當前速度方向的夾角
                input_dir = [dx, dy]
                vel_dir = [self.velocity[0] / vel_length, self.velocity[1] / vel_length]
                dot_product = input_dir[0] * vel_dir[0] + input_dir[1] * vel_dir[1]
                cos_angle = max(min(dot_product, 1.0), -1.0)  # 限制範圍避免浮點誤差
                # 若接近反向（夾角接近180度），增加加速並減弱當前速度
                if cos_angle < -0.5:  # 夾角大於120度
                    self.velocity[0] *= 0.5  # 減弱當前速度以加快反向
                    self.velocity[1] *= 0.5
                    accel = self.acceleration * self.turn_boost
                else:
                    accel = self.acceleration
            else:
                accel = self.acceleration

            self.velocity[0] += dx * accel * dt
            self.velocity[1] += dy * accel * dt

        # 限制速度
        vel_length = (self.velocity[0] ** 2 + self.velocity[1] ** 2) ** 0.5
        if vel_length > self.speed:
            self.velocity = [self.velocity[0] * self.speed / vel_length, self.velocity[1] * self.speed / vel_length]

        # 計算新位置
        new_x, new_y = self.pos[0] + self.velocity[0] * dt, self.pos[1] + self.velocity[1] * dt
        new_rect = self.rect.copy()
        new_rect.center = (new_x, new_y)

        # 處理實體碰撞
        for other in self.game.enemy_group:
            if other.id != self.id and new_rect.colliderect(other.rect):
                repel_dx, repel_dy = self.pos[0] - other.pos[0], self.pos[1] - other.pos[1]
                repel_length = (repel_dx ** 2 + repel_dy ** 2) ** 0.5 or 1
                repel_dx, repel_dy = repel_dx / repel_length, repel_dy / repel_length
                repel_factor = min(500.0 / repel_length, self.speed)
                new_x += repel_dx * repel_factor * dt
                new_y += repel_dy * repel_factor * dt

        # 檢查地圖邊界並擴展
        tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
        if tile_x < 0 or tile_y < 0 or tile_x >= self.dungeon.grid_width or tile_y >= self.dungeon.grid_height:
            self.dungeon.expand_grid(max(self.dungeon.grid_width, tile_x + 1), max(self.dungeon.grid_height, tile_y + 1))

        # 處理地塊碰撞
        if 0 <= tile_x < self.dungeon.grid_width and 0 <= tile_y < self.dungeon.grid_height:
            tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
            if tile in PASSABLE_TILES:
                self.pos = [new_x, new_y]
                self.rect.center = self.pos
            else:
                # 嘗試沿X或Y軸滑動
                y_allowed = 0 <= int(new_y // TILE_SIZE) < self.dungeon.grid_height and \
                            self.dungeon.dungeon_tiles[int(new_y // TILE_SIZE)][int(self.pos[0] // TILE_SIZE)] in PASSABLE_TILES
                x_allowed = 0 <= int(new_x // TILE_SIZE) < self.dungeon.grid_width and \
                            self.dungeon.dungeon_tiles[int(self.pos[1] // TILE_SIZE)][int(new_x // TILE_SIZE)] in PASSABLE_TILES

                if y_allowed:
                    self.pos[1] = new_y
                    self.rect.centery = new_y
                    self.velocity[1] *= max(0, 1 - self.deceleration * dt / self.speed)
                if x_allowed:
                    self.pos[0] = new_x
                    self.rect.centerx = new_x
                    self.velocity[0] *= max(0, 1 - self.deceleration * dt / self.speed)
                if not (x_allowed or y_allowed):
                    self.velocity = [self.velocity[0] * max(0, 1 - self.deceleration * dt / self.speed),
                                    self.velocity[1] * max(0, 1 - self.deceleration * dt / self.speed)]

    def take_hit(self, bullet: 'Bullet') -> Tuple[bool, int]:
        """Handle being hit by a bullet. Returns (killed, damage)."""
        if self.invulnerable > 0:
            return False, 0
        if bullet.effects:
            for effect in bullet.effects:
                effect_copy = copy.deepcopy(effect)
                self.apply_buff(effect_copy)
                print(f"Applied effect {effect_copy.name} to {self.__class__.__name__}")
                print(f"Effect details: {effect_copy.effects}, Remaining time: {effect_copy.remaining_time}")
        killed, damage = self.take_damage(bullet.damage, bullet.element)
        if bullet.penetrating:
            return False, damage
        return True, damage
    
    def take_damage(self, damage: int, element: str) -> Tuple[bool, int]:
        """Apply damage to the entity, considering elemental resistance and affinity. Returns (killed, damage)."""
        affinity_multiplier = 1.0
        if element != 'untyped' and self.element != 'untyped':
            if (element == 'light' and self.element == 'dark') or (element == 'dark' and self.element == 'light'):
                affinity_multiplier = 1.5
            elif (element == 'metal' and self.element == 'wood') or \
                 (element == 'wood' and self.element == 'earth') or \
                 (element == 'earth' and self.element == 'water') or \
                 (element == 'water' and self.element == 'fire') or \
                 (element == 'fire' and self.element == 'metal'):
                affinity_multiplier = 1.5
            elif (element == 'earth' and self.element == 'electric') or \
                 (element == 'wood' and self.element == 'wind') or \
                 (element == 'fire' and self.element == 'ice'):
                affinity_multiplier = 1.5

        resistance = getattr(self, f"{element}_resistance", 0.0)
        final_damage = max(1, int(damage * affinity_multiplier * (1.0 - resistance)) - self.eff_defense)
        self.health -= final_damage
        if self.health <= 0:
            self.kill()
            return True, final_damage
        return False, final_damage

    def update(self, dt: float, current_time: float) -> None:
        """Update entity state, including buffs."""
        self.update_buffs(dt)
    
    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if not isinstance(other, pygame.sprite.Sprite):
            return False
        return self.id == other.id