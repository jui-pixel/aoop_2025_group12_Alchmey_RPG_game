import esper
import pygame
from src.ecs.components import (
    Position, Renderable, Health, Defense, Buffs, Tag, Collider,
    NPCInteractComponent, DungeonPortalComponent
)

def create_dungeon_portal_npc(
    world: esper.World,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    available_dungeons: Optional[List[Dict]] = None
) -> int:
    """創建一個 ECS 地牢傳送門 NPC 實體。"""
    
    npc_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag="dungeon_portal_npc"))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    world.add_component(npc_entity, Renderable(
        image=None,
        shape="rect",
        w=w,
        h=h,
        color=(128, 0, 128), # 紫色
        layer=0 
    ))

    # 3. 碰撞器
    world.add_component(npc_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="portal"
    ))

    # 4. 健康與防禦 (高防禦且無敵)
    world.add_component(npc_entity, Health(max_hp=999999, current_hp=999999))
    world.add_component(npc_entity, Defense(
        defense=100,
        element="untyped",
        invulnerable=True
    ))

    # 5. 增益效果
    world.add_component(npc_entity, Buffs())

    # 6. NPC 交互狀態 (interaction_range=80.0)
    world.add_component(npc_entity, NPCInteractComponent(interaction_range=80.0))
    
    # 7. 傳送門專屬狀態
    world.add_component(npc_entity, DungeonPortalComponent(
        available_dungeons=available_dungeons or [{'name': 'Test Dungeon', 'level': 1, 'dungeon_id': 1}]
    ))

    return npc_entity

# src/entities/npc/dungeon_portal_npc.py (重構後)

from typing import Optional, List, Dict, Tuple
import pygame
import math
import esper
# 假設所有 ECS Component 都可導入
from src.ecs.components import DungeonPortalComponent, NPCInteractComponent, Defense, Position 
from src.config import *
# 移除 BasicEntity, HealthEntity, BuffableEntity 的舊式導入

class DungeonPortalNPC:
    """
    地牢傳送門 NPC 門面 (Facade)。
    它提供一個接口來啟動傳送門交互，並使用 ECS Component 存儲狀態。
    """
    def __init__(self, game, ecs_entity: int):
        self.game = game
        self.ecs_entity = ecs_entity
        self.world = game.world 

    # --- 輔助方法：獲取核心組件 ---

    def _get_portal_comp(self) -> 'DungeonPortalComponent':
        return self.world.component_for_entity(self.ecs_entity, DungeonPortalComponent)
    
    def _get_interact_comp(self) -> 'NPCInteractComponent':
        return self.world.component_for_entity(self.ecs_entity, NPCInteractComponent)
        
    def _get_defense_comp(self) -> 'Defense':
        return self.world.component_for_entity(self.ecs_entity, Defense)
        
    def _get_position_comp(self) -> 'Position':
        return self.world.component_for_entity(self.ecs_entity, Position)

    # --- 交互邏輯 (操作 Component) ---

    @property
    def available_dungeons(self) -> List[Dict]:
        return self._get_portal_comp().available_dungeons

    @property
    def portal_effect_active(self) -> bool:
        return self._get_portal_comp().portal_effect_active

    # 移除 update 和 draw 方法 (已移至 InteractionSystem 和 RenderSystem)

    def start_interaction(self) -> None:
        """Show dungeon selection menu via MenuManager."""
        interact_comp = self._get_interact_comp()
        interact_comp.is_interacting = True
        
        if self.game:
            dungeons = self._get_portal_comp().available_dungeons
            self.game.show_menu('dungeon_menu', dungeons)
        print(f"DungeonPortalNPC: Opening dungeon menu with {len(dungeons)} dungeons")

    def end_interaction(self) -> None:
        """Close menu."""
        interact_comp = self._get_interact_comp()
        interact_comp.is_interacting = False
        if self.game:
            self.game.hide_menu('dungeon_menu')
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
                    self.game.dungeon_manager.dungeon.initialize_dungeon() 
                    
                    # 假設 Player Facade 具有 displacement 屬性
                    player_facade = self.game.entity_manager.player 
                    if hasattr(player_facade, 'displacement'):
                        player_facade.displacement = (0, 0)
                        
                    self.game.entity_manager.initialize_dungeon_entities()
                    self.game.event_manager.state = "playing"
                    self.game.hide_menu('dungeon_menu')
                    self.game.menu_manager.set_menu(None)
                    
                    # 更新 ECS Component 狀態
                    portal_comp.portal_effect_active = True
                    print(f"DungeonPortalNPC: Entered {dungeon_name}, menu closed")
                    return True
        print(f"DungeonPortalNPC: Failed to enter {dungeon_name}")
        return False

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                     max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                     lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """NPC takes damage, checks invulnerability from Defense Component."""
        if self._get_defense_comp().invulnerable:
            return False, 0
            
        # 由於 HealthSystem 會在 ECS 中處理傷害，這裡僅是接口兼容，並假定它不會被殺死
        return False, 0
    
    def calculate_distance_to(self, other_entity) -> float:
        """Calculate the Euclidean distance to another entity."""
        self_pos = self._get_position_comp()
        # 假設 other_entity (Player Facade) 具有 x, y 屬性
        dx = self_pos.x - other_entity.x
        dy = self_pos.y - other_entity.y
        return math.sqrt(dx**2 + dy**2)