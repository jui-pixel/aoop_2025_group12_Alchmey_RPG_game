# src/entities/enemy/enemy1.py
from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Dict, Optional, Any
import math
import pygame
import random
from ..attack_entity import AttackEntity
from ..buffable_entity import BuffableEntity
from ..health_entity import HealthEntity
from ..movement_entity import MovementEntity
from ...config import TILE_SIZE, RED
from ..bullet.bullet import Bullet
from ..bullet.expand_circle_bullet import ExpandingCircleBullet
from ..buff.element_buff import ELEMENTAL_BUFFS
from ..basic_entity import BasicEntity
from ...config import PASSABLE_TILES

# 行為樹節點（與前次一致）
class BehaviorNode(ABC):
    @abstractmethod
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        pass

class ConditionNode(BehaviorNode):
    def __init__(self, condition: Callable[['Enemy1', float], bool], on_success: BehaviorNode, on_fail: BehaviorNode = None):
        self.condition = condition
        self.on_success = on_success
        self.on_fail = on_fail
    
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if self.condition(entity, current_time):
            return self.on_success.execute(entity, dt, current_time)
        elif self.on_fail:
            return self.on_fail.execute(entity, dt, current_time)
        return False

class Sequence(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        for child in self.children:
            if not child.execute(entity, dt, current_time):
                return False
        return True

class Selector(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        for child in self.children:
            if child.execute(entity, dt, current_time):
                return True
        return False

class PerformNextAction(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action']):
        self.actions = actions
    
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if not entity.action_list:
            return False
        action_id = entity.action_list[0]
        action = self.actions.get(action_id)
        if not action:
            entity.action_list.pop(0)
            return False
        if not action.started:
            action.start(entity, current_time)
            action.started = True
        if action.update(entity, dt, current_time):
            print(f"{action.timer:.2f} seconds remaining for {action.action_id}")
            return True
        entity.action_list.pop(0)
        print(f"Action {action.action_id} finished")
        print(f"Remaining actions: {entity.action_list}")
        action.reset()
        if len(entity.action_list) >= 1:
            return True
        return False

class RefillActionList(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action'], default_combo: Callable[['Enemy1'], List[str]]):
        self.actions = actions
        self.default_combo = default_combo
    
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        entity.action_list = self.default_combo(entity)
        print(f"Refilled action list: {entity.action_list}")
        return True

class IdleNode(BehaviorNode):
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        entity.current_action = 'idle'
        entity.move(0, 0, dt)  # Stop movement
        return True

# 動作定義
class Action(ABC):
    def __init__(self, action_id: str, duration: float = 0.0):
        self.action_id = action_id
        self.duration = duration
        self.timer = 0.0
        self.started = False
    
    @abstractmethod
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        pass
    
    @abstractmethod
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        pass
    
    def reset(self) -> None:
        self.timer = 0.0
        self.started = False

class RandomMoveAction(Action):
    def __init__(self, duration: float, action_id: str, speed: float):
        super().__init__(action_id, duration)
        self.speed = speed
        self.direction: Tuple[float, float] = (0.0, 0.0)
        self.change_interval: float = 1.0  # Change direction every second
        self.change_timer: float = 0.0
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        self.timer = self.duration
        self.change_timer = 0.0
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            print(f"{self.action_id} completed")
            return False
        
        self.change_timer -= dt
        if self.change_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.direction = (math.cos(angle), math.sin(angle))
            self.change_timer = self.change_interval
            print(f"{self.action_id} new direction: dx={self.direction[0]:.2f}, dy={self.direction[1]:.2f}")
        
        entity.move(self.direction[0] * self.speed / entity.speed, 
                    self.direction[1] * self.speed / entity.speed, dt)
        
        self.timer -= dt
        return True

class ChaseAction(Action):
    def __init__(self, duration: float, action_id: str, 
                 direction_source: Callable[['Enemy1'], Tuple[float, float]]):
        super().__init__(action_id, duration)
        self.direction_source = direction_source
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        self.timer = self.duration
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not entity.game.entity_manager.player:
            print(f"{self.action_id} {'completed' if self.timer <= 0 else 'failed: No player'}")
            return False
        dx, dy = self.direction_source(entity)
        entity.move(dx, dy, dt)
        print(f"{self.action_id} moving: dx={dx:.2f}, dy={dy:.2f}")
        self.timer -= dt
        return True

class AttackAction(Action):
    def __init__(self, action_id: str, damage: int = 5, bullet_speed: float = 400.0, 
                 bullet_size: int = 5, effects: List[Any] = None, tag: str = ""):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.effects = effects or [ELEMENTAL_BUFFS['fire']]
        self.tag = tag
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if not entity.can_attack:
            print(f"{self.action_id} skipped: Cannot attack")
            return False
        if not entity.game.entity_manager.player:
            print(f"{self.action_id} failed: No player")
            return False
        dx = entity.game.entity_manager.player.x - entity.x
        dy = entity.game.entity_manager.player.y - entity.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 500 or distance == 0:
            print(f"{self.action_id} failed: Player out of range")
            return False
        direction = (dx / distance, dy / distance)
        bullet = Bullet(
            x=entity.x,
            y=entity.y,
            w=self.bullet_size,
            h=self.bullet_size,
            game=entity.game,
            tag=self.tag,
            max_speed=self.bullet_speed,
            direction=direction,
            damage=self.damage,
            buffs=self.effects,
        )
        bullet.image = pygame.Surface((self.bullet_size, self.bullet_size))
        bullet.image.fill(RED)
        bullet.rect = bullet.image.get_rect(center=(entity.x, entity.y))
        entity.game.entity_manager.bullet_group.add(bullet)
        print(f"{self.action_id} completed")
        return False

class WaitAction(Action):
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        self.timer = self.duration
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        self.timer -= dt
        if self.timer <= 0:
            print(f"{self.action_id} completed")
            return False
        return True

class PatrolAction(Action):
    def __init__(self, duration: float, action_id: str, waypoints: List[Tuple[float, float]]):
        super().__init__(action_id, duration)
        self.waypoints = waypoints
        self.current_waypoint = 0
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        self.timer = self.duration
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            print(f"{self.action_id} completed")
            return False
        if not self.waypoints:
            return False
        target = self.waypoints[self.current_waypoint]
        dx = target[0] - entity.x
        dy = target[1] - entity.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance < 10:
            self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            return True
        direction = (dx / max(distance, 1e-10), dy / max(distance, 1e-10))
        entity.move(direction[0], direction[1], dt)
        self.timer -= dt
        return True

class DodgeAction(Action):
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
        self.max_threat_distance: float = 5 * TILE_SIZE  # 最大威脅檢測範圍
        self.dodge_speed_multiplier: float = 1.5  # 閃避時的速度倍率
        self.max_bullets_to_check: int = 5  # 最多檢查 5 顆子彈
        self.dodge_direction_timer: float = 0.0  # 固定閃避方向計時器
        self.chosen_dodge_direction: Tuple[float, float] = (0.0, 0.0)  # 當前選擇的閃避方向
        self.dodge_direction_duration: float = 0.2  # 固定方向 0.2 秒
        self.player_threat_weight: float = 0.4  # 玩家威脅權重
        self.max_prediction_time: float = 0.2  # 最大預判時間（秒）
        self.close_bullet_threshold: float = 1.5 * TILE_SIZE  # 過近子彈閾值

    def start(self, entity: 'Enemy1', current_time: float) -> None:
        """
        開始閃避動作，初始化計時器和動作ID。
        """
        self.timer = self.duration
        entity.current_action = self.action_id
        print(f"開始動作 {self.action_id}: 計時器={self.timer:.2f}")

    def predict_intercept(self, entity_pos: Tuple[float, float], bullet_pos: Tuple[float, float], 
                        bullet_vel: Tuple[float, float], entity_speed: float) -> Tuple[float, float]:
        """
        預判子彈與敵人的交會點，基於二次方程。
        - entity_pos: 敵人位置 (x, y)
        - bullet_pos: 子彈當前位置 (x, y)
        - bullet_vel: 子彈速度向量 (vx, vy)
        - entity_speed: 敵人閃避速度
        返回預測交會點 (pred_x, pred_y) 或 None（無解）。
        """
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

    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        """
        更新閃避動作，結合子彈預判和玩家位置，模擬像人一樣的閃躲。
        - 若子彈距離 < 1 TILE_SIZE，直接遠離該子彈。
        - 否則使用預判子彈交會點和玩家位置，選擇垂直閃避方向（左右）。
        - 固定方向 0.5 秒避免抽搐，檢查可通行瓦片避免卡牆。
        """
        if self.timer <= 0 or not entity.game:
            print(f"{self.action_id} {'完成' if self.timer <= 0 else '失敗：無遊戲實例'}")
            return False

        # 更新閃避方向計時器
        self.dodge_direction_timer -= dt
        dungeon = entity.game.dungeon_manager.get_dungeon()
        move_direction = self.chosen_dodge_direction
        speed_multiplier = 1.0

        
        closest_bullet = None
        min_distance = float('inf')
        bullets = list(entity.game.entity_manager.bullet_group)[:self.max_bullets_to_check]
        for bullet in bullets:
            if bullet.tag != "player":
                continue
            dx = bullet.x - entity.x
            dy = bullet.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance < min_distance:
                min_distance = distance
                closest_bullet = bullet
                
        if closest_bullet and min_distance < self.close_bullet_threshold:
            # 子彈過近，直接遠離
            dx = closest_bullet.x - entity.x
            dy = closest_bullet.y - entity.y
            distance = max(min_distance, 0.1)
            threat_dir = (-dx / distance, -dy / distance)  # 反向遠離
            move_direction = threat_dir
            speed_multiplier = self.dodge_speed_multiplier * 2
            self.chosen_dodge_direction = move_direction
            self.dodge_direction_timer = 0.0
            
        # 若計時器結束或無方向，重新計算
        elif self.dodge_direction_timer <= 0 or move_direction == (0.0, 0.0):
            # 無過近子彈，使用預判和玩家位置
            bullet_threat = [0.0, 0.0]
            bullet_threat_count = 0
            for bullet in bullets:
                if bullet.tag != "player":
                    continue
                pred_pos = self.predict_intercept(
                    (entity.x, entity.y),
                    (bullet.x, bullet.y),
                    bullet.velocity,
                    entity.speed * self.dodge_speed_multiplier
                )
                if pred_pos:
                    dx = pred_pos[0] - entity.x
                    dy = pred_pos[1] - entity.y
                    distance = math.sqrt(dx**2 + dy**2)
                    if 0 < distance < self.max_threat_distance:
                        weight = 1.0 / max(distance, 0.1)
                        bullet_threat[0] += (dx / distance) * weight
                        bullet_threat[1] += (dy / distance) * weight
                        bullet_threat_count += 1

            # 計算玩家威脅向量
            player_threat = [0.0, 0.0]
            if entity.game.entity_manager.player:
                dx = entity.x - entity.game.entity_manager.player.x
                dy = entity.y - entity.game.entity_manager.player.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance > TILE_SIZE * 0.5:
                    magnitude = max(distance, 0.1)
                    player_threat = (dx / magnitude, dy / magnitude)

            # 結合威脅向量
            threat_vector = [
                bullet_threat[0] + player_threat[0] * self.player_threat_weight,
                bullet_threat[1] + player_threat[1] * self.player_threat_weight
            ]
            magnitude = math.sqrt(threat_vector[0]**2 + threat_vector[1]**2)

            if magnitude > 0:
                threat_dir = (threat_vector[0] / magnitude, threat_vector[1] / magnitude)
                directions = [
                    (-threat_dir[1], threat_dir[0]),  # 左（順時針 90 度）
                    (threat_dir[1], -threat_dir[0])   # 右（逆時針 90 度）
                ]
                random.shuffle(directions)
                for dx, dy in directions:
                    new_x = entity.x + dx * entity.speed * self.dodge_speed_multiplier * dt
                    new_y = entity.y + dy * entity.speed * self.dodge_speed_multiplier * dt
                    if dungeon.get_tile_at((new_x, new_y)) in PASSABLE_TILES:
                        move_direction = (dx, dy)
                        speed_multiplier = self.dodge_speed_multiplier
                        self.chosen_dodge_direction = move_direction
                        self.dodge_direction_timer = self.dodge_direction_duration
                        break
                else:
                    move_direction = (0.0, 0.0)
                    self.chosen_dodge_direction = move_direction
                    self.dodge_direction_timer = self.dodge_direction_duration
            else:
                move_direction = (0.0, 0.0)
                self.chosen_dodge_direction = move_direction
                self.dodge_direction_timer = self.dodge_direction_duration
                
        # 執行移動
        if move_direction != (0.0, 0.0):
            new_x = entity.x + move_direction[0] * entity.speed * speed_multiplier * dt
            new_y = entity.y + move_direction[1] * entity.speed * speed_multiplier * dt
            if dungeon.get_tile_at((new_x, new_y)) in PASSABLE_TILES:
                entity.move(move_direction[0], move_direction[1], dt * speed_multiplier)
            else:
                self.chosen_dodge_direction = (0.0, 0.0)
                self.dodge_direction_timer = self.dodge_direction_duration

        self.timer -= dt
        return True

class SpecialAttackAction(Action):
    def __init__(self, action_id: str, damage: int = 10, bullet_speed: float = 300.0, 
                 outer_radius: float = TILE_SIZE * 2, expansion_duration: float = 1.5, tag: str = ""):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.outer_radius = outer_radius
        self.expansion_duration = expansion_duration
        self.tag = tag  
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if not entity.can_attack:
            print(f"{self.action_id} skipped: Cannot attack")
            return False
        if not entity.game.entity_manager.player:
            print(f"{self.action_id} failed: No player")
            return False
        dx = entity.game.entity_manager.player.x - entity.x
        dy = entity.game.entity_manager.player.y - entity.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 500 or distance == 0:
            print(f"{self.action_id} failed: Player out of range")
            return False
        direction = (dx / distance, dy / distance)
        r = TILE_SIZE // 2
        num_bullets = int(math.ceil(distance / r) + 5)  # Extend beyond player
        for i in range(num_bullets):
            # Calculate position with sinusoidal offset
            t = i * r / distance  # Normalized distance along path
            offset_magnitude = r * 2 * math.sin(t * 2 * math.pi * 2)  # Wave with 2 cycles
            # Perpendicular vector to direction
            perp = (-direction[1], direction[0])  # Rotate 90 degrees
            bullet_x = entity.x + i * r * direction[0] + offset_magnitude * perp[0]
            bullet_y = entity.y + i * r * direction[1] + offset_magnitude * perp[1]
            # Dynamic wait_time: starts at 0.1s, increases by 0.05s per bullet
            wait_time = 0.1 + 0.02 * i
            
            bullet = ExpandingCircleBullet(
                x=bullet_x,
                y=bullet_y,
                w=TILE_SIZE // 2,
                h=TILE_SIZE // 2,
                game=entity.game,
                tag=self.tag,
                max_speed=0.0,  # Stationary bullet
                direction=direction,
                damage=self.damage,
                outer_radius=self.outer_radius,
                explosion_range=self.outer_radius,  # Synced with outer_radius
                expansion_duration=self.expansion_duration,
                wait_time=wait_time,
            )
            entity.game.entity_manager.bullet_group.add(bullet)
        print(f"{self.action_id} completed")
        return False

class MeleeAttackAction(Action):
    def __init__(self, action_id: str, damage: int = 5):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if not entity.game.entity_manager.player or entity.game.entity_manager.player.invulnerable:
            print(f"{self.action_id} failed: No player or player invulnerable")
            return False
        entity.collision(entity.game.entity_manager.player)
        return False

class Enemy1(AttackEntity, BuffableEntity, HealthEntity, MovementEntity):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = TILE_SIZE // 2, h: int = TILE_SIZE // 2, 
                 image: Optional[pygame.Surface] = None, shape: str = "rect", game: 'Game' = None, tag: str = "",
                 base_max_hp: int = 100, max_shield: int = 0, dodge_rate: float = 0.0, max_speed: float = 2 * TILE_SIZE,
                 element: str = "untyped", defense: int = 10, resistances: Optional[Dict[str, float]] = None, 
                 damage_to_element: Optional[Dict[str, float]] = None, can_move: bool = True, can_attack: bool = True, 
                 invulnerable: bool = False):
        # Initialize BasicEntity first
        BasicEntity.__init__(self, x, y, w, h, image, shape, game, tag)
        
        # Initialize mixins without basic init
        MovementEntity.__init__(self, x, y, w, h, image, shape, game, tag, max_speed, can_move, init_basic=False)
        HealthEntity.__init__(self, x, y, w, h, image, shape, game, tag, base_max_hp, max_shield, dodge_rate, element, defense, resistances, invulnerable, init_basic=False)
        AttackEntity.__init__(self, x, y, w, h, image, shape, game, tag, can_attack, damage_to_element, 
                             atk_element=element, damage=0, max_penetration_count=0, collision_cooldown=0.2, 
                             explosion_range=0.0, explosion_damage=0, init_basic=False)
        BuffableEntity.__init__(self, x, y, w, h, image, shape, game, tag, init_basic=False)
        
        if self.image is None:
            self.image = pygame.Surface((w, h))
            self.image.fill((0, 255, 0))  # 綠色方塊，代表敵人1
            self.rect = self.image.get_rect(center=(x, y))
        
        # Enemy-specific attributes
        self.current_action = 'idle'
        self.action_list = []
        # self.bullet_speed = 400.0
        # self.bullet_damage = 5
        # self.bullet_size = 5
        # self.bullet_effects = [ELEMENTAL_BUFFS['fire']] # Example effect
        self.vision_radius = 15  # In tiles
        self.patrol_points = [(x + i * TILE_SIZE * 2, y) for i in range(-2, 3)]
        
        # Define actions
        self.actions = {
            'chase': ChaseAction(
                duration=0.3,
                action_id='chase',
                direction_source=lambda e: (
                    (e.game.entity_manager.player.x - e.x) / max(1e-10, math.sqrt((e.game.entity_manager.player.x - e.x)**2 + (e.game.entity_manager.player.y - e.y)**2)),
                    (e.game.entity_manager.player.y - e.y) / max(1e-10, math.sqrt((e.game.entity_manager.player.x - e.x)**2 + (e.game.entity_manager.player.y - e.y)**2))
                ) if e.game.entity_manager.player else (0, 0)
            ),
            'attack': AttackAction(
                action_id='attack',
                damage=5,
                bullet_speed=400.0,
                bullet_size=5,
                effects=[ELEMENTAL_BUFFS['fire']],
                tag = self.tag
            ),
            'pause': WaitAction(duration=0.3, action_id='pause'),
            'pause2': WaitAction(duration=1.5, action_id='pause2'),
            'patrol': PatrolAction(
                duration=5.0,
                action_id='patrol',
                waypoints=self.patrol_points
            ),
            'dodge': DodgeAction(
                duration=0.5,
                action_id='dodge'
            ),
            'special_attack': SpecialAttackAction(
                action_id='special_attack',
                damage=10,
                bullet_speed=0.0,
                outer_radius=TILE_SIZE // 2,
                expansion_duration=1.0,
                tag = self.tag
            ),
            'melee': MeleeAttackAction(
                action_id='melee',
                damage=5
            ),
            'random_move': RandomMoveAction(
                duration=0.5,
                action_id='random_move',
                speed=self.max_speed
            ),
        }
        
        # Dynamic combo
        def get_default_combo(entity: 'Enemy1') -> List[str]:
            if not entity.game.entity_manager.player:
                return ['patrol', 'pause']
            hp_ratio = entity.current_hp / entity.max_hp
            dx = entity.game.entity_manager.player.x - entity.x
            dy = entity.game.entity_manager.player.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            # Check for nearby player bullets
            bullet_nearby = False
            for bullet in entity.game.entity_manager.bullet_group:
                if bullet.tag != "player_bullet":
                    continue
                b_dx = bullet.x - entity.x
                b_dy = bullet.y - entity.y
                b_distance = math.sqrt(b_dx**2 + b_dy**2)
                if b_distance < 3 * TILE_SIZE:
                    bullet_nearby = True
                    break
            # return ['chase']
            # return ['attack']
            # return ['dodge']
            # return ['melee']
            # return ['special_attack']
            # return ['patrol']
            # return ['pause']
            if hp_ratio < 0.3:  # Low HP: prioritize dodge
                return ['dodge', 'pause', 'attack', 'pause', 'chase']
            elif bullet_nearby:  # Nearby bullet: dodge
                return ['dodge', 'pause', 'attack', 'pause']
            elif distance < 2 * TILE_SIZE:  # Player too close: dodge or melee
                return ['chase', 'melee', 'pause']
            elif distance < entity.vision_radius * TILE_SIZE:  # Player in range
                return ['attack', 'dodge', 'attack', 'chase', 'random_move']
            else:  # Player out of range
                return ['patrol', 'pause']
        
        # Behavior tree
        def interrupt_condition(entity: 'Enemy1', current_time: float) -> bool:
            if not entity.is_alive():
                print("Interrupt: Entity not alive")
                return True
            if not entity.game.entity_manager.player:
                print("Interrupt: No player")
                return True
            if entity.current_action not in ['dodge', 'special_attack', 'attack'] and bullet_nearby_condition(entity, current_time):
                entity.action_list = ['dodge', 'special_attack', 'pause2', 'random_move']
                return True
            dx = entity.game.entity_manager.player.x - entity.x
            dy = entity.game.entity_manager.player.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            return distance >= entity.vision_radius * TILE_SIZE or distance <= 0
        
        def low_hp_condition(entity: 'Enemy1', current_time: float) -> bool:
            return entity.current_hp / entity.max_hp < 0.3
        
        def bullet_nearby_condition(entity: 'Enemy1', current_time: float) -> bool:
            for bullet in entity.game.entity_manager.bullet_group:
                if bullet.tag != "player":
                    continue
                dx = bullet.x - entity.x
                dy = bullet.y - entity.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance < 3 * TILE_SIZE:
                    return True
            return False
        
        def player_close_condition(entity: 'Enemy1', current_time: float) -> bool:
            if not entity.game.entity_manager.player:
                return False
            dx = entity.game.entity_manager.player.x - entity.x
            dy = entity.game.entity_manager.player.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            return distance < 2 * TILE_SIZE
        
        def action_list_has_actions(entity: 'Enemy1', current_time: float) -> bool:
            # print(f"Action list: {entity.action_list}")
            return len(entity.action_list) >= 1
        
        self.behavior_tree = Selector([
            ConditionNode(
                condition=interrupt_condition,
                on_success=IdleNode()
            ),
            ConditionNode(
                condition=action_list_has_actions,
                on_success=PerformNextAction(self.actions)
            ),
            ConditionNode(
                condition=low_hp_condition,
                on_success=Sequence([
                    RefillActionList(self.actions, get_default_combo)
                ])
            ),
            ConditionNode(
                condition=bullet_nearby_condition,
                on_success=Sequence([
                    RefillActionList(self.actions, get_default_combo)
                ])
            ),
            ConditionNode(
                condition=player_close_condition,
                on_success=Sequence([
                    RefillActionList(self.actions, get_default_combo)
                ])
            ),
            RefillActionList(self.actions, get_default_combo),
            IdleNode()
        ])
    
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    # def check_collision_with_player(self, current_time: float) -> int:
    #     # Move collision damage to MeleeAttackAction
    #     return 0
    
    def update(self, dt: float, current_time: float) -> None:
        # Explicitly call each mixin's update
        MovementEntity.update(self, dt, current_time)
        HealthEntity.update(self, dt, current_time)
        AttackEntity.update(self, dt, current_time)
        BuffableEntity.update(self, dt, current_time)
        # Execute behavior tree
        if self.behavior_tree:
            self.behavior_tree.execute(self, dt, current_time)
    
    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        BasicEntity.draw(self, screen, camera_offset)
        self.draw_health_bar(screen, camera_offset)