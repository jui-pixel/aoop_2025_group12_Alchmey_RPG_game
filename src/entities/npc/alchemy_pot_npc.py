# 假設此函數位於 src/entities/ecs_factory.py
import esper
import pygame
from src.config import TILE_SIZE 
from src.ecs.components import (
    Position, Renderable, Health, Defense, Collider, Buffs, Tag, 
    NPCInteractComponent 
)

def create_alchemy_pot_npc(
    world: esper.World,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    tag: str = "alchemy_pot_npc",
    base_max_hp: int = 999999, 
    element: str = "earth", 
    defense: int = 100,
    invulnerable: bool = True
) -> int:
    """創建一個 ECS 煉金鍋 NPC 實體。"""
    
    npc_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag=tag))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    # 注意：這裡應該載入圖片，但為了簡化，我們只設定屬性
    world.add_component(npc_entity, Renderable(
        image=None, 
        shape="rect",
        w=w,
        h=h,
        color=(139, 69, 19), # 棕色
        layer=0 
    ))

    # 3. 碰撞器 (用於交互距離檢查)
    world.add_component(npc_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="npc"
    ))

    # 4. 健康與防禦
    world.add_component(npc_entity, Health(
        max_hp=base_max_hp,
        current_hp=base_max_hp,
        max_shield=0,
        current_shield=0
    ))
    world.add_component(npc_entity, Defense(
        defense=defense,
        dodge_rate=0.0,
        element=element,
        resistances=None,
        invulnerable=invulnerable
    ))

    # 5. 增益效果 (Buffs)
    world.add_component(npc_entity, Buffs())

    # 6. 煉金鍋專屬狀態
    world.add_component(npc_entity, NPCInteractComponent()) 

    return npc_entity