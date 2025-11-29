# 假設此函數位於 src/entities/ecs_factory.py
import esper
import pygame
from src.config import TILE_SIZE 
from src.ecs.components import (
    Position, Renderable, Health, Defense, Collider, Buffs, Tag, 
    NPCInteractComponent 
)
from typing import Optional, Dict, List, Tuple
import math
from src.buffs.element_buff import ELEMENTAL_BUFFS
from src.config import *



class AlchemyPotNPC:
    """
    煉金鍋 NPC 門面 (Facade)。
    它不包含狀態，而是透過 ecs_entity ID 來執行交互操作。
    """
    def __init__(self, game, ecs_entity: int):
        self.game = game
        self.ecs_entity = ecs_entity
        self.world = game.world # 假設 game 實例持有 esper.World

        # 移除所有父類構造函式調用 (BasicEntity, HealthEntity, BuffableEntity)
        # 狀態由 ECS Factory 負責初始化。

    # --- 輔助方法：獲取核心組件 ---

    def _get_NPCinteract_comp(self) -> 'NPCInteractComponent':
        return self.world.component_for_entity(self.ecs_entity, NPCInteractComponent)
    
    def _get_health_comp(self) -> 'Health':
        return self.world.component_for_entity(self.ecs_entity, Health)

    def _get_defense_comp(self) -> 'Defense':
        return self.world.component_for_entity(self.ecs_entity, Defense)
        
    def _get_position_comp(self) -> 'Position':
        return self.world.component_for_entity(self.ecs_entity, Position)

    # --- 核心交互方法 (邏輯保持不變，但操作 Component) ---
    
    @property
    def interaction_range(self) -> float:
        return self._get_pot_comp().interaction_range
        
    def calculate_distance_to(self, other_entity: 'Player') -> float:
        """計算到另一個實體（例如玩家）的距離。"""
        # 從 ECS 獲取自己的位置
        self_pos = self._get_position_comp()
        # 假設 Player Facade 提供 x, y 屬性 (已在上一輪重構中實現)
        dx = self_pos.x - other_entity.x
        dy = self_pos.y - other_entity.y
        return math.sqrt(dx**2 + dy**2)
    
    # update 和 draw 方法被移除，功能將移至 System

    def start_interaction(self) -> None:
        """Initiate alchemy menu."""
        comp = self._get_pot_comp()
        comp.is_interacting = True
        if self.game:
            # 假設 alchemy_options 已載入到 Component 中
            self.game.show_menu('alchemy_menu', comp.alchemy_options)
        print("Alchemy Pot NPC: Open alchemy synthesis menu.")

    def end_interaction(self) -> None:
        """End interaction."""
        comp = self._get_pot_comp()
        comp.is_interacting = False
        if self.game:
            self.game.hide_menu('alchemy_menu')

    def synthesize_item(self, ingredients: List[str]) -> Optional[str]:
        """Perform alchemy synthesis based on ingredients."""
        comp = self._get_pot_comp()
        for option in comp.alchemy_options:
            if sorted(option['ingredients']) == sorted(ingredients):
                result = option['result']
                if self.game and self.game.entity_manager.player:
                    buff = ELEMENTAL_BUFFS.get(result)
                    if buff:
                        # 假設 player 實體有 buff_synthesizer 邏輯
                        self.game.entity_manager.player.buff_synthesizer.synthesize_buffs([buff], self.game.entity_manager.player)
                        print(f"Alchemy Pot NPC: Synthesized {result}")
                        return result
        print("Alchemy Pot NPC: Invalid ingredient combination")
        return None

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                     max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                     lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """NPC takes minimal damage and regenerates. 由 ECS CombatSystem 處理，但為了兼容舊接口仍保留。"""
        
        defense_comp = self._get_defense_comp()
        if defense_comp.invulnerable:
            return False, 0
            
        # ⚠️ 注意：在 ECS 中，此邏輯應該在 CombatSystem/HealthSystem 內運行。
        # 這裡的實現只是為了兼容舊的 `take_damage` 接口，並模擬其行為：
        # 它調用父類 (這裡應該是 System 函數)，然後自我治療。
        
        # 由於無法直接調用 HealthSystem 的傷害邏輯，這裡直接返回舊邏輯
        # 簡化為：若非無敵，假裝受到傷害但立即治癒。
        damage = base_damage # 簡易模擬
        if damage > 0:
            health_comp = self._get_health_comp()
            health_comp.current_hp = max(health_comp.current_hp - damage, 1) # 至少保留 1 HP
            health_comp.current_hp = min(health_comp.current_hp + damage, health_comp.max_hp) # 立即自我治療
        
        return False, damage