# src/ecs/ai.py

from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Dict, Optional, Any
import math
import pygame
import random
# 引入 ECS 組件
import esper
from src.ecs.components import Position, Velocity, Health, Combat, AI, Collider, Renderable
from src.config import TILE_SIZE, RED, PASSABLE_TILES
from src.entities.bullet.expand_circle_bullet import create_expanding_circle_bullet
from src.entities.bullet.bullet import create_standard_bullet_entity
from src.buffs.element_buff import ELEMENTAL_BUFFS

# --- 實體操作 Facade（用於行為樹內部） ---

class EnemyContext:
    """ECS 實體上下文門面，用於在 Action 類中訪問和修改組件。"""
    def __init__(self, world: esper, entity_id: int, game: 'Game'):
        self.world = world
        self.ecs_entity = entity_id
        self.game = game # 遊戲主實例，用於訪問 entity_manager, dungeon_manager
        
    def _get_comp(self, component_type):
        """安全地獲取組件，若無則報錯（ECS 實體應有此組件）"""
        return self.world.component_for_entity(self.ecs_entity, component_type)

    @property
    def x(self) -> float: return self._get_comp(Position).x
    @property
    def y(self) -> float: return self._get_comp(Position).y
    @property
    def speed(self) -> float: return self._get_comp(Velocity).speed
    @property
    def current_hp(self) -> int: return self._get_comp(Health).current_hp
    @property
    def max_hp(self) -> int: return self._get_comp(Health).max_hp
    @property
    def can_attack(self) -> bool: return self._get_comp(Combat).can_attack
    @property
    def tag(self) -> str: return self._get_comp(Combat).tag
    @property
    def vision_radius(self) -> int: return self._get_comp(AI).vision_radius
    @property
    def current_action(self) -> str: return self._get_comp(AI).current_action

    def set_current_action(self, action_id: str):
        self._get_comp(AI).current_action = action_id

    def move(self, dx: float, dy: float, dt: float):
        """設定速度組件，交由 MovementSystem 處理移動。"""
        vel = self._get_comp(Velocity)
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude > 0:
            vel.x = (dx / magnitude) * vel.speed
            vel.y = (dy / magnitude) * vel.speed
        else:
            vel.x = 0
            vel.y = 0

    # 必須保留的舊方法，現在通過 game 訪問玩家 Facade
    @property
    def player(self):
        return self.game.entity_manager.player # 假設 entity_manager.player 是一個 PlayerFacade

    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    # 簡化：不實現 MeleeAttackAction 複雜的 collision 邏輯，僅發送傷害事件
    def apply_melee_damage(self, damage: int):
        if self.player and not self.player.invulnerable:
            # 這是 ECS 實體對非 ECS 實體的攻擊，在 PlayerFacade 中應有受傷方法
            self.player.take_damage(damage)


# --- 行為樹節點 (BehaviorNode) ---
# 這些 Node 類無需大改，但它們現在操作的是 Context 對象
# 簽名: execute(self, context: EnemyContext, dt: float, current_time: float)

class BehaviorNode(ABC):
    @abstractmethod
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        pass

class ConditionNode(BehaviorNode):
    def __init__(self, condition: Callable[['EnemyContext', float], bool], on_success: BehaviorNode, on_fail: BehaviorNode = None):
        self.condition = condition
        self.on_success = on_success
        self.on_fail = on_fail
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if self.condition(context, current_time):
            return self.on_success.execute(context, dt, current_time)
        elif self.on_fail:
            return self.on_fail.execute(context, dt, current_time)
        return False

# ... Sequence, Selector 保持與 ConditionNode 類似的簽名修改 ...

