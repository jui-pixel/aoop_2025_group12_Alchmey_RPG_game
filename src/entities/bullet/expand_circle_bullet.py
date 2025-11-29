import esper
import pygame
import math
import os
from typing import Tuple, Dict, List, TYPE_CHECKING
from src.config import TILE_SIZE
from dataclasses import dataclass, field
from src.ecs.components import Tag

# 假設這是您的組件導入路徑
from src.ecs.components import (
    Position, Velocity, Combat, Renderable, Collider, 
    ProjectileState, ExpansionLifecycle, ExpansionRenderData
)

# ----------------- 輔助函數：模擬資源載入 -----------------

def get_project_path(*subpaths):
    """模擬 get_project_path，用於載入資源"""
    # 這裡應該指向您的實際專案路徑
    return os.path.join("path", "to", "project", *subpaths)

def load_expansion_frames(outer_radius: float) -> List[pygame.Surface]:
    """
    載入 ExpandingCircleBullet 的動畫幀，並調整大小。
    在 ECS 環境中，資源載入應在初始化階段，然後傳遞給 Factory。
    """
    frames = []
    size = int(outer_radius * 2)
    # 模擬載入 9 幀圖片 (0 to 8)
    for i in range(9):
        # 實際程式碼會在這裡載入並縮放 pygame.Surface
        frame = pygame.Surface((size, size), pygame.SRCALPHA)
        # 為了演示，我們簡單地畫一個彩色圓形
        if i < 4:
             pygame.draw.circle(frame, (0, 255, 0, 100 + i*40), (size // 2, size // 2), size // 2 * (i+1) / 4)
        else:
             pygame.draw.circle(frame, (255, 0, 0, 255 - (i-4)*50), (size // 2, size // 2), size // 2)

        frames.append(frame)
    
    print(f"Loaded {len(frames)} animation frames for radius {outer_radius}")
    return frames

# ----------------- 實體工廠函數 -----------------

def create_expanding_circle_bullet(
    world: esper,
    x: float,
    y: float,
    direction: Tuple[float, float],
    tag: str = "player_bullet",
    damage: int = 10,
    max_speed: float = 300.0,
    outer_radius: float = TILE_SIZE,
    expansion_duration: float = 1.0,
    lifetime: float = 5.0,
    hide_time: float = 0.0,
    wait_time: float = 0.0,
    # ... 其他 Combat 相關參數
) -> int:
    """
    創建一個 ECS 實體，作為 ExpandingCircleBullet。
    將所有必要的數據組件附加到該實體上。
    """
    bullet_entity = world.create_entity()

    # 1. 基礎屬性 (Position, Velocity, Tag)
    world.add_component(bullet_entity, Position(x=x, y=y))
    # 子彈在創建時就設定為全速移動
    vel_x = direction[0] * max_speed
    vel_y = direction[1] * max_speed
    world.add_component(bullet_entity, Velocity(x=vel_x, y=vel_y, speed=max_speed))
    world.add_component(bullet_entity, Tag(tag=tag))


    # 2. 視覺與碰撞 (Renderable, Collider)
    # 圖像將由 RenderSystem 根據 ExpansionRenderData 動態生成或選擇幀
    world.add_component(bullet_entity, Renderable(
        image=None,  # 初始為 None，由 RenderSystem/ExpansionSystem 處理
        shape="circle",
        w=int(outer_radius * 2),
        h=int(outer_radius * 2),
        color=(255, 255, 255),
        layer=2
    ))
    # Collider 的尺寸應與 RenderData 的 outer_radius 匹配
    world.add_component(bullet_entity, Collider(
        w=int(outer_radius * 2),
        h=int(outer_radius * 2),
        pass_wall=True,  # ExpandingCircleBullet 允許穿牆
        collision_group="bullet"
    ))

    # 3. 戰鬥屬性 (Combat)
    world.add_component(bullet_entity, Combat(
        damage=damage,
        explosion_range=outer_radius, # 爆炸範圍通常是其最終大小
        explosion_damage=damage * 2,  # 假設爆炸傷害是基礎傷害的兩倍
        # ... 其他 Combat 參數 (atk_element, buffs, percentage_damage)
        collision_cooldown=0.2,
        max_penetration_count=-1, # -1 表示無限穿透 (直到擴張完成)
    ))

    # 4. 拋射物運行狀態 (ProjectileState)
    world.add_component(bullet_entity, ProjectileState(
        direction=direction,
        max_speed=max_speed,
        max_lifetime=lifetime,
        explode_on_collision=True # 碰撞即銷毀並爆炸
    ))

    # 5. 擴張生命週期 (ExpansionLifecycle)
    world.add_component(bullet_entity, ExpansionLifecycle(
        hide_time=hide_time,
        wait_time=wait_time,
    ))

    # 6. 擴張渲染數據 (ExpansionRenderData)
    # 載入動畫幀
    frames = load_expansion_frames(outer_radius)
    world.add_component(bullet_entity, ExpansionRenderData(
        outer_radius=outer_radius,
        expansion_duration=expansion_duration,
        animation_frames=frames
    ))

    return bullet_entity