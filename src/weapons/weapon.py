import pygame
from typing import Tuple, Optional
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
from src.dungeon.dungeon import Dungeon


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], direction: Tuple[float, float], speed: float, fire_time: float, dungeon: Dungeon):
        super().__init__()
        self.pos = list(pos)  # 轉為列表以便修改
        self.direction = direction
        self.speed = speed
        self.fire_time = fire_time
        self.dungeon = dungeon
        self.image = pygame.Surface((4, 5))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt: float) -> bool:
        # 更新子彈位置
        new_x = self.pos[0] + self.direction[0] * self.speed * dt
        new_y = self.pos[1] + self.direction[1] * self.speed * dt
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)

        # 檢查是否撞到牆壁或超出地牢邊界
        if (0 <= tile_x < self.dungeon.grid_width and 0 <= tile_y < self.dungeon.grid_height):
            if self.dungeon.dungeon_tiles[tile_y][tile_x] == 'Border_wall':
                return False
        else:
            return False

        # 檢查子彈是否在螢幕可見範圍內
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
    def __init__(self, name: str, fire_rate: float, bullet_speed: float, max_ammo: int, is_melee: bool = False, melee_range: int = 1):
        self.name = name
        self.fire_rate = fire_rate
        self.bullet_speed = bullet_speed
        self.max_ammo = max_ammo
        self.ammo = max_ammo if not is_melee else float('inf')
        self.is_melee = is_melee
        self.melee_range = melee_range  # 近戰範圍（以瓦片為單位）
        self.last_fired = 0.0  # 上次開火時間

    def can_fire(self, last_fired: float, current_time: float) -> bool:
        return current_time - last_fired >= self.fire_rate and (self.is_melee or self.ammo > 0)

    def fire(self, pos: Tuple[float, float], direction: Tuple[float, float], current_time: float, dungeon: Dungeon) -> Optional[Bullet]:
        if not self.can_fire(last_fired=self.last_fired, current_time=current_time):
            return None
        if self.is_melee:
            self.apply_melee_damage(pos, dungeon)
            return None
        self.ammo -= 1
        self.last_fired = current_time
        return Bullet(pos, direction, self.bullet_speed, current_time, dungeon)

    def apply_melee_damage(self, pos: Tuple[float, float], dungeon: Dungeon):
        tile_x = int(pos[0] // TILE_SIZE)
        tile_y = int(pos[1] // TILE_SIZE)
        for dx in range(-self.melee_range, self.melee_range + 1):
            for dy in range(-self.melee_range, self.melee_range + 1):
                check_x = tile_x + dx
                check_y = tile_y + dy
                if (0 <= check_x < dungeon.grid_width and 0 <= check_y < dungeon.grid_height):
                    if dungeon.dungeon_tiles[check_y][check_x] in ('Border_wall'):
                        print(f"Melee hit at ({check_x}, {check_y})")  # 未來可添加敵人傷害邏輯


class Gun(Weapon):
    def __init__(self):
        super().__init__(name="Gun", fire_rate=0.2, bullet_speed=400.0, max_ammo=30)


class Bow(Weapon):
    def __init__(self):
        super().__init__(name="Bow", fire_rate=0.5, bullet_speed=300.0, max_ammo=20)


class Staff(Weapon):
    def __init__(self):
        super().__init__(name="Staff", fire_rate=1.0, bullet_speed=200.0, max_ammo=10)


class Knife(Weapon):
    def __init__(self):
        super().__init__(name="Knife", fire_rate=0.1, bullet_speed=0.0, max_ammo=0, is_melee=True, melee_range=2)