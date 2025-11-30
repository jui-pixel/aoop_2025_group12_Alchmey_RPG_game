from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple
from enum import Enum

# 假設定義 RoomType 來自其他文件
class RoomType(Enum):
    """房間類型定義 (僅作參考，實際應在 room.py 中)"""
    EMPTY = 'Empty_room'
    START = 'Start_room'
    END = 'End_room'
    LOBBY = 'Lobby_room'
    MONSTER = 'Monster_room'
    TRAP = 'Trap_room'
    REWARD = 'Reward_room'
    NORMAL = 'Normal_room'
    NPC = 'NPC_room'


# ======================================================================
# 核心地牢瓦片常量定義 (Tiling Constants)
# 確保所有地牢相關模組都使用這些標準字串
# ======================================================================

TILE_OUTSIDE = 'Outside'
TILE_FLOOR = 'Room_floor'
TILE_BRIDGE = 'Bridge_floor'
TILE_DOOR = 'Door'
TILE_WALL = 'Border_wall'
TILE_PLAYER_SPAWN = 'Player_spawn'
TILE_END_PORTAL = 'End_room_portal'

# ======================================================================
# DungeonConfig Dataclass
# ======================================================================

@dataclass
class DungeonConfig:
    """
    地牢生成配置

    集中管理所有地牢生成相關的參數，提供驗證和查詢功能。
    """
    
    # ========== 網格尺寸 ==========
    grid_width: int = 120
    """地牢網格寬度（瓦片數）"""
    
    grid_height: int = 100
    """地牢網格高度（瓦片數）"""
    
    tile_size: int = 32
    """每個瓦片的像素大小"""

    # ========== 房間尺寸 & BSP 參數 ==========
    room_width: int = 20
    """單個房間的最大寬度（瓦片數）"""
    
    room_height: int = 20
    """單個房間的最大高度（瓦片數）"""
    
    min_room_size: int = 15
    """房間的最小尺寸（寬度和高度）"""
    
    room_gap: int = 2
    """房間之間的最小間距（瓦片數）"""
    
    max_split_depth: int = 6
    """BSP 分割的最大深度（控制生成房間的數量）"""
    
    min_split_size: Optional[int] = None
    """BSP 分割的最小尺寸（默認使用 min_room_size）"""
    
    bias_ratio: float = 0.8
    """房間大小偏向比例"""
    
    bias_strength: float = 0.3
    """偏向強度"""
    
    # ========== 走廊參數 ==========
    min_bridge_width: int = 2
    """走廊的最小寬度（瓦片數）"""
    
    max_bridge_width: int = 4
    """走廊的最大寬度（瓦片數）"""
    
    extra_bridge_ratio: float = 0.0
    """額外走廊的比例（0.0-1.0，增加連通性）"""
    
    # ========== 房間類型比例 ==========
    monster_room_ratio: float = 0.8
    """怪物房間的比例"""
    
    trap_room_ratio: float = 0.1
    """陷阱房間的比例"""
    
    reward_room_ratio: float = 0.1
    """獎勵房間的比例"""
    
    # ========== 大廳尺寸 ==========
    lobby_width: int = 30
    """大廳的寬度（瓦片數）"""
    
    lobby_height: int = 20
    """大廳的高度（瓦片數）"""
    
    # ========== 整合的瓦片屬性 (強化部分) ==========
    
    pathfinding_costs: Dict[str, float] = field(default_factory=lambda: {
        TILE_OUTSIDE: 1.0,
        TILE_FLOOR: 1.0,      # 房間地板
        TILE_BRIDGE: 1.0,     # 走廊地板
        TILE_DOOR: 1.0,       # 門
        TILE_WALL: 9999.0,    # 牆壁 (高成本，幾乎不可通過)
    })
    """不同瓦片類型的尋路成本"""
    
    passable_tiles_set: Set[str] = field(default_factory=set)
    """所有可通行的瓦片類型集合 (從 src/config.py 導入)"""
    
    def __post_init__(self):
        """初始化後處理"""
        # 如果未指定 min_split_size，使用 min_room_size
        if self.min_split_size is None:
            self.min_split_size = self.min_room_size
        
        # 確保 pathfinding_costs 包含所有通行瓦片，如果沒有指定成本，使用默認 1.0
        # 這是為了確保所有生成步驟都能獲取通行性資訊
        for tile in self.passable_tiles_set:
            if tile not in self.pathfinding_costs:
                 self.pathfinding_costs[tile] = 1.0

    # --- 新增的輔助方法 (強化部分) ---
    
    def get_tile_cost(self, tile_type: str) -> float:
        """獲取指定瓦片類型的尋路成本，未定義則視為牆壁成本。"""
        # 尋路器應該調用此方法
        return self.pathfinding_costs.get(tile_type, self.pathfinding_costs.get(TILE_WALL, 9999.0))
        
    def is_tile_passable(self, tile_type: str) -> bool:
        """檢查指定瓦片類型是否可行走（用於移動系統）。"""
        # 移動系統應該調用此方法
        return tile_type in self.passable_tiles_set

    # --- 類方法 ---
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        驗證配置有效性
        """
        # ... (驗證邏輯保持不變)
        # 檢查網格尺寸
        if self.grid_width <= 0 or self.grid_height <= 0:
            return False, "網格尺寸必須大於 0"
        
        # 檢查房間尺寸
        if self.min_room_size <= 0:
            return False, "最小房間尺寸必須大於 0"
        
        if self.room_width < self.min_room_size or self.room_height < self.min_room_size:
            return False, "房間最大尺寸不能小於最小尺寸"
        
        if self.room_gap < 0:
            return False, "房間間距不能為負數"
        
        # 檢查 BSP 參數
        if self.max_split_depth < 0:
            return False, "BSP 最大深度不能為負數"
        
        if self.min_split_size <= 0:
            return False, "BSP 最小分割尺寸必須大於 0"
        
        # 檢查走廊參數
        if self.min_bridge_width <= 0 or self.max_bridge_width <= 0:
            return False, "走廊寬度必須大於 0"
        
        if self.min_bridge_width > self.max_bridge_width:
            return False, "最小走廊寬度不能大於最大走廊寬度"
        
        if not 0.0 <= self.extra_bridge_ratio <= 1.0:
            return False, "額外走廊比例必須在 0.0 到 1.0 之間"
        
        # 檢查房間類型比例
        # 注意：使用您原始的 MOMSTER_ROOM_RATIO 拼寫
        total_ratio = self.monster_room_ratio + self.trap_room_ratio + self.reward_room_ratio
        if not 0.99 <= total_ratio <= 1.01:  # 允許浮點誤差
            return False, f"房間類型比例總和必須為 1.0(當前為 {total_ratio:.2f})"
        
        if any(ratio < 0.0 or ratio > 1.0 for ratio in [
            self.monster_room_ratio, self.trap_room_ratio, self.reward_room_ratio
        ]):
            return False, "房間類型比例必須在 0.0 到 1.0 之間"
        
        # 檢查大廳尺寸
        if self.lobby_width <= 0 or self.lobby_height <= 0:
            return False, "大廳尺寸必須大於 0"
        
        # 檢查瓦片大小
        if self.tile_size <= 0:
            return False, "瓦片大小必須大於 0"
        
        # 檢查網格是否足夠容納最小房間
        min_grid_size = self.min_room_size + 2 * self.room_gap
        if self.grid_width < min_grid_size or self.grid_height < min_grid_size:
            return False, f"網格尺寸太小，無法容納最小房間（需要至少 {min_grid_size}x{min_grid_size})"
        
        return True, None
    
    @classmethod
    def from_config_file(cls, config_module) -> 'DungeonConfig':
        """
        從配置文件（例如 src.config）創建 DungeonConfig。
        
        Args:
            config_module: 配置模塊（例如：src.config）
        
        Returns:
            DungeonConfig 實例
        """
        # 初始化預設成本 (可根據 config_module.ROOM_FLOOR_COLORS 等進一步強化)
        initial_costs = {
            TILE_OUTSIDE: 1.0,
            TILE_FLOOR: 1.0,
            TILE_BRIDGE: 1.0,
            TILE_DOOR: 1.0,
            TILE_WALL: 9999.0,
        }

        return cls(
            grid_width=getattr(config_module, 'GRID_WIDTH', 120),
            grid_height=getattr(config_module, 'GRID_HEIGHT', 100),
            room_width=getattr(config_module, 'ROOM_WIDTH', 20),
            room_height=getattr(config_module, 'ROOM_HEIGHT', 20),
            min_room_size=getattr(config_module, 'MIN_ROOM_SIZE', 15),
            room_gap=getattr(config_module, 'ROOM_GAP', 2),
            max_split_depth=getattr(config_module, 'MAX_SPLIT_DEPTH', 6),
            min_bridge_width=getattr(config_module, 'MIN_BRIDGE_WIDTH', 2),
            max_bridge_width=getattr(config_module, 'MAX_BRIDGE_WIDTH', 4),
            extra_bridge_ratio=getattr(config_module, 'EXTRA_BRIDGE_RATIO', 0.0),
            # 注意：使用您原始的 MOMSTER_ROOM_RATIO 拼寫
            monster_room_ratio=getattr(config_module, 'MOMSTER_ROOM_RATIO', 0.8), 
            trap_room_ratio=getattr(config_module, 'TRAP_ROOM_RATIO', 0.1),
            reward_room_ratio=getattr(config_module, 'REWARD_ROOM_RATIO', 0.1),
            lobby_width=getattr(config_module, 'LOBBY_WIDTH', 30),
            lobby_height=getattr(config_module, 'LOBBY_HEIGHT', 20),
            bias_ratio=getattr(config_module, 'BIAS_RATIO', 0.8),
            bias_strength=getattr(config_module, 'BIAS_STRENGTH', 0.3),
            tile_size=getattr(config_module, 'TILE_SIZE', 32),
            
            # 從通用配置中提取通行瓦片集合
            passable_tiles_set=set(getattr(config_module, 'PASSABLE_TILES', set())),
            pathfinding_costs=initial_costs
        )
    
    def copy(self, **changes) -> 'DungeonConfig':
        """
        創建配置副本並應用修改
        """
        import copy
        # 使用深拷貝來複製內部的 mutable 結構 (例如 passable_tiles_set, pathfinding_costs)
        new_config = copy.deepcopy(self) 
        for key, value in changes.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
            else:
                raise ValueError(f"未知的配置屬性: {key}")
        # 執行 post_init 邏輯以確保新的副本狀態一致
        new_config.__post_init__() 
        return new_config


# 預定義配置
DEFAULT_CONFIG = DungeonConfig()
"""默認配置"""

SMALL_DUNGEON_CONFIG = DungeonConfig(
    grid_width=60,
    grid_height=50,
    max_split_depth=4,
)
"""小型地牢配置"""

LARGE_DUNGEON_CONFIG = DungeonConfig(
    grid_width=200,
    grid_height=150,
    max_split_depth=8,
)
"""大型地牢配置"""

DENSE_DUNGEON_CONFIG = DungeonConfig(
    extra_bridge_ratio=0.3,
    max_split_depth=7,
)
"""高連通性地牢配置"""