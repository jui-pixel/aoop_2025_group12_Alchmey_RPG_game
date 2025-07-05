from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame
from src.weapons.weapon import Weapon, Bullet
from src.skills.skill import Skill
from src.dungeon.dungeon import Dungeon
from src.config import TILE_SIZE, MAX_WEAPONS_DEFAULT


@dataclass
class Player(pygame.sprite.Sprite):
    pos: Tuple[float, float]
    speed: float = 300.0
    health: int = 100
    max_health: int = 100
    weapons: List[Weapon] = None
    current_weapon_idx: int = 0
    skill: Optional[Skill] = None
    max_weapons: int = MAX_WEAPONS_DEFAULT
    last_fired: float = 0.0
    invulnerable: float = 0.0
    direction: Tuple[float, float] = (0.0, 0.0)  # 玩家當前方向
    game: Optional['Game'] = None

    def __post_init__(self):
        super().__init__()
        if self.weapons is None:
            self.weapons = []
        self.image = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2))  # 8x8 像素
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(center=self.pos)

    def move(self, dx: float, dy: float, dt: float, room: 'Room') -> None:
        if not self.game or not self.game.dungeon:
            return
        dungeon = self.game.dungeon
        new_x = self.pos[0] + dx * self.speed * dt
        new_y = self.pos[1] + dy * self.speed * dt
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)
        global_tile_x = tile_x
        global_tile_y = tile_y

        # 動態擴展地圖
        if global_tile_x < 0 or global_tile_y < 0 or global_tile_x >= dungeon.grid_width or global_tile_y >= dungeon.grid_height:
            # min_x = min(0, global_tile_x)
            # min_y = min(0, global_tile_y)
            max_x = max(dungeon.grid_width, global_tile_x + 1)
            max_y = max(dungeon.grid_height, global_tile_y + 1)
            dungeon.expand_grid(max_x, max_y)

        # 更新 global 座標
        global_tile_x = tile_x
        global_tile_y = tile_y
        
        # 穿牆模式
        self.pos = (new_x, new_y)
        self.rect.center = self.pos
        self.direction = (dx, dy)
        
        # # 檢查新位置是否在地圖範圍內
        # if (0 <= global_tile_x < dungeon.grid_width and 0 <= global_tile_y < dungeon.grid_height):

        #     tile = dungeon.dungeon_tiles[global_tile_y][global_tile_x]
        #     if tile in ('Room_floor', 'Bridge_floor', 'End_room_floor', 'End_room_portal'):
        #         self.pos = (new_x, new_y)
        #         self.rect.center = self.pos
        #     else:
        #         print(f"Blocked: tile at ({global_tile_x}, {global_tile_y}) is {tile}")
        # else:
        #     print(f"Out of bounds: tile_x={global_tile_x}, tile_y={global_tile_y}")

    def fire(self, direction: Tuple[float, float], current_time: float) -> Optional['Bullet']:
        weapon = self.weapons[self.current_weapon_idx] if self.weapons else None
        if weapon and weapon.can_fire(self.last_fired, current_time) and self.game and self.game.dungeon:
            bullet = weapon.fire(self.pos, direction, current_time, self.game.dungeon)
            if bullet:
                self.last_fired = current_time
            return bullet
        return None
