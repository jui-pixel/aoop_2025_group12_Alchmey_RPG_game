import esper
import pygame
from src.ecs.components import (
    Position, Renderable, Health, Defense, Collider, Buffs, Tag, 
    NPCInteractComponent # 使用通用交互組件
)

def create_magic_crystal_npc(
    world: esper.World,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    tag: str = "magic_crystal_npc",
    base_max_hp: int = 999999, 
    element: str = "light", 
    defense: int = 100,
    invulnerable: bool = True
) -> int:
    """創建一個 ECS 魔法水晶 NPC 實體。"""
    
    npc_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag=tag))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    world.add_component(npc_entity, Renderable(
        image=None, # 讓 RenderSystem 處理載入白色水晶圖像
        shape="rect",
        w=w,
        h=h,
        color=(255, 255, 255), # 白色
        layer=0 
    ))

    # 3. 碰撞器
    world.add_component(npc_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="npc"
    ))

    # 4. 健康與防禦
    world.add_component(npc_entity, Health(
        max_hp=base_max_hp,
        current_hp=base_max_hp
    ))
    world.add_component(npc_entity, Defense(
        defense=defense,
        element=element,
        invulnerable=invulnerable
    ))

    # 5. 增益效果 (Buffs)
    world.add_component(npc_entity, Buffs())

    # 6. NPC 交互狀態 (interaction_range=80.0, is_interacting=False)
    world.add_component(npc_entity, NPCInteractComponent(interaction_range=80.0)) 

    return npc_entity

# src/entities/npc/dungeon_portal_npc.py (重構後)
from typing import Optional, Dict, Tuple, List
import pygame
import math
import esper # 引入 ECS 庫
# 假設所有 ECS Component 都可導入
from src.ecs.components import NPCInteractComponent, Health, Defense, Position 
from src.config import *
# 移除 BasicEntity, HealthEntity, BuffableEntity 的舊式導入

class MagicCrystalNPC:
    """
    魔法水晶 NPC 門面 (Facade)。
    它不包含狀態，而是透過 ecs_entity ID 來執行交互操作。
    """
    def __init__(self, game, ecs_entity: int):
        self.game = game
        self.ecs_entity = ecs_entity
        self.world = game.world # 假設 game 實例持有 esper.World

        # 移除所有父類構造函式調用

    # --- 輔助方法：獲取核心組件 ---

    def _get_crystal_comp(self) -> 'NPCInteractComponent':
        return self.world.component_for_entity(self.ecs_entity, NPCInteractComponent)
    
    def _get_health_comp(self) -> 'Health':
        return self.world.component_for_entity(self.ecs_entity, Health)

    def _get_defense_comp(self) -> 'Defense':
        return self.world.component_for_entity(self.ecs_entity, Defense)
        
    def _get_position_comp(self) -> 'Position':
        return self.world.component_for_entity(self.ecs_entity, Position)

    # --- 移除持續性更新與繪圖 ---
    
    # 移除 update 方法 (距離檢查移至 InteractionSystem)
    # 移除 draw 方法 (繪圖移至 RenderSystem)

    # --- 交互邏輯 (操作 Component) ---

    def start_interaction(self) -> None:
        """Open crystal shop/menu via MenuManager."""
        comp = self._get_crystal_comp()
        comp.is_interacting = True
        if self.game:
            self.game.show_menu('crystal_menu')
        print("Magic Crystal NPC: Browse elemental crystals and buffs.")

    def end_interaction(self) -> None:
        """Close shop."""
        comp = self._get_crystal_comp()
        comp.is_interacting = False
        if self.game:
            self.game.hide_menu('crystal_menu')

    # --- 距離計算 (使用 Component 數據) ---

    @property
    def interaction_range(self) -> float:
        return self._get_crystal_comp().interaction_range

    def calculate_distance_to(self, other_entity) -> float:
        """Calculate the Euclidean distance to another entity."""
        self_pos = self._get_position_comp()
        # 假設 other_entity (Player Facade) 具有 x, y 屬性 (已在上一輪重構中實現)
        dx = self_pos.x - other_entity.x
        dy = self_pos.y - other_entity.y
        return math.sqrt(dx**2 + dy**2)
    
    # --- 傷害處理 (由 ECS System 負責，Facade 僅保留兼容接口) ---

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                     max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                     lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """
        模擬 NPC 受到傷害邏輯，但由於 invulnerable=True，它不會實際受損。
        在 ECS 中，此邏輯應由 CombatSystem 處理，但保留此方法用於兼容舊代碼。
        """
        if self._get_defense_comp().invulnerable:
            return False, 0
            
        # 為了兼容舊的 return 格式，返回 (未被殺死, 0 傷害)
        return False, 0