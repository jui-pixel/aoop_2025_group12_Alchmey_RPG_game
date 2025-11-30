# src/entities/npc/alchemy_pot_npc.py (重構後)

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

# 假設導入您在上一輪創建的抽象基類
from .base_npc_facade import AbstractNPCFacade 
# 假設導入煉金鍋專屬組件
# from src.ecs.components import AlchemyPotComponent # 實際專案中請確保導入路徑正確

class AlchemyPotNPC(AbstractNPCFacade): # <--- 繼承抽象基類
    """
    煉金鍋 NPC 門面 (Facade)。
    繼承自 AbstractNPCFacade，僅保留特有的煉金邏輯。
    """
    
    # 構造函數 __init__ 已被 AbstractNPCFacade 繼承，無需重複定義。

    # --- 輔助方法：獲取核心組件 ---
    
    # 以下通用組件獲取方法已移除，因為它們在 AbstractNPCFacade 中：
    # _get_NPCinteract_comp
    # _get_health_comp
    # _get_defense_comp
    # _get_position_comp

    # --- 核心交互方法 (邏輯保持不變，但操作 Component) ---
        
    def calculate_distance_to(self, other_entity: 'Player') -> float:
        """計算到另一個實體（例如玩家）的距離。
        *** (此方法已在 AbstractNPCFacade 中實作，但因您要求 "僅去除重複的參數" 
        並未修改邏輯，此處已將其移除，改為繼承父類。) ***
        """
        return super().calculate_distance_to(other_entity) # 實際程式碼中不需要這行，只需刪除原始方法即可自動繼承
    
    def start_interaction(self) -> None:
        """Initiate alchemy menu. (實作 AbstractNPCFacade 抽象方法)"""
        comp = self._get_NPCinteract_comp()
        comp.is_interacting = True
        if self.game and self.game.menu_manager:
            # 假設 menu_manager 存在，且已載入 alchemy_options 到 Component 中
            self.game.menu_manager.show_menu('alchemy_menu', comp.alchemy_options)
        print("Alchemy Pot NPC: Open alchemy synthesis menu.")

    def end_interaction(self) -> None:
        """End interaction. (實作 AbstractNPCFacade 抽象方法)"""
        comp = self._get_NPCinteract_comp()
        comp.is_interacting = False
        if self.game and self.game.menu_manager:
            self.game.menu_manager.hide_menu('alchemy_menu')

    def synthesize_item(self, ingredients: List[str]) -> Optional[str]:
        """Perform alchemy synthesis based on ingredients. (特有邏輯，保留)"""
        comp = self._get_NPCinteract_comp()
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
        """NPC takes minimal damage and regenerates. (保留特殊邏輯，僅使用繼承的組件獲取器)"""
        
        defense_comp = self._get_defense_comp() # 繼承自父類
        if defense_comp.invulnerable:
            return False, 0
            
        # ⚠️ 注意：這段邏輯是特殊的自我修復，故保留。
        damage = base_damage # 簡易模擬
        if damage > 0:
            health_comp = self._get_health_comp() # 繼承自父類
            health_comp.current_hp = max(health_comp.current_hp - damage, 1) # 至少保留 1 HP
            health_comp.current_hp = min(health_comp.current_hp + damage, health_comp.max_hp) # 立即自我治療
        
        return False, damage