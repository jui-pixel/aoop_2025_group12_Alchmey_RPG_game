# dungeon/dungeon.py
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import pygame 
import os # 用於路徑操作 (雖然主要在 ResourceLoader 中使用)

# --- 1. 導入數據結構 ---
from .room import Room 
from .bridge import Bridge 
from .bsp_node import BSPNode

# --- 2. 導入 Builder 和 Config ---
from .builder.dungeon_builder import DungeonBuilder 
from .config.dungeon_config import ( 
    DungeonConfig, RoomType, 
    TILE_OUTSIDE, TILE_FLOOR, TILE_DOOR, TILE_WALL 
) 

# --- 3. 導入 Pygame 相關常數 (假設來自頂層 src/config.py) ---
try:
    # 這些常數用於繪圖方法中的屏幕尺寸和回退顏色
    from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, GRAY, BLACK, DARK_GRAY 
except ImportError:
    print("警告：無法導入 src.config 中的屏幕/顏色常量。使用默認值。")
    SCREEN_WIDTH, SCREEN_HEIGHT = 1400, 750
    GRAY, BLACK, DARK_GRAY = (100, 100, 100), (0, 0, 0), (40, 40, 40)

from src.utils.helpers import load_background_tileset, load_foreground_tileset, get_project_path
# ======================================================================
#  Dungeon 類：狀態管理、門面與繪圖接口
# ======================================================================

