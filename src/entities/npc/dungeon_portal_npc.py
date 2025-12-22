# src/entities/npc/dungeon_portal_npc.py (修正後)

import esper
import pygame
import math
from typing import Optional, List, Dict, Tuple
# 假設導入 AbstractNPCFacade
from .base_npc_facade import AbstractNPCFacade 
from src.ecs.components import DungeonPortalComponent, NPCInteractComponent, Defense, Position 
from src.config import *
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
class DungeonPortalNPC(AbstractNPCFacade): # <--- 繼承抽象基類
    """
    地牢傳送門 NPC 門面 (Facade)。
    它提供一個接口來啟動傳送門交互，並使用 ECS Component 存儲狀態。
    """
    def __init__(self, game, ecs_entity: int):
        super().__init__(game, ecs_entity)
        
        # 確保在初始化時將 Facade 方法指派給 Component 屬性，供 ECS 系統使用。
        interact_comp = self._get_interact_comp() # 繼承自父類
        interact_comp.tag = "dungeon_portal_npc"
        interact_comp.start_interaction = self.start_interaction
        
        dungeon_comp = self._get_portal_comp()
        dungeon_comp.available_dungeons = [{'name': 'Test Dungeon', 'level': 1, 'dungeon_id': 1}]

    # --- 輔助方法：特有組件獲取 ---

    def _get_portal_comp(self) -> 'DungeonPortalComponent':
        """獲取 DungeonPortalComponent。"""
        return self.world.component_for_entity(self.ecs_entity, DungeonPortalComponent)
    
    # 通用 getter (_get_interact_comp, _get_defense_comp, _get_position_comp) 
    # 已移除，由 AbstractNPCFacade 提供。

    # --- 交互邏輯 (操作 Component) ---

    @property
    def available_dungeons(self) -> List[Dict]:
        return self._get_portal_comp().available_dungeons

    @property
    def portal_effect_active(self) -> bool:
        return self._get_portal_comp().portal_effect_active

    def start_interaction(self) -> None:
        """Show dungeon selection menu via MenuManager."""
        interact_comp = self._get_interact_comp()
        interact_comp.is_interacting = True
        
        if self.game:
            dungeons = self._get_portal_comp().available_dungeons
            # 【修正點】將數據打包成字典，包含 dungeons 列表和 npc_facade 實例
            menu_data = {'dungeons': dungeons, 'npc_facade': self}
            self.game.menu_manager.open_menu(MenuNavigation.DUNGEON_MENU, data=menu_data)
        print(f"DungeonPortalNPC: Opening dungeon menu with {len(dungeons)} dungeons")

    def end_interaction(self) -> None:
        """Close menu. (實作 AbstractNPCFacade 抽象方法)"""
        interact_comp = self._get_interact_comp() # 繼承自父類
        interact_comp.is_interacting = False
        if self.game and self.game.menu_manager:
            # 這裡應該使用 game.hide_menu() 或 game.menu_manager.set_menu(None)
            # 根據您的 Game 類設計，我們假設 hide_menu 或 set_menu(None) 可用
            # 由於 Game.show_menu 有 stack 邏輯，這裡使用 set_menu(None) 保持一致
            self.game.menu_manager.close_menu(MenuNavigation.DUNGEON_MENU)
        print("DungeonPortalNPC: Closed dungeon menu")

    def enter_dungeon(self, dungeon_name: str) -> bool:
        """Switch to the selected dungeon room, initialize dungeon, and place entities."""
        portal_comp = self._get_portal_comp()
        
        for dungeon in portal_comp.available_dungeons:
            if dungeon['name'] == dungeon_name:
                if 'dungeon_id' not in dungeon:
                    print(f"DungeonPortalNPC: Error - No dungeon_id for {dungeon_name}")
                    return False
                
                if self.game and self.game.entity_manager.player:
                    # 核心遊戲狀態切換邏輯 (保留在 Facade 中)
                    print("DungeonPortalNPC: Initializing full dungeon")
                    # 修正: 呼叫 DungeonManager 而非直接呼叫其屬性
                    self.game.dungeon_manager.initialize_dungeon(dungeon['dungeon_id']) 
                    
                    player_facade = self.game.entity_manager.player 
                    if hasattr(player_facade, 'displacement'):
                        player_facade.displacement = (0, 0)
                        
                    self.game.entity_manager.initialize_dungeon_entities()
                    self.game.event_manager.state = "playing"
                    
                    # 關閉菜單
                    self.game.menu_manager.close_all_menus()
                    
                    # 更新 ECS Component 狀態
                    portal_comp.portal_effect_active = True
                    print(f"DungeonPortalNPC: Entered {dungeon_name}, menu closed")
                    return True
        print(f"DungeonPortalNPC: Failed to enter {dungeon_name}")
        return False

    # take_damage 和 calculate_distance_to 方法已移除，由 AbstractNPCFacade 提供。
    # 如果 DungeonPortalNPC 需要特殊傷害邏輯，則在子類中覆寫 take_damage 即可。
    # 這裡我們依賴父類提供的通用（無敵）邏輯。