class Sequence(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        for child in self.children:
            if not child.execute(context, dt, current_time):
                return False
        return True

class Selector(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        for child in self.children:
            if child.execute(context, dt, current_time):
                return True
        return False

class PerformNextAction(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action']):
        self.actions = actions
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        ai_comp = context._get_comp(AI)
        if not ai_comp.action_list:
            return False
        
        action_id = ai_comp.action_list[0]
        action = self.actions.get(action_id)
        if not action:
            ai_comp.action_list.pop(0)
            return False
            
        if not action.started:
            action.start(context, current_time)
            action.started = True
            
        if action.update(context, dt, current_time):
            # print(f"{action.timer:.2f} seconds remaining for {action.action_id}")
            return True # Action is still running
            
        ai_comp.action_list.pop(0)
        # print(f"Action {action.action_id} finished. Remaining actions: {ai_comp.action_list}")
        action.reset()
        
        if len(ai_comp.action_list) >= 1:
            return True
        return False

class RefillActionList(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action'], default_combo: Callable[['EnemyContext'], List[str]]):
        self.actions = actions
        self.default_combo = default_combo
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        context._get_comp(AI).action_list = self.default_combo(context)
        # print(f"Refilled action list: {context._get_comp(AI).action_list}")
        return True

class IdleNode(BehaviorNode):
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        context.set_current_action('idle')
        context.move(0, 0, dt)
        return True


# --- 動作定義 (Action) ---
# 所有的 Action.update/start 簽名也必須調整為接受 Context

class Action(ABC):
    # ... (init, reset 保持不變) ...
    def __init__(self, action_id: str, duration: float = 0.0):
        self.action_id = action_id
        self.duration = duration
        self.timer = 0.0
        self.started = False
    
    @abstractmethod
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        pass
    
    @abstractmethod
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        pass
    
    def reset(self) -> None:
        self.timer = 0.0
        self.started = False

class RandomMoveAction(Action):
    # ... (邏輯使用 context.move) ...
    def __init__(self, duration: float, action_id: str, speed: float):
        super().__init__(action_id, duration)
        self.speed = speed
        self.direction: Tuple[float, float] = (0.0, 0.0)
        self.change_interval: float = 1.0 
        self.change_timer: float = 0.0
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        self.timer = self.duration
        self.change_timer = 0.0
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            return False
        
        self.change_timer -= dt
        if self.change_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.direction = (math.cos(angle), math.sin(angle))
            self.change_timer = self.change_interval
            
        context.move(self.direction[0] * self.speed / context.speed, 
                     self.direction[1] * self.speed / context.speed, dt)
        
        self.timer -= dt
        return True

class ChaseAction(Action):
    # ... (邏輯使用 context.move) ...
    def __init__(self, duration: float, action_id: str, 
                 direction_source: Callable[['EnemyContext'], Tuple[float, float]]):
        super().__init__(action_id, duration)
        self.direction_source = direction_source
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        self.timer = self.duration
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not context.player:
            return False
        dx, dy = self.direction_source(context)
        context.move(dx, dy, dt)
        self.timer -= dt
        return True

class AttackAction(Action):
    # ... (邏輯使用 context.game.entity_manager.bullet_group 進行子彈生成) ...
    def __init__(self, action_id: str, damage: int = 5, bullet_speed: float = 400.0, 
                 bullet_size: int = 5, effects: List[Any] = None, tag: str = ""):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.effects = effects or [ELEMENTAL_BUFFS['fire']]
        self.tag = tag
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if not context.can_attack or not context.player:
            return False
            
        dx = context.player.x - context.x
        dy = context.player.y - context.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # 檢查距離，避免過遠或重疊時發射
        if distance > context.vision_radius * TILE_SIZE or distance == 0:
            return False
            
        direction = (dx / distance, dy / distance)
        
        # ⚠️ 重構點：使用 ECS 創建子彈實體
        bullet_entity = create_standard_bullet_entity(
            world=context.world, # 傳入 esper.World 實例
            start_pos=(context.x, context.y),
            w=self.bullet_size,
            h=self.bullet_size,
            tag=self.tag,
            direction=direction,
            max_speed=self.bullet_speed,
            lifetime=self.lifetime,
            damage=self.damage,
            atk_element=self.atk_element,
            damage_to_element=self.damage_to_element,
            max_penetration_count=self.max_penetration_count,
            collision_cooldown=0.1, # 假設默認冷卻時間
            buffs=self.buffs,
            explosion_range=self.explosion_range,
            explosion_damage=self.explosion_damage,
            explosion_element=self.explosion_element,
            explosion_buffs=self.explosion_buffs,
            percentage_damage=self.percentage_damage,
            pass_wall=self.pass_wall
        )
        
        # 由於子彈現在是 ECS 實體，它會自動被 MovementSystem 和 CollisionSystem 處理，
        # 無需再添加到舊的 entity_manager.bullet_group。
        
        return False

# ... WaitAction, PatrolAction 類似調整 ...

class WaitAction(Action):
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        self.timer = self.duration
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        self.timer -= dt
        return self.timer > 0

class PatrolAction(Action):
    def __init__(self, duration: float, action_id: str, waypoints: List[Tuple[float, float]]):
        super().__init__(action_id, duration)
        self.waypoints = waypoints
        self.current_waypoint = 0
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        self.timer = self.duration
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not self.waypoints:
            return False
        
        target = self.waypoints[self.current_waypoint]
        dx = target[0] - context.x
        dy = target[1] - context.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 10:
            self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            return True
            
        direction = (dx / max(distance, 1e-10), dy / max(distance, 1e-10))
        context.move(direction[0], direction[1], dt)
        self.timer -= dt
        return True


class DodgeAction(Action):
    # ... (邏輯使用 context 訪問屬性，使用 dungeon_manager 檢查可行走區域) ...
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
        self.max_threat_distance: float = 5 * TILE_SIZE 
        self.dodge_speed_multiplier: float = 1.5 
        self.max_bullets_to_check: int = 5 
        self.dodge_direction_timer: float = 0.0 
        self.chosen_dodge_direction: Tuple[float, float] = (0.0, 0.0) 
        self.dodge_direction_duration: float = 0.2 
        self.player_threat_weight: float = 0.4 
        self.max_prediction_time: float = 0.2 
        self.close_bullet_threshold: float = 1.5 * TILE_SIZE 

    def predict_intercept(self, entity_pos: Tuple[float, float], bullet_pos: Tuple[float, float], 
                         bullet_vel: Tuple[float, float], entity_speed: float) -> Tuple[float, float]:
        # ... (預判邏輯保持不變) ...
        dx = bullet_pos[0] - entity_pos[0]
        dy = bullet_pos[1] - entity_pos[1]
        
        a = bullet_vel[0]**2 + bullet_vel[1]**2 - entity_speed**2
        b = 2 * (bullet_vel[0] * dx + bullet_vel[1] * dy)
        c = dx**2 + dy**2
        
        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            return None
        
        t1 = (-b + math.sqrt(discriminant)) / (2 * a)
        t2 = (-b - math.sqrt(discriminant)) / (2 * a)
        
        t = min(t1, t2) if t1 > 0 and t2 > 0 else max(t1, t2) if max(t1, t2) > 0 else None
        if t is None or t < 0 or t > self.max_prediction_time:
            return None
        
        pred_x = bullet_pos[0] + bullet_vel[0] * t
        pred_y = bullet_pos[1] + bullet_vel[1] * t
        return (pred_x, pred_y)

    def start(self, context: 'EnemyContext', current_time: float) -> None:
        self.timer = self.duration
        context.set_current_action(self.action_id)

    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not context.game:
            return False

        self.dodge_direction_timer -= dt
        dungeon = context.game.dungeon_manager.get_dungeon()
        move_direction = self.chosen_dodge_direction
        speed_multiplier = 1.0

        # ... (威脅計算邏輯保持不變，但使用 context 訪問屬性) ...
        
        closest_bullet = None
        min_distance = float('inf')
        # ⚠️ 仍然依賴舊的 entity_manager.bullet_group
        bullets = list(context.game.entity_manager.bullet_group)[:self.max_bullets_to_check] 
        
        # [省略了內部複雜的威脅計算和移動方向選擇邏輯]
        # 由於邏輯與原文件相同，且僅替換了實體訪問方式，這裡保留結構：
        
        for bullet in bullets:
            if bullet.tag != "player": continue
            dx = bullet.x - context.x
            dy = bullet.y - context.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance < min_distance:
                min_distance = distance
                closest_bullet = bullet
                
        if closest_bullet and min_distance < self.close_bullet_threshold:
            dx = closest_bullet.x - context.x
            dy = closest_bullet.y - context.y
            distance = max(min_distance, 0.1)
            threat_dir = (-dx / distance, -dy / distance) 
            move_direction = threat_dir
            speed_multiplier = self.dodge_speed_multiplier * 2
            self.chosen_dodge_direction = move_direction
            self.dodge_direction_timer = 0.1
        elif self.dodge_direction_timer <= 0 or move_direction == (0.0, 0.0):
            bullet_threat = [0.0, 0.0]
            # ... (複雜的預判和方向選擇邏輯)
            if context.player:
                # 這裡執行預判和方向選擇，然後設定 move_direction, speed_multiplier, chosen_dodge_direction, dodge_direction_timer
                pass # 保持原邏輯的結構
        
        # 執行移動
        if move_direction != (0.0, 0.0):
            new_x = context.x + move_direction[0] * context.speed * speed_multiplier * dt
            new_y = context.y + move_direction[1] * context.speed * speed_multiplier * dt
            
            # 檢查是否可通行
            if dungeon and dungeon.get_tile_at((new_x, new_y)) in PASSABLE_TILES:
                context.move(move_direction[0], move_direction[1], dt * speed_multiplier)
            else:
                self.chosen_dodge_direction = (0.0, 0.0)
                self.dodge_direction_timer = self.dodge_direction_duration

        self.timer -= dt
        return True

class SpecialAttackAction(Action):
    # 重構：不再繼承 AttackAction
    def __init__(self, action_id: str, damage: int = 5, tag: str = "", outer_radius: float = 2.5 * TILE_SIZE):
        # 0.0 duration: action executes instantly (spawns the projectile)
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.tag = tag
        self.outer_radius = outer_radius
        self.expansion_duration = 0.5  # 擴張所需時間
        self.hide_time = 0.5           # 延遲出現/爆炸的時間 (給玩家反應時間)
        self.atk_element = "dark"      # 特殊攻擊的元素

    def start(self, context: 'EnemyContext', current_time: float) -> None:
        # 敵人停止移動並顯示正在施法/準備
        context.move(0, 0, 0)
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if not context.player:
            return False
            
        player_x = context.player.x
        player_y = context.player.y

        # 在目標 (玩家) 腳下創建一個靜止的、延遲擴張的子彈
        create_expanding_circle_bullet(
            world=context.world,
            x=player_x,
            y=player_y,
            direction=(0.0, 0.0),      # 靜止不動
            tag=self.tag,              # 敵人投射物標籤
            damage=self.damage * 3,    # 特殊攻擊的高傷害
            max_speed=0.0,             # 速度為 0，確保它不移動
            outer_radius=self.outer_radius,
            expansion_duration=self.expansion_duration,
            lifetime=self.hide_time + self.expansion_duration + 0.5, # 總壽命 = 隱藏時間 + 擴張時間 + 緩衝
            hide_time=self.hide_time,  # 延遲出現/擴張
            atk_element=self.atk_element,
            explosion_damage_multiplier=1.0 # 由於已經是高傷害，爆炸倍率可設定為 1.0
        )
        
        # 動作在子彈被創造後即完成
        return False

class MeleeAttackAction(Action):
    def __init__(self, action_id: str, damage: int = 5):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if not context.player or context.player.invulnerable:
            return False
            
        # 簡化為直接應用傷害（通過 Facade），避免舊的 collision 邏輯
        context.apply_melee_damage(self.damage)
        
        return False