class Dungeon:
    """
    地牢狀態管理與門面類 (Facade)。
    """
    
    def __init__(self, config: Optional[DungeonConfig] = None):
        """
        初始化地牢的資料結構。
        """
        # --- 配置管理 ---
        self.config: DungeonConfig = config if config is not None else DungeonConfig()
        
        # --- 數據狀態 ---
        self.rooms: List[Room] = []  
        self.bridges: List[Bridge] = []  
        self.bsp_tree: Optional[BSPNode] = None  
        
        self.grid_width = self.config.grid_width  
        self.grid_height = self.config.grid_height  
        self.dungeon_tiles: List[List[str]] = [] 
        
        self.next_room_id = 1  
        self.total_appeared_rooms = 0  

        # --- 貼圖集資源 (由 ResourceLoader 注入) ---
        self.background_tileset: Optional[Dict[str, pygame.Surface]] = load_background_tileset(self.config, get_project_path)
        self.foreground_tileset: Optional[Dict[str, pygame.Surface]] = load_foreground_tileset(self.config, get_project_path)

        # --- 核心整合點：Builder ---
        self.builder: DungeonBuilder = DungeonBuilder(self.config) 

    def initialize_dungeon(self, dungeon_id: int) -> None:
        """地牢生成入口。委派給 DungeonBuilder 執行整個生成流程。"""
        print("Dungeon: 啟動 DungeonBuilder 進行地牢生成...")
        self.builder = DungeonBuilder(self.config)  # 使用當前配置初始化 Builder
        self.builder.initialize_dungeon(dungeon_id)
        self.dungeon_tiles = self.builder.tile_manager.grid
        print("Dungeon: 生成完成，地牢數據已準備就緒。")

    def initialize_lobby(self) -> None:
        """
        僅初始化一個大廳房間的地牢 (常用於遊戲起始點)。
        注意：此方法調用 DungeonBuilder 的內部方法，體現 Dungeon 作為門面。
        """
        # 1. 重設狀態，並使用 Builder 的網格初始化方法
        self.builder._initialize_grid()
        self.rooms = []
        self.bridges = []
        self.next_room_id = 0
        
        # 2. 從 Config 中獲取大廳尺寸
        lobby_width = self.config.lobby_width
        lobby_height = self.config.lobby_height
        
        # 3. 計算大廳左上位置
        lobby_x = 2
        lobby_y = 2
        
        # 4. 生成並放置房間 (委派給 Builder)
        lobby_room = self.builder.generate_room(
            lobby_x, lobby_y, lobby_width, lobby_height, self.next_room_id, RoomType.LOBBY
        )
        
        self.next_room_id += 1
        self.rooms.append(lobby_room)
        self.total_appeared_rooms = len(self.rooms)
        
        self.builder._place_room(lobby_room) 
        self.builder._add_walls() 
        self.builder.adjust_wall() 
        self.dungeon_tiles = self.builder.tile_manager.grid
        
        print(f"初始化大廳：房間 {lobby_room.id} 在 ({lobby_x}, {lobby_y})，尺寸 {lobby_width}x{lobby_height}")


    def set_tilesets(self, background_ts: Dict[str, pygame.Surface], foreground_ts: Dict[str, pygame.Surface]) -> None:
        """設置地牢所需的貼圖集。"""
        self.background_tileset = background_ts
        self.foreground_tileset = foreground_ts
    
    # ==================================================================
    #  繪圖接口 (Drawing Accessors)
    # ==================================================================

    def draw_background(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """
        Draw the dungeon background tiles, optimized by camera clipping.
        """
        print("Dungeon: 繪製背景瓦片...")
        offset_x, offset_y = camera_offset
        tile_size = self.config.tile_size # 使用配置
        
        if not self.background_tileset: return
        if not self.dungeon_tiles: return
        # 計算瓦片範圍: 攝影機視圖 + 2 瓦片緩衝區
        start_tile_x = max(0, int((offset_x - 2 * tile_size) / tile_size))
        end_tile_x = min(self.grid_width, int((offset_x + SCREEN_WIDTH + 2 * tile_size) / tile_size))
        start_tile_y = max(0, int((offset_y - 2 * tile_size) / tile_size))
        end_tile_y = min(self.grid_height, int((offset_y + SCREEN_HEIGHT + 2 * tile_size) / tile_size))

        # 繪製背景瓦片
        for tile_y in range(start_tile_y, end_tile_y):
            for tile_x in range(start_tile_x, end_tile_x):
                # 安全邊界檢查
                if not (0 <= tile_y < self.grid_height and 0 <= tile_x < self.grid_width): continue
                tile_type = self.dungeon_tiles[tile_y][tile_x]
                tile_image = self.background_tileset.get(tile_type, None)
                screen_x = tile_x * tile_size - offset_x
                screen_y = tile_y * tile_size - offset_y

                if tile_image:
                    screen.blit(tile_image, (screen_x, screen_y))
                    # print(f"繪製瓦片 {tile_type} 在屏幕位置 ({screen_x}, {screen_y})")
                else:
                    # 回退到彩色矩形，使用配置中的通行性判斷
                    is_passable = self.config.is_tile_passable(tile_type)
                    import random
                    color = GRAY if is_passable else random.choice([BLACK, DARK_GRAY])
                    pygame.draw.rect(screen, color, (screen_x, screen_y, tile_size, tile_size))

    def draw_foreground(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """
        Draw the dungeon foreground walls (2.5D effect).
        """
        return
        offset_x, offset_y = camera_offset
        tile_size = self.config.tile_size # 使用配置
        half_tile = tile_size * 0.5
        
        if not self.foreground_tileset: return
        if not self.dungeon_tiles: return
        # 瓦片範圍計算與背景相同 (使用 SCREEN_WIDTH, SCREEN_HEIGHT)
        start_tile_x = max(0, int((offset_x - 2 * tile_size) / tile_size))
        end_tile_x = min(self.grid_width, int((offset_x + SCREEN_WIDTH + 2 * tile_size) / tile_size))
        start_tile_y = max(0, int((offset_y - 2 * tile_size) / tile_size))
        end_tile_y = min(self.grid_height, int((offset_y + SCREEN_HEIGHT + 2 * tile_size) / tile_size))

        # 繪製牆壁作為前景 (不可通行瓦片)
        for tile_y in range(start_tile_y, end_tile_y):
            for tile_x in range(start_tile_x, end_tile_x):
                if not (0 <= tile_y < self.grid_height and 0 <= tile_x < self.grid_width): continue
                     
                tile_type = self.dungeon_tiles[tile_y][tile_x]
                
                # 繪製所有不可通行的瓦片
                if not self.config.is_tile_passable(tile_type):
                    tile_image = self.foreground_tileset.get(tile_type, None)
                    screen_x = tile_x * tile_size - offset_x
                    
                    # 2.5D 效果：將牆壁向上偏移半個瓦片高度
                    screen_y = (tile_y * tile_size - offset_y) - half_tile 
                    
                    if tile_image:
                        wall_image = tile_image
                        screen.blit(wall_image, (screen_x, screen_y))
                    else:
                        # 回退到彩色矩形
                        wall_color = DARK_GRAY # 牆壁使用 DARK_GRAY
                        # 注意這裡的矩形繪製是完整的瓦片大小，但位置上移了 half_tile
                        pygame.draw.rect(screen, wall_color, (screen_x, screen_y, tile_size, tile_size))


    # --- 門面存取方法 (保持不變) ---

    def get_tile(self, x: int, y: int) -> str:
        # ... (邏輯不變)
        if 0 <= y < self.grid_height and 0 <= x < self.grid_width:
            return self.dungeon_tiles[y][x]
        return TILE_OUTSIDE 

    def is_passable(self, x: int, y: int) -> bool:
        # ... (邏輯不變)
        tile = self.get_tile(x, y)
        return self.config.is_tile_passable(tile)


    def get_start_position(self) -> Tuple[int, int]:
        # ... (邏輯不變)
        try:
            start_room = next(
                r for r in self.rooms if r.room_type == RoomType.START
            )
            
            tile_size = self.config.tile_size
            
            center_x = int(start_room.x + start_room.width // 2) * tile_size
            center_y = int(start_room.y + start_room.height // 2) * tile_size
            return center_x, center_y
        except StopIteration:
            print("警告：未找到起始房間 (RoomType.START)！回傳 (0, 0)。")
            return 0, 0