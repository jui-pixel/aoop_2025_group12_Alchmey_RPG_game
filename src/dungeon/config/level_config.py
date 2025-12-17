# src/dungeon/config/level_config.py
"""
關卡配置模組
定義關卡配置的資料結構，包括怪物配置和地牢生成參數
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class MonsterType(Enum):
    """怪物類型枚舉"""
    SLIME = "slime"
    GOBLIN = "goblin"
    ORC = "orc"
    SKELETON = "skeleton"
    ZOMBIE = "zombie"
    SPIDER = "spider"
    BAT = "bat"
    WOLF = "wolf"
    DEMON = "demon"
    DRAGON = "dragon"


@dataclass
class MonsterConfig:
    """
    單個怪物類型的配置
    
    定義怪物的生成參數，包括數量範圍、屬性倍率和生成權重
    """
    type: str
    """怪物類型名稱（例如：'slime', 'goblin'）"""
    
    min_count: int = 1
    """每個怪物房間最少生成的怪物數量"""
    
    max_count: int = 3
    """每個怪物房間最多生成的怪物數量"""
    
    health_multiplier: float = 1.0
    """生命值倍率（1.0 = 100%，1.5 = 150%）"""
    
    damage_multiplier: float = 1.0
    """傷害倍率（1.0 = 100%，1.2 = 120%）"""
    
    spawn_weight: float = 1.0
    """生成權重（數值越高，生成機率越大）"""
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        驗證怪物配置的有效性
        
        Returns:
            (is_valid, error_message): 驗證結果和錯誤訊息
        """
        if self.min_count < 0:
            return False, f"怪物 {self.type} 的 min_count 不能為負數"
        
        if self.max_count < self.min_count:
            return False, f"怪物 {self.type} 的 max_count 不能小於 min_count"
        
        if self.health_multiplier <= 0:
            return False, f"怪物 {self.type} 的 health_multiplier 必須大於 0"
        
        if self.damage_multiplier <= 0:
            return False, f"怪物 {self.type} 的 damage_multiplier 必須大於 0"
        
        if self.spawn_weight < 0:
            return False, f"怪物 {self.type} 的 spawn_weight 不能為負數"
        
        return True, None


