# src/entities/ecs_factory.py

import esper
import pygame
# 假設已導入 Position, Renderable, Health, Defense, Tag, Collider, RegenComponent
from src.ecs.components import (
    Position, Renderable, Health, Defense, Tag, Collider
)

def create_dummy_entity(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 32, 
    h: int = 32,
    base_max_hp: int = 999999999 # 模擬無限生命
) -> int:
    """創建一個 ECS 訓練假人實體。"""
    
    dummy_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(dummy_entity, Tag(tag="dummy"))
    world.add_component(dummy_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    # (註：這裡應處理圖片載入，但在 ECS 中我們只設定屬性)
    world.add_component(dummy_entity, Renderable(
        image=None,
        shape="rect",
        w=w,
        h=h,
        color=(255, 0, 0), # 紅色
        layer=1 # 可能比地圖高
    ))

    # 3. 碰撞器 (假人是靜止的)
    world.add_component(dummy_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="enemy_dummy" # 假設有一個專門的碰撞組
    ))

    # 4. 健康與防禦
    world.add_component(dummy_entity, Health(
        max_hp=base_max_hp,
        current_hp=base_max_hp,
        regen_rate=base_max_hp
    ))
    world.add_component(dummy_entity, Defense(
        defense=0,
        element="untyped",
        invulnerable=False # 允許受到傷害
    ))


    return dummy_entity

# src/ecs/systems/regeneration_system.py (新增)

import esper
from ...ecs.components import Health, Defense # 假設 Defense 組件用於檢查 invulnerable

class RegenerationSystem(esper.Processor):
    """
    處理所有具有 RegenComponent 實體的生命值再生。
    這取代了 Dummy 類別中的 update() 和 take_damage() 內部的自我治療邏輯。
    """
    def process(self, dt: float, *args, **kwargs) -> None:
        
        # 迭代所有有再生、生命和防禦組件的實體
        for ent, (health, defense) in self.world.get_components(Health, Defense):
            
            if defense.invulnerable:
                continue # 如果是無敵狀態，則不需要再生
                
            # 假人的核心邏輯：持續恢復生命
            if health.current_hp < health.max_hp:
                # 計算再生量
                heal_amount = int(health.regen_rate * dt)
                
                # 應用再生：確保不超過最大生命值
                health.current_hp = min(health.current_hp + heal_amount, health.max_hp)