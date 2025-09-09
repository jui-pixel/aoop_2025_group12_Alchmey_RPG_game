from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Dict, Optional, Any
import math
import pygame
from ..attack_entity import AttackEntity
from ..buffable_entity import BuffableEntity
from ..health_entity import HealthEntity
from ..movement_entity import MovementEntity
from ...config import TILE_SIZE, RED
from ..bullet.bullet import Bullet
from ..bullet.expand_circle_bullet import ExpandingCircleBullet
from ..buff.element_buff import ELEMENTAL_BUFFS
from ..basic_entity import BasicEntity

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
        if action.update(entity, dt, current_time):
            return True
        entity.action_list.pop(0)
        action.reset()
        return False

class RefillActionList(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action'], default_combo: Callable[['Enemy1'], List[str]]):
        self.actions = actions
        self.default_combo = default_combo
    
    def execute(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        entity.action_list = self.default_combo(entity)
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
    
    @abstractmethod
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        pass
    
    @abstractmethod
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        pass
    
    def reset(self) -> None:
        self.timer = 0.0

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
        if self.timer <= 0 or not entity.game.player:
            print(f"{self.action_id} {'completed' if self.timer <= 0 else 'failed: No player'}")
            return False
        dx, dy = self.direction_source(entity)
        entity.move(dx, dy, dt)
        self.timer -= dt
        return True

class AttackAction(Action):
    def __init__(self, action_id: str, damage: int = 5, bullet_speed: float = 400.0, 
                 bullet_size: int = 5, effects: List[Any] = None):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.effects = effects or [ELEMENTAL_BUFFS['Burn']]
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if not entity.can_attack:
            print(f"{self.action_id} skipped: Cannot attack")
            return False
        if not entity.game.player:
            print(f"{self.action_id} failed: No player")
            return False
        dx = entity.game.player.x - entity.x
        dy = entity.game.player.y - entity.y
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
            tag="enemy_bullet",
            max_speed=self.bullet_speed,
            direction=direction,
            damage=self.damage,
            buffs=self.effects
        )
        bullet.image = pygame.Surface((self.bullet_size, self.bullet_size))
        bullet.image.fill(RED)
        bullet.rect = bullet.image.get_rect(center=(entity.x, entity.y))
        entity.game.entity_manager.enemy_bullet_group.add(bullet)
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
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        self.timer = self.duration
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not entity.game:
            print(f"{self.action_id} {'completed' if self.timer <= 0 else 'failed: No game'}")
            return False
        
        # Check for nearby player bullets
        bullet_direction = None
        min_distance = float('inf')
        for bullet in entity.game.entity_manager.player_bullet_group:
            dx = bullet.x - entity.x
            dy = bullet.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance < 3 * TILE_SIZE and distance > 0:
                if distance < min_distance:
                    min_distance = distance
                    bullet_direction = (dx / distance, dy / distance)
        
        if bullet_direction:
            # Move away from nearest bullet
            entity.move(-bullet_direction[0], -bullet_direction[1], dt)
        elif entity.game.player:
            # Move away from player if no bullets
            dx = entity.x - entity.game.player.x
            dy = entity.y - entity.game.player.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                direction = (dx / distance, dy / distance)
                entity.move(direction[0], direction[1], dt)
            else:
                # Random movement if too close
                import random
                entity.move(random.uniform(-1, 1), random.uniform(-1, 1), dt)
        else:
            # Random movement if no player or bullets
            import random
            entity.move(random.uniform(-1, 1), random.uniform(-1, 1), dt)
        
        self.timer -= dt
        return True

class SpecialAttackAction(Action):
    def __init__(self, action_id: str, damage: int = 10, bullet_speed: float = 300.0, 
                 outer_radius: float = TILE_SIZE * 2, expansion_duration: float = 1.5):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.outer_radius = outer_radius
        self.expansion_duration = expansion_duration
    
    def start(self, entity: 'Enemy1', current_time: float) -> None:
        entity.current_action = self.action_id
        print(f"Starting {self.action_id}")
    
    def update(self, entity: 'Enemy1', dt: float, current_time: float) -> bool:
        if not entity.can_attack:
            print(f"{self.action_id} skipped: Cannot attack")
            return False
        if not entity.game.player:
            print(f"{self.action_id} failed: No player")
            return False
        dx = entity.game.player.x - entity.x
        dy = entity.game.player.y - entity.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 500 or distance == 0:
            print(f"{self.action_id} failed: Player out of range")
            return False
        direction = (dx / distance, dy / distance)
        bullet = ExpandingCircleBullet(
            x=entity.x,
            y=entity.y,
            w=TILE_SIZE // 2,
            h=TILE_SIZE // 2,
            game=entity.game,
            tag="enemy_bullet",
            max_speed=self.bullet_speed,
            direction=direction,
            damage=self.damage,
            outer_radius=self.outer_radius,
            expansion_duration=self.expansion_duration
        )
        entity.game.entity_manager.enemy_bullet_group.add(bullet)
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
        if not entity.game.player or entity.game.player.invulnerable:
            print(f"{self.action_id} failed: No player or player invulnerable")
            return False
        if entity.rect.colliderect(entity.game.player.rect):
            killed, damage = entity.game.player.take_damage(self.damage, entity.element)
            if killed:
                print("Player died!")
            print(f"{self.action_id} completed: Dealt {damage} damage")
            return False
        return False

class Enemy1(AttackEntity, BuffableEntity, HealthEntity, MovementEntity):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = TILE_SIZE // 2, h: int = TILE_SIZE // 2, 
                 image: Optional[pygame.Surface] = None, shape: str = "rect", game: 'Game' = None, tag: str = "",
                 base_max_hp: int = 100, max_shield: int = 0, dodge_rate: float = 0.0, max_speed: float = 5 * TILE_SIZE,
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
        
        # Enemy-specific attributes
        self.current_action = 'idle'
        self.action_list = []
        self.bullet_speed = 400.0
        self.bullet_damage = 5
        self.bullet_size = 5
        self.bullet_effects = [ELEMENTAL_BUFFS['Burn']]
        self.vision_radius = 10  # In tiles
        self.patrol_points = [(x + i * TILE_SIZE * 2, y) for i in range(-2, 3)]
        
        # Define actions
        self.actions = {
            'chase': ChaseAction(
                duration=2.0,
                action_id='chase',
                direction_source=lambda e: (
                    (e.game.player.x - e.x) / max(1e-10, math.sqrt((e.game.player.x - e.x)**2 + (e.game.player.y - e.y)**2)),
                    (e.game.player.y - e.y) / max(1e-10, math.sqrt((e.game.player.x - e.x)**2 + (e.game.player.y - e.y)**2))
                ) if e.game.player else (0, 0)
            ),
            'attack': AttackAction(
                action_id='attack',
                damage=self.bullet_damage,
                bullet_speed=self.bullet_speed,
                bullet_size=self.bullet_size,
                effects=self.bullet_effects
            ),
            'pause': WaitAction(duration=1.0, action_id='pause'),
            'patrol': PatrolAction(
                duration=5.0,
                action_id='patrol',
                waypoints=self.patrol_points
            ),
            'dodge': DodgeAction(
                duration=1.0,
                action_id='dodge'
            ),
            'special_attack': SpecialAttackAction(
                action_id='special_attack',
                damage=10,
                bullet_speed=300.0,
                outer_radius=TILE_SIZE * 2,
                expansion_duration=1.5
            ),
            'melee': MeleeAttackAction(
                action_id='melee',
                damage=self.bullet_damage
            )
        }
        
        # Dynamic combo
        def get_default_combo(entity: 'Enemy1') -> List[str]:
            if not entity.game.player:
                return ['patrol', 'pause']
            hp_ratio = entity.current_hp / entity.max_hp
            dx = entity.game.player.x - entity.x
            dy = entity.game.player.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            # Check for nearby player bullets
            bullet_nearby = False
            for bullet in entity.game.entity_manager.player_bullet_group:
                b_dx = bullet.x - entity.x
                b_dy = bullet.y - entity.y
                b_distance = math.sqrt(b_dx**2 + b_dy**2)
                if b_distance < 3 * TILE_SIZE:
                    bullet_nearby = True
                    break
            if hp_ratio < 0.3:  # Low HP: prioritize dodge
                return ['dodge', 'pause', 'attack', 'dodge', 'chase']
            elif bullet_nearby:  # Nearby bullet: dodge
                return ['dodge', 'pause', 'attack']
            elif distance < 2 * TILE_SIZE:  # Player too close: dodge or melee
                return ['dodge', 'melee', 'pause']
            elif distance < entity.vision_radius * TILE_SIZE:  # Player in range
                return ['attack', 'dodge', 'special_attack', 'dodge', 'chase']
            else:  # Player out of range
                return ['patrol', 'pause']
        
        # Behavior tree
        def interrupt_condition(entity: 'Enemy1', current_time: float) -> bool:
            if not entity.is_alive():
                print("Interrupt: Entity not alive")
                return True
            if not entity.game.player:
                print("Interrupt: No player")
                return True
            dx = entity.game.player.x - entity.x
            dy = entity.game.player.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            return distance >= entity.vision_radius * TILE_SIZE or distance <= 0
        
        def low_hp_condition(entity: 'Enemy1', current_time: float) -> bool:
            return entity.current_hp / entity.max_hp < 0.3
        
        def bullet_nearby_condition(entity: 'Enemy1', current_time: float) -> bool:
            for bullet in entity.game.entity_manager.player_bullet_group:
                dx = bullet.x - entity.x
                dy = bullet.y - entity.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance < 3 * TILE_SIZE:
                    return True
            return False
        
        def player_close_condition(entity: 'Enemy1', current_time: float) -> bool:
            if not entity.game.player:
                return False
            dx = entity.game.player.x - entity.x
            dy = entity.game.player.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            return distance < 2 * TILE_SIZE
        
        def action_list_has_actions(entity: 'Enemy1', current_time: float) -> bool:
            return bool(entity.action_list)
        
        self.behavior_tree = Selector([
            ConditionNode(
                condition=interrupt_condition,
                on_success=IdleNode()
            ),
            ConditionNode(
                condition=low_hp_condition,
                on_success=Sequence([
                    PerformNextAction(self.actions),
                    RefillActionList(self.actions, get_default_combo)
                ])
            ),
            ConditionNode(
                condition=bullet_nearby_condition,
                on_success=Sequence([
                    PerformNextAction(self.actions),
                    RefillActionList(self.actions, get_default_combo)
                ])
            ),
            ConditionNode(
                condition=player_close_condition,
                on_success=Sequence([
                    PerformNextAction(self.actions),
                    RefillActionList(self.actions, get_default_combo)
                ])
            ),
            ConditionNode(
                condition=action_list_has_actions,
                on_success=PerformNextAction(self.actions)
            ),
            RefillActionList(self.actions, get_default_combo),
            IdleNode()
        ])
    
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    def check_collision_with_player(self, current_time: float) -> int:
        # Move collision damage to MeleeAttackAction
        return 0
    
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