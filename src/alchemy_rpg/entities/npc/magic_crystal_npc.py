# src/entities/npc/magic_crystal_npc.py (修正後)

import esper
import pygame
import math
from typing import Optional, Dict, Tuple, List
# 假設導入 AbstractNPCFacade
from .base_npc_facade import AbstractNPCFacade
from src.ecs.components import NPCInteractComponent, Health, Defense, Position 
from src.core.config import *
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

class MagicCrystalNPC(AbstractNPCFacade): # <--- 繼承抽象基類
    """
    魔法水晶 NPC 門面 (Facade)。
    繼承自 AbstractNPCFacade，僅保留特有的交互邏輯。
    """
    def __init__(self, game, ecs_entity: int):
        super().__init__(game, ecs_entity)
        
        # 確保在初始化時將 Facade 方法指派給 Component 屬性，供 ECS 系統使用。
        interact_comp = self._get_interact_comp() # 繼承自父類
        interact_comp.tag = "magic_crystal_npc"
        interact_comp.start_interaction = self.start_interaction

    # --- 輔助方法：特有組件獲取 (這裡只需要通用的 _get_interact_comp，因此不需要額外定義) ---
    # 原本的 _get_crystal_comp 實質上就是 _get_interact_comp，故可移除。

    # --- 交互邏輯 (操作 Component) ---

    # interaction_range 屬性已移除，由 AbstractNPCFacade 提供。
    
    def start_interaction(self) -> None:
        """Open crystal shop/menu via MenuManager. (實作 AbstractNPCFacade 抽象方法)"""
        comp = self._get_interact_comp() # 繼承自父類
        comp.is_interacting = True
        if self.game and self.game.menu_manager:
            self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU, data=self)
        print("Magic Crystal NPC: Browse elemental crystals and buffs.")

    def end_interaction(self) -> None:
        """Close shop. (實作 AbstractNPCFacade 抽象方法)"""
        comp = self._get_interact_comp() # 繼承自父類
        comp.is_interacting = False
        if self.game and self.game.menu_manager:
            self.game.menu_manager.set_menu(None)
    
    # calculate_distance_to 和 take_damage 方法已移除，由 AbstractNPCFacade 提供。