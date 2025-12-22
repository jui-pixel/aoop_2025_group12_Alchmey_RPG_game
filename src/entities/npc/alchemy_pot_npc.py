# src/entities/npc/alchemy_pot_npc.py (修正版本)

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
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
# 假設導入您在上一輪創建的抽象基類
from .base_npc_facade import AbstractNPCFacade 

class AlchemyPotNPC(AbstractNPCFacade): # <--- 繼承抽象基類
    """
    煉金鍋 NPC 門面 (Facade)。
    繼承自 AbstractNPCFacade，僅保留特有的煉金邏輯。
    """
    
    def __init__(self, game, ecs_entity: int):
        super().__init__(game, ecs_entity)
        
        # 確保在初始化時將 Facade 方法指派給 Component 屬性，供 ECS 系統使用。
        interact_comp = self._get_interact_comp()
        interact_comp.tag = "alchemy_pot_npc" 
        interact_comp.start_interaction = self.start_interaction # <--- 關鍵：將 Facade 方法連結到 Component
        # 注意: end_interaction 通常不需要被系統直接調用，但如果需要，也可以在此處設置

    # --- 輔助方法：獲取核心組件 ---
    # 所有通用 getter (如 _get_health_comp, _get_defense_comp) 皆已移除，由 AbstractNPCFacade 提供。

    # --- 核心交互方法 (已修復組件獲取器名稱) ---
        
    # calculate_distance_to 方法已在 AbstractNPCFacade 中實作，故移除此處的冗餘定義。
    
    @property
    def interaction_range(self) -> float:
        """從父類繼承，確保使用正確組件的範圍。"""
        # 由於 AbstractNPCFacade.interaction_range 已經使用 self._get_interact_comp()
        # 且 NPCInteractComponent 包含 interaction_range，此處可直接依賴父類實現。
        return super().interaction_range 

    def start_interaction(self) -> None:
        """Initiate alchemy menu. (實作 AbstractNPCFacade 抽象方法)"""
        # ✨ 修正點: 改用繼承的 self._get_interact_comp()
        comp = self._get_interact_comp()
        comp.is_interacting = True
        if self.game and self.game.menu_manager:
            self.game.menu_manager.open_menu(MenuNavigation.ALCHEMY_MENU, data=self)
        print("Alchemy Pot NPC: Open alchemy synthesis menu.")

    def end_interaction(self) -> None:
        """End interaction. (實作 AbstractNPCFacade 抽象方法)"""
        # ✨ 修正點: 改用繼承的 self._get_interact_comp()
        comp = self._get_interact_comp()
        comp.is_interacting = False
        if self.game and self.game.menu_manager:
            self.game.menu_manager.close_menu(MenuNavigation.ALCHEMY_MENU)

    def synthesize_item(self, ingredients: List[str]) -> Optional[str]:
        """Perform alchemy synthesis based on ingredients. (特有邏輯，保留)"""
        # ✨ 修正點: 改用繼承的 self._get_interact_comp()
        comp = self._get_interact_comp()
        
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
        """NPC takes minimal damage and regenerates. (保留特殊邏輯，使用繼承的組件獲取器)"""
        
        defense_comp = self._get_defense_comp() # 繼承自父類
        if defense_comp.invulnerable:
            return False, 0
            
        # 邏輯保留：特殊的自我修復行為
        damage = base_damage
        if damage > 0:
            health_comp = self._get_health_comp() # 繼承自父類
            health_comp.current_hp = max(health_comp.current_hp - damage, 1)
            health_comp.current_hp = min(health_comp.current_hp + damage, health_comp.max_hp)
        
        return False, damage