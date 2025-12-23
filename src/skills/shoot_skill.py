from typing import Optional, Dict, Tuple, List
import math
# 移除對舊 Bullet 類別的依賴
# from ..entities.bullet.bullet import Bullet 
from ..buffs.element_buff import ElementBuff, ELEMENTAL_BUFFS, apply_elemental_buff
from .abstract_skill import Skill
from ..core.config import TILE_SIZE

# 假設這是您的 ECS 實體工廠函數所在的路徑
from ..entities.bullet.bullet import create_standard_bullet_entity 

class ShootingSkill(Skill):
    def __init__(self, name: str, element: str, energy_cost: float = 20.0,
                 damage_level: int = 0, penetration_level: int = 0, elebuff_level: int = 0,
                 explosion_level: int = 0, speed_level: int = 0):
        super().__init__(name, "shooting", element, energy_cost)
        
        # Level-based parameters (保持不變)
        self.damage_level = damage_level
        self.penetration_level = penetration_level
        self.elebuff_level = elebuff_level
        self.explosion_level = explosion_level
        self.speed_level = speed_level
        
        # Calculated values based on levels (保持不變)
        self.bullet_damage = 10 * (1 + 0.1 * damage_level)
        self.bullet_speed = 3 * TILE_SIZE * (1 + 0.1 * speed_level)
        self.bullet_size = 8
        self.bullet_element = element
        self.max_penetration_count = penetration_level
        self.explosion_range = explosion_level * 10
        self.element_buff_enable = elebuff_level > 0
        
        # Default values for other parameters (保持不變)
        self.bullet_max_hp_percentage_damage = 0
        self.bullet_current_hp_percentage_damage = 0
        self.bullet_lose_hp_percentage_damage = 0
        self.explosion_damage = explosion_level * 10
        self.explosion_max_hp_percentage_damage = 0
        self.explosion_current_hp_percentage_damage = 0
        self.explosion_lose_hp_percentage_damage = 0
        self.explosion_element = element
        self.collision_cooldown = 0.2
        self.pass_wall = False
        self.cause_death = True
        
        self.bullet_effects = [ELEMENTAL_BUFFS[element]] if self.element_buff_enable else []
        self.explosion_buffs = [ELEMENTAL_BUFFS[element]] if self.element_buff_enable else []

    def activate(self, player: 'Player', game: 'Game', target_position: Tuple[float, float], current_time: float) -> None:
        self.last_used = current_time

        # 1. 計算子彈中心點和方向
        player_center_x = player.x
        player_center_y = player.y
        
        dx = target_position[0] - player_center_x
        dy = target_position[1] - player_center_y
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude == 0:
            return
        direction = (dx / magnitude, dy / magnitude)

        # 2. 準備 ECS 實體工廠所需的參數
        damage_to_element = player.damage_to_element
        start_pos = (player_center_x, player_center_y)
        
        # 整合百分比傷害參數為一個字典
        percentage_damage = {
            'max_hp': self.bullet_max_hp_percentage_damage,
            'current_hp': self.bullet_current_hp_percentage_damage,
            'lose_hp': self.bullet_lose_hp_percentage_damage,
        }
        
        # 3. 呼叫 ECS 實體工廠函數
        # 此處取代了原本的 `bullet = Bullet(...)` 呼叫
        bullet_entity_id = create_standard_bullet_entity(
            world=game.world, # 傳遞 ECS World 實例
            start_pos=start_pos,
            w=self.bullet_size,
            h=self.bullet_size,
            tag="player", # 修正 tag 為 'player' 以避免友傷
            direction=direction,
            
            # ProjectileState & Movement
            max_speed=self.bullet_speed,
            
            # Combat
            damage=self.bullet_damage,
            atk_element=self.element,
            damage_to_element=damage_to_element,
            max_penetration_count=self.max_penetration_count,
            collision_cooldown=self.collision_cooldown,
            buffs=self.bullet_effects,
            explosion_range=self.explosion_range,
            explosion_damage=self.explosion_damage,
            explosion_element=self.explosion_element,
            explosion_buffs=self.explosion_buffs,
            percentage_damage=percentage_damage,
            cause_death=self.cause_death,

            # Collider
            pass_wall=self.pass_wall,
            
            # lifetime
            lifetime=5.0
        )
        
        # 4. 移除舊的實體管理 (在 ECS 中，實體會被自動添加到 World)
        # 舊程式碼: game.entity_manager.bullet_group.add(bullet)
        # 現在不再需要此行，因為 ECS System 會自動處理新增的實體。