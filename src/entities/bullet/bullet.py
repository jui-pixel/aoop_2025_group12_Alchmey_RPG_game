# 假設此函數位於 src/entities/factories.py 或一個專門的 ECS 創建模組中
import esper
import pygame
from typing import Tuple, Dict, List, Any
from dataclasses import dataclass
from src.ecs.components import Position, Velocity, Combat, Renderable, Collider, ProjectileState, Tag

def create_standard_bullet_entity(
    world: esper,
    start_pos: Tuple[float, float],
    w: int,
    h: int,
    tag: str,
    direction: Tuple[float, float],
    # ProjectileState & Movement
    max_speed: float,
    lifetime: float, # 假設預設壽命
    # Combat
    damage: int,
    atk_element: str,
    damage_to_element: Dict[str, float],
    max_penetration_count: int,
    collision_cooldown: float,
    buffs: List[Any],
    explosion_range: float,
    explosion_damage: int,
    explosion_element: str,
    explosion_buffs: List[Any],
    # Percentage Damage (簡化為一個 dict)
    percentage_damage: Dict[str, int], 
    # Collider
    pass_wall: bool,
    # 其他
    cause_death: bool = True
) -> int:
    """創建一個標準 ECS 子彈實體，取代 Bullet 類別的初始化。"""
    
    bullet_entity = world.create_entity()
    
    # 1. Position & Movement
    world.add_component(bullet_entity, Position(x=start_pos[0], y=start_pos[1]))
    
    vel_x = direction[0] * max_speed
    vel_y = direction[1] * max_speed
    world.add_component(bullet_entity, Velocity(x=vel_x, y=vel_y, speed=max_speed))
    
    # 2. Renderable (使用 rect shape)
    world.add_component(bullet_entity, Renderable(
        image=None, # 讓 RenderSystem 處理默認繪製或加載圖像
        shape="rect",
        w=w,
        h=h,
        color=(255, 255, 0), # 默認黃色
        layer=1 
    ))

    # 3. Collider
    world.add_component(bullet_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=pass_wall,
        collision_group="projectile" 
    ))

    # 4. Combat & Attack
    world.add_component(bullet_entity, Combat(
        damage=damage,
        can_attack=True,
        atk_element=atk_element,
        damage_to_element=damage_to_element,
        max_penetration_count=max_penetration_count,
        collision_cooldown=collision_cooldown,
        explosion_range=explosion_range,
        explosion_damage=explosion_damage,
        explosion_element=explosion_element,
        explosion_buffs=explosion_buffs,
        buffs=buffs,
        # 將百分比傷害展開
        max_hp_percentage_damage=percentage_damage['max_hp'],
        current_hp_percentage_damage=percentage_damage['current_hp'],
        lose_hp_percentage_damage=percentage_damage['lose_hp'],
        cause_death=cause_death
    ))

    # 5. Projectile State & Tag
    world.add_component(bullet_entity, ProjectileState(
        direction=direction,
        max_speed=max_speed,
        max_lifetime=lifetime, 
        can_move=True,
        explode_on_collision=(max_penetration_count <= 0) # 假設無穿透時碰撞即爆炸
    ))
    
    world.add_component(bullet_entity, Tag(tag=tag))
    
    return bullet_entity