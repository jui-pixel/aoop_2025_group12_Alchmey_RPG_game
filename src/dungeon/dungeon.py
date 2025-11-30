# dungeon/dungeon.py
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

# --- 1. 導入數據結構 ---
# 假設這些類別已從原始的 `dungeon.py` 拆分出來
from .room import Room, RoomType # RoomType 假設定義在 room.py 中
from .bridge import Bridge 
from .bsp_node import BSPNode

# --- 2. 導入 Builder 和 Config ---
# 導入建構者 (負責生成流程)
from .builder.dungeon_builder import DungeonBuilder 
# 假設所有配置常數已移動到此處
from .config.dungeon_config import ( 
    GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, 
    TILE_EMPTY, TILE_FLOOR, TILE_WALL, TILE_DOOR
) 

# ======================================================================
#  重構後的 Dungeon 類：僅負責狀態管理與對外接口 (門面)
# ======================================================================

class Dungeon:
    """
    地牢狀態管理與門面類 (Facade)。

    此類負責儲存已生成地牢的所有狀態數據，並提供簡單的接口供遊戲系統存取。
    所有的複雜生成邏輯都委派給 DungeonBuilder 處理。
    """
    
    def __init__(self):
        """
        初始化地牢的資料結構。
        """
        # --- 數據狀態 ---
        self.rooms: List[Room] = []  # 儲存所有房間實例
        self.bridges: List[Bridge] = [] # 儲存橋樑/走廊資訊 (如果需要)
        self.bsp_tree: Optional[BSPNode] = None # 儲存 BSP 樹的根節點
        
        # 地圖網格 (二維列表，儲存瓦片類型字串)
        self.grid_width = GRID_WIDTH 
        self.grid_height = GRID_HEIGHT 
        self.dungeon_tiles: List[List[str]] = [] 
        
        # 雜項狀態
        self.next_room_id = 1 
        self.total_appeared_rooms = 0 

        # --- 核心整合點：Builder ---
        # 創建 DungeonBuilder 實例，並將自身的引用傳遞給它
        self.builder: DungeonBuilder = DungeonBuilder(self) 

    def initialize_dungeon(self) -> None:
        """
        地牢生成入口。委派給 DungeonBuilder 執行整個生成流程。
        這是遊戲系統調用來生成地牢的唯一方法。
        """
        print("Dungeon: 啟動 DungeonBuilder 進行地牢生成...")
        self.builder.initialize_dungeon()
        print("Dungeon: 生成完成，地牢數據已準備就緒。")


    # ==================================================================
    #  門面存取方法 (Facade Accessors)：供遊戲系統/ECS System 使用
    # ==================================================================

    def get_tile(self, x: int, y: int) -> str:
        """
        獲取指定座標的瓦片類型。
        """
        if 0 <= y < self.grid_height and 0 <= x < self.grid_width:
            return self.dungeon_tiles[y][x]
        return TILE_EMPTY # 或 'Outside'

    def is_passable(self, x: int, y: int) -> bool:
        """
        檢查指定座標是否可行走 (用於移動系統)。
        """
        tile = self.get_tile(x, y)
        # 假設在 config 中定義了所有可通行的瓦片類型
        passable_tiles = {TILE_FLOOR, TILE_DOOR} 
        return tile in passable_tiles

    def get_start_position(self) -> Tuple[int, int]:
        """
        回傳玩家的起始房間中心座標 (瓦片座標)。
        """
        try:
            start_room = next(
                r for r in self.rooms if r.room_type == RoomType.START
            )
            # 回傳以 TILE_SIZE 為單位的像素座標，如果需要瓦片座標則移除 * TILE_SIZE
            center_x = int(start_room.x + start_room.width // 2) * TILE_SIZE
            center_y = int(start_room.y + start_room.height // 2) * TILE_SIZE
            return center_x, center_y
        except StopIteration:
            print("警告：未找到起始房間 (RoomType.START)！回傳 (0, 0)。")
            return 0, 0
    
    # ... 您可以根據需要添加其他簡單的數據存取方法 ...