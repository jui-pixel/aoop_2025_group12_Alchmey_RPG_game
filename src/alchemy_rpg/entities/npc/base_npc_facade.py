# src/entities/npc/base_npc_facade.py

from abc import ABC, abstractmethod
from typing import Tuple, TYPE_CHECKING
import math
import esper

# 假設這些核心組件存在於您的專案結構中
# 您需要根據實際路徑調整此處的導入
try:
    from src.ecs.components import Position, Health, Defense, NPCInteractComponent 
except ImportError:
    # 僅為演示，如果您的環境中沒有這些組件，請在實際專案中確保它們可導入
    print("Warning: ECS Components not found. Please ensure src.ecs.components is correct.")
    # 實際專案中應避免這種錯誤處理
    
# 為了避免循環導入和提高性能，可以使用 TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.game import Game # 假設您的主遊戲類為 Game

# 抽象 NPC 門面類 (Abstract NPC Facade)
class AbstractNPCFacade(ABC):
    """
    所有 ECS 架構 NPC 實體的抽象門面基類 (Base Facade)。
    它提供了一個統一的接口來與 NPC 交互，但不持有狀態。
    狀態皆存於 ECS 組件中，通過 ecs_entity ID 訪問。
    """
    
    def __init__(self, game: 'Game', ecs_entity: int):
        """
        初始化 NPC Facade。
        :param game: 遊戲主實例 (通常持有世界/管理器)。
        :param ecs_entity: 該 NPC 在 esper.World 中的實體 ID。
        """
        self.game = game
        self.ecs_entity = ecs_entity
        # 假設 game 實例持有 esper.World
        self.world: esper.World = getattr(game, 'world', None) 
        
        if self.world is None:
            # 這是必要的 ECS 引用
            raise AttributeError("Game instance must have an 'world' (esper.World) attribute.")

    # --- 輔助方法：獲取核心組件 (Component Getters) ---
    # 所有子類都可以使用這些方法來存取組件數據

    def _get_position_comp(self) -> Position:
        """獲取該實體的位置組件 (Position Component)。"""
        return self.world.component_for_entity(self.ecs_entity, Position)
    
    def _get_health_comp(self) -> Health:
        """獲取該實體的生命值組件 (Health Component)。"""
        return self.world.component_for_entity(self.ecs_entity, Health)

    def _get_defense_comp(self) -> Defense:
        """獲取該實體的防禦組件 (Defense Component)。"""
        return self.world.component_for_entity(self.ecs_entity, Defense)
    
    def _get_interact_comp(self) -> NPCInteractComponent:
        """獲取該實體的 NPC 交互組件 (NPCInteractComponent)。"""
        return self.world.component_for_entity(self.ecs_entity, NPCInteractComponent)


    # --- 抽象交互接口 (Abstract Interaction Interface) ---
    # 所有子類必須實作這兩個方法，以定義其交互行為

    @abstractmethod
    def start_interaction(self) -> None:
        """
        當玩家與 NPC 開始交互時調用（例如：打開商店菜單、觸發對話）。
        子類必須實作此方法。
        """
        pass

    @abstractmethod
    def end_interaction(self) -> None:
        """
        當玩家與 NPC 結束交互時調用（例如：關閉菜單、清除交互標誌）。
        子類必須實作此方法。
        """
        pass
        
    # --- 共通屬性與方法 (Common Properties and Methods) ---
    
    @property
    def interaction_range(self) -> float:
        """獲取 NPC 的交互範圍 (從 NPCInteractComponent)。"""
        return self._get_interact_comp().interaction_range

    def calculate_distance_to(self, other_entity) -> float:
        """
        計算該 NPC 實體與另一個實體之間的歐幾里得距離。
        假設 other_entity (例如 Player Facade) 具有 x, y 屬性。
        """
        self_pos = self._get_position_comp()
        # 假設 other_entity (Player Facade) 具有 x, y 屬性
        dx = self_pos.x - other_entity.x
        dy = self_pos.y - other_entity.y
        return math.sqrt(dx**2 + dy**2)
    
    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                     max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                     lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """
        NPC 接受傷害的接口。
        
        ⚠️ 注意：在 ECS 架構中，傷害計算主要由 CombatSystem/HealthSystem 處理。
        這個方法作為一個兼容接口，只需進行基本的檢查 (如無敵狀態) 並委派給 ECS 系統。
        
        :return: (是否受到傷害, 實際減少的 HP)
        """
        defense_comp = self._get_defense_comp()
        if defense_comp.invulnerable:
            return False, 0
            
        # 實際傷害計算和 Health Component 的更新應該在 HealthSystem/CombatSystem 中完成。
        # 這裡僅是接口保留，返回 False 和 0 (表示 Facade 不負責實際扣血)
        return False, 0