from abc import ABC, abstractmethod
from typing import List, Tuple, Callable
import pygame
import math
from src.config import TILE_SIZE, RED
from src.entities.movable_entity import MovableEntity
from src.entities.character.weapons.weapon import Bullet
from src.entities.element_buff_library import ELEMENTBUFFLIBRARY

class Action(ABC):
    """基類：定義動作的執行邏輯"""
    def __init__(self, action_id: str, duration: float = 0.0):
        self.action_id = action_id
        self.duration = duration
        self.timer = 0.0

    @abstractmethod
    def start(self, entity: 'BasicEnemy', current_time: float) -> None:
        pass

    @abstractmethod
    def update(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        pass

    def reset(self) -> None:
        self.timer = 0.0

class ChaseAction(Action):
    """追逐動作：朝玩家移動"""
    def __init__(self, duration: float, action_id: str, direction_source: Callable[['BasicEnemy'], Tuple[float, float]]):
        super().__init__(action_id, duration)
        self.direction_source = direction_source

    def start(self, entity: 'BasicEnemy', current_time: float) -> None:
        self.timer = self.duration
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")

    def update(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not entity.game.player:
            print(f"{self.action_id} {'completed' if self.timer <= 0 else 'failed: No player'}")
            return False
        self.timer -= dt
        dx, dy = self.direction_source(entity)
        entity.move(dx, dy, dt)
        print(f"Executing {self.action_id}: timer={self.timer:.2f}")
        return True

class AttackAction(Action):
    """攻擊動作：向玩家發射一次子彈"""
    def __init__(self, action_id: str):
        super().__init__(action_id, duration=0.0)

    def start(self, entity: 'BasicEnemy', current_time: float) -> None:
        print(f"Starting {self.action_id}")

    def update(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            if not entity.canfire():
                print(f"{self.action_id} skipped: Cooldown or status")
                return False
            player_pos = entity.game.player.pos
            dx = player_pos[0] - entity.pos[0]
            dy = player_pos[1] - entity.pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 500 or distance == 0:
                print(f"{self.action_id} failed: Player out of range")
                return False
            direction = (dx / distance, dy / distance)
            bullet = Bullet(
                pos=entity.pos,
                direction=direction,
                speed=entity.bullet_speed,
                damage=entity.bullet_damage,
                dungeon=entity.dungeon,
                shooter=entity,
                fire_time=current_time,
                effects=entity.bullet_effects
            )
            bullet.image = pygame.Surface((entity.bullet_size, entity.bullet_size))
            bullet.image.fill((255, 0, 0))
            bullet.rect = bullet.image.get_rect(center=entity.pos)
            entity.game.enemy_bullet_group.add(bullet)
            entity.last_fired = current_time
            print(f"{self.action_id} completed")
            return False
        self.timer -= dt
        return True

class WaitAction(Action):
    """等待動作：暫停指定時間"""
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)

    def start(self, entity: 'BasicEnemy', current_time: float) -> None:
        self.timer = self.duration
        entity.velocity = [0.0, 0.0]
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")

    def update(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            print(f"{self.action_id} completed")
            return False
        self.timer -= dt
        entity.velocity = [0.0, 0.0]
        print(f"Executing {self.action_id}: timer={self.timer:.2f}")
        return True

class BehaviorNode(ABC):
    """行為樹節點基類"""
    @abstractmethod
    def execute(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        pass

class Selector(BehaviorNode):
    """選擇器：執行子節點，直到某個成功"""
    def __init__(self, children: List[BehaviorNode]):
        self.children = children

    def execute(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        for child in self.children:
            if child.execute(entity, dt, current_time):
                return True
        return False

class ConditionNode(BehaviorNode):
    """條件節點：檢查特定條件"""
    def __init__(self, condition: Callable[['BasicEnemy', float], bool], on_success: BehaviorNode):
        self.condition = condition
        self.on_success = on_success

    def execute(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        if self.condition(entity, current_time):
            return self.on_success.execute(entity, dt, current_time)
        return False

class PerformNextAction(BehaviorNode):
    """執行action_list中的下一個動作"""
    def __init__(self, action_map: dict):
        self.action_map = action_map

    def execute(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        if not entity.action_list:
            print("No actions in action_list")
            return False
        action_id = entity.action_list[0]
        action = self.action_map.get(action_id)
        if not action:
            print(f"Invalid action_id: {action_id}")
            entity.action_list.pop(0)
            return False
        if entity.current_action != action_id:
            entity.current_action = action_id
            action.start(entity, current_time)
        result = action.update(entity, dt, current_time)
        if not result:
            entity.action_list.pop(0)
            print(f"Action {action_id} completed, remaining actions: {len(entity.action_list)}")
        return True

class RefillActionList(BehaviorNode):
    """當action_list為空時重新填充"""
    def __init__(self, action_map: dict, combo: List[str]):
        self.action_map = action_map
        self.combo = combo

    def execute(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        if not entity.action_list:
            entity.action_list.extend(self.combo)
            print(f"Filled action_list with: {entity.action_list}")
            return True
        return False

class IdleNode(BehaviorNode):
    """空閒節點"""
    def execute(self, entity: 'BasicEnemy', dt: float, current_time: float) -> bool:
        if entity.current_action != 'idle':
            entity.current_action = 'idle'
            entity.velocity = [0.0, 0.0]
            entity.action_list.clear()
            print("Starting idle, cleared action_list")
        # print("Idling")
        return True

class BasicEnemy(MovableEntity):
    def __init__(self, pos: Tuple[float, float], game: 'Game'):
        super().__init__(pos=pos, game=game, size=TILE_SIZE // 2, color=RED)
        self.speed = 100.0
        self.health = 50
        self.max_health = 50
        self.coll_damage = 10
        self.last_hit_time = 0.0
        self.hit_cooldown = 1.0
        self.base_defense = 5
        self.eff_defense = self.base_defense
        self.fire_rate = 1.5
        self.last_fired = 0.0
        self.bullet_speed = 400.0
        self.bullet_damage = 5
        self.bullet_size = 5
        self.bullet_effects = [ELEMENTBUFFLIBRARY['Burn']]
        self.current_action = 'idle'
        self.action_list = []
        # Define actions
        self.actions = {
            'chase': ChaseAction(
                duration=2.0,
                action_id='chase',
                direction_source=lambda e: (
                    (e.game.player.pos[0] - e.pos[0]) / max(1e-10, math.sqrt((e.game.player.pos[0] - e.pos[0])**2 + (e.game.player.pos[1] - e.pos[1])**2)),
                    (e.game.player.pos[1] - e.pos[1]) / max(1e-10, math.sqrt((e.game.player.pos[0] - e.pos[0])**2 + (e.game.player.pos[1] - e.pos[1])**2))
                ) if e.game.player else (0, 0)
            ),
            'attack': AttackAction(action_id='attack'),
            'pause': WaitAction(duration=1.0, action_id='pause')
        }
        # Default combo sequence
        self.default_combo = ['attack', 'pause', 'attack', 'pause', 'chase']
        # Behavior tree
        def interrupt_condition(entity: 'BasicEnemy', current_time: float) -> bool:
            if entity.paralysis or entity.freeze or entity.petrochemical:
                print("Interrupt: Status effect")
                return True
            if not entity.game.player:
                print("Interrupt: No player")
                return True
            dx = entity.game.player.pos[0] - entity.pos[0]
            dy = entity.game.player.pos[1] - entity.pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            if distance >= entity.vision_radius * TILE_SIZE or distance <= 0:
                # print("Interrupt: Player out of range")
                return True
            return False
        
        def action_list_has_actions(entity: 'BasicEnemy', current_time: float) -> bool:
            return bool(entity.action_list)
        
        
        self.behavior_tree = Selector([
            ConditionNode(
                condition=interrupt_condition,
                on_success=IdleNode()
            ),
            ConditionNode(
                condition=action_list_has_actions,
                on_success=PerformNextAction(self.actions)
            ),
            RefillActionList(self.actions, self.default_combo),
            IdleNode()
        ])

    def check_collision_with_player(self, current_time: float) -> int:
        if not self.game.player or self.game.player.invulnerable > 0:
            return 0
        if current_time - self.last_hit_time < self.hit_cooldown:
            return 0
        if self.rect.colliderect(self.game.player.rect):
            killed, damage = self.game.player.take_damage(self.coll_damage, self.element)
            self.last_hit_time = current_time
            if self.game.player.health <= 0:
                print("Player died!")
            return damage
        return 0

    def update(self, dt: float, current_time: float) -> None:
        super().update(dt, current_time)
        self.behavior_tree.execute(self, dt, current_time)
        self.check_collision_with_player(current_time)