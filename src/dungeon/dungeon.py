# dungeon/dungeon.py
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

# --- 1. 導入數據結構 ---
# 假設這些類別已從原始的 `dungeon.py` 拆分出來
from .room import Room 
from .bridge import Bridge 
from .bsp_node import BSPNode

# --- 2. 導入 Builder 和 Config (已修正) ---
from .builder.dungeon_builder import DungeonBuilder 
from .config.dungeon_config import ( 
    DungeonConfig, RoomType, # 導入 DungeonConfig 類和 RoomType Enum
    TILE_OUTSIDE, TILE_FLOOR, TILE_DOOR # 導入核心瓦片字串常量 (用於方法簽名或回傳值)
) 
# 注意：舊的 GRID_WIDTH, GRID_HEIGHT 等現在是透過 DungeonConfig 實例訪問

# ======================================================================
#  重構後的 Dungeon 類：僅負責狀態管理與對外接口 (門面)
# ======================================================================

class Dungeon:
    """
    地牢狀態管理與門面類 (Facade)。
    
    此類負責儲存已生成地牢的所有狀態數據，並提供簡單的接口供遊戲系統存取。
    所有的複雜生成邏輯都委派給 DungeonBuilder 處理。
    """
    
    def __init__(self, config: Optional[DungeonConfig] = None):
        """
        初始化地牢的資料結構。
        可選擇性傳入 DungeonConfig 實例，否則使用默認配置。
        """
        # --- 配置管理 (新整合點) ---
        # 優先使用傳入的配置，否則創建一個默認配置
        self.config: DungeonConfig = config if config is not None else DungeonConfig()
        
        # --- 數據狀態 ---
        self.rooms: List[Room] = []  
        self.bridges: List[Bridge] = []  
        self.bsp_tree: Optional[BSPNode] = None  
        
        # 從配置中讀取網格尺寸
        self.grid_width = self.config.grid_width  
        self.grid_height = self.config.grid_height  
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
        """
        print("Dungeon: 啟動 DungeonBuilder 進行地牢生成...")
        # 注意：DungeonBuilder 必須已被修改以接收 Dungeon 實例，並從 self.dungeon.config 中讀取參數
        self.builder.initialize_dungeon()
        print("Dungeon: 生成完成，地牢數據已準備就緒。")


    # ==================================================================
    #  門面存取方法 (Facade Accessors)：供遊戲系統/ECS System 使用
    # ==================================================================

    def get_tile(self, x: int, y: int) -> str:
        """
        獲取指定座標的瓦片類型。
        """
        # 使用 self.grid_width/height 進行邊界檢查
        if 0 <= y < self.grid_height and 0 <= x < self.grid_width:
            return self.dungeon_tiles[y][x]
        # 使用配置中定義的外部瓦片常量
        return TILE_OUTSIDE 

    def is_passable(self, x: int, y: int) -> bool:
        """
        檢查指定座標是否可行走 (用於移動系統)。
        (調用 Config 類提供的強化方法來判斷通行性)
        """
        tile = self.get_tile(x, y)
        return self.config.is_tile_passable(tile)


    def get_start_position(self) -> Tuple[int, int]:
        """
        回傳玩家的起始房間中心座標 (像素座標)。
        """
        try:
            # 使用 RoomType Enum 來查找起始房間
            start_room = next(
                r for r in self.rooms if r.room_type == RoomType.START
            )
            
            # 使用 config.tile_size 進行座標轉換
            tile_size = self.config.tile_size
            
            # 回傳以 TILE_SIZE 為單位的像素座標
            center_x = int(start_room.x + start_room.width // 2) * tile_size
            center_y = int(start_room.y + start_room.height // 2) * tile_size
            return center_x, center_y
        except StopIteration:
            print("警告：未找到起始房間 (RoomType.START)！回傳 (0, 0)。")
            return 0, 0