@dataclass
class MonsterPoolConfig:
    """
    怪物池配置
    
    定義關卡中所有可能生成的怪物及其配置
    """
    monsters: List[MonsterConfig] = field(default_factory=list)
    """怪物配置列表"""
    
    total_monster_multiplier: float = 1.0
    """整體怪物數量倍率（影響所有怪物房間的怪物總數）"""
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        驗證怪物池配置的有效性
        
        Returns:
            (is_valid, error_message): 驗證結果和錯誤訊息
        """
        if not self.monsters:
            return False, "怪物池不能為空，至少需要一種怪物類型"
        
        if self.total_monster_multiplier <= 0:
            return False, "total_monster_multiplier 必須大於 0"
        
        # 驗證每個怪物配置
        for monster in self.monsters:
            is_valid, error = monster.validate()
            if not is_valid:
                return False, error
        
        # 檢查生成權重總和
        total_weight = sum(m.spawn_weight for m in self.monsters)
        if total_weight <= 0:
            return False, "怪物生成權重總和必須大於 0"
        
        return True, None
    
    def get_monster_by_type(self, monster_type: str) -> Optional[MonsterConfig]:
        """
        根據類型獲取怪物配置
        
        Args:
            monster_type: 怪物類型名稱
            
        Returns:
            怪物配置，如果不存在則返回 None
        """
        for monster in self.monsters:
            if monster.type == monster_type:
                return monster
        return None


@dataclass
class LevelConfig:
    """
    關卡配置
    
    包含完整的關卡配置，包括地牢生成參數和怪物配置
    """
    level_id: int
    """關卡 ID"""
    
    level_name: str = ""
    """關卡名稱"""
    
    # 地牢生成參數
    grid_width: int = 120
    """地牢網格寬度（瓦片數）"""
    
    grid_height: int = 100
    """地牢網格高度（瓦片數）"""
    
    max_split_depth: int = 6
    """BSP 分割的最大深度"""
    
    min_room_size: int = 13
    """房間的最小尺寸"""
    
    room_gap: int = 2
    """房間之間的最小間距"""
    
    extra_bridge_ratio: float = 0.1
    """額外走廊的比例（增加連通性）"""
    
    monster_room_ratio: float = 0.7
    """怪物房間的比例"""
    
    trap_room_ratio: float = 0.15
    """陷阱房間的比例"""
    
    reward_room_ratio: float = 0.15
    """獎勵房間的比例"""
    
    min_bridge_width: int = 2
    """走廊的最小寬度"""
    
    max_bridge_width: int = 4
    """走廊的最大寬度"""
    
    bias_ratio: float = 0.8
    """房間大小偏向比例"""
    
    bias_strength: float = 0.3
    """偏向強度"""
    
    # 怪物配置
    monster_pool: MonsterPoolConfig = field(default_factory=MonsterPoolConfig)
    """怪物池配置"""
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        驗證關卡配置的有效性
        
        Returns:
            (is_valid, error_message): 驗證結果和錯誤訊息
        """
        # 檢查關卡 ID
        if self.level_id < 0:
            return False, "關卡 ID 不能為負數"
        
        # 檢查網格尺寸
        if self.grid_width <= 0 or self.grid_height <= 0:
            return False, "網格尺寸必須大於 0"
        
        # 檢查房間尺寸
        if self.min_room_size <= 0:
            return False, "最小房間尺寸必須大於 0"
        
        if self.room_gap < 0:
            return False, "房間間距不能為負數"
        
        # 檢查 BSP 參數
        if self.max_split_depth < 0:
            return False, "BSP 最大深度不能為負數"
        
        # 檢查走廊參數
        if self.min_bridge_width <= 0 or self.max_bridge_width <= 0:
            return False, "走廊寬度必須大於 0"
        
        if self.min_bridge_width > self.max_bridge_width:
            return False, "最小走廊寬度不能大於最大走廊寬度"
        
        if not 0.0 <= self.extra_bridge_ratio <= 1.0:
            return False, "額外走廊比例必須在 0.0 到 1.0 之間"
        
        # 檢查房間類型比例
        total_ratio = self.monster_room_ratio + self.trap_room_ratio + self.reward_room_ratio
        if not 0.99 <= total_ratio <= 1.01:  # 允許浮點誤差
            return False, f"房間類型比例總和必須為 1.0（當前為 {total_ratio:.2f}）"
        
        if any(ratio < 0.0 or ratio > 1.0 for ratio in [
            self.monster_room_ratio, self.trap_room_ratio, self.reward_room_ratio
        ]):
            return False, "房間類型比例必須在 0.0 到 1.0 之間"
        
        # 驗證怪物池配置
        is_valid, error = self.monster_pool.validate()
        if not is_valid:
            return False, f"怪物池配置無效: {error}"
        
        return True, None
    
    def to_dict(self) -> Dict:
        """
        將配置轉換為字典格式（用於保存為 JSON）
        
        Returns:
            配置字典
        """
        return {
            "level_id": self.level_id,
            "level_name": self.level_name,
            "dungeon_config": {
                "grid_width": self.grid_width,
                "grid_height": self.grid_height,
                "max_split_depth": self.max_split_depth,
                "min_room_size": self.min_room_size,
                "room_gap": self.room_gap,
                "extra_bridge_ratio": self.extra_bridge_ratio,
                "monster_room_ratio": self.monster_room_ratio,
                "trap_room_ratio": self.trap_room_ratio,
                "reward_room_ratio": self.reward_room_ratio,
                "min_bridge_width": self.min_bridge_width,
                "max_bridge_width": self.max_bridge_width,
                "bias_ratio": self.bias_ratio,
                "bias_strength": self.bias_strength,
            },
            "monster_config": {
                "monsters": [
                    {
                        "type": m.type,
                        "min_count": m.min_count,
                        "max_count": m.max_count,
                        "health_multiplier": m.health_multiplier,
                        "damage_multiplier": m.damage_multiplier,
                        "spawn_weight": m.spawn_weight,
                    }
                    for m in self.monster_pool.monsters
                ],
                "total_monster_multiplier": self.monster_pool.total_monster_multiplier,
            }
        }
