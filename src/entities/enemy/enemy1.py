from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Dict, Optional, Any
import math
import pygame
from combat_entity import CombatEntity
from config import TILE_SIZE, RED
from entities.character.weapons.weapon import Bullet
from entities.element_buff_library import ELEMENTBUFFLIBRARY

class Action(ABC):
    """Base class for all actions in the behavior tree."""
    
    def __init__(self, action_id: str, duration: float = 0.0):
        self.action_id = action_id
        self.duration = duration
        self.timer = 0.0
    
    @abstractmethod
    def start(self, entity: 'enemy1', current_time: float) -> None:
        """Called when the action starts."""
        pass
    
    @abstractmethod
    def update(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        """
        Called every frame while the action is active.
        Returns True if the action should continue, False if it's complete.
        """
        pass
    
    def reset(self) -> None:
        """Reset the action to its initial state."""
        self.timer = 0.0

class ChaseAction(Action):
    """Chase action: Move towards a target."""
    
    def __init__(self, duration: float, action_id: str, 
                 direction_source: Callable[['enemy1'], Tuple[float, float]]):
        super().__init__(action_id, duration)
        self.direction_source = direction_source
    
    def start(self, entity: 'enemy1', current_time: float) -> None:
        self.timer = self.duration
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not entity.game.player:
            print(f"{self.action_id} {'completed' if self.timer <= 0 else 'failed: No player'}")
            return False
        
        dx, dy = self.direction_source(entity)
        entity.move(dx, dy, dt)
        
        self.timer -= dt
        print(f"Executing {self.action_id}: timer={self.timer:.2f}")
        return True

class AttackAction(Action):
    """Attack action: Fire a bullet at the player."""
    
    def __init__(self, action_id: str, damage: int = 5, bullet_speed: float = 400.0, 
                 bullet_size: int = 5, effects: List[Any] = None):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.effects = effects or [ELEMENTBUFFLIBRARY['Burn']]
    
    def start(self, entity: 'enemy1', current_time: float) -> None:
        print(f"Starting {self.action_id}")
    
    def update(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            if not entity.can_attack or (current_time - entity.last_fired < entity.fire_rate):
                print(f"{self.action_id} skipped: Cannot attack or on cooldown")
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
                pos=(entity.x, entity.y),
                direction=direction,
                speed=self.bullet_speed,
                damage=self.damage,
                dungeon=entity.dungeon,
                shooter=entity,
                fire_time=current_time,
                effects=self.effects
            )
            bullet.image = pygame.Surface((self.bullet_size, self.bullet_size))
            bullet.image.fill(RED)
            bullet.rect = bullet.image.get_rect(center=(entity.x, entity.y))
            entity.game.enemy_bullet_group.add(bullet)
            entity.last_fired = current_time
            print(f"{self.action_id} completed")
            return False
        
        self.timer -= dt
        return True

class WaitAction(Action):
    """Wait action: Pause for a specified duration."""
    
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
    
    def start(self, entity: 'enemy1', current_time: float) -> None:
        self.timer = self.duration
        entity.velocity = (0.0, 0.0)
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            print(f"{self.action_id} completed")
            return False
        
        self.timer -= dt
        entity.velocity = (0.0, 0.0)
        print(f"Executing {self.action_id}: timer={self.timer:.2f}")
        return True

class BehaviorNode(ABC):
    """Base class for all behavior tree nodes."""
    
    @abstractmethod
    def execute(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        """
        Execute the behavior node.
        Returns True if the node succeeded, False otherwise.
        """
        pass

class Selector(BehaviorNode):
    """Selector: Execute children until one succeeds."""
    
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        for child in self.children:
            if child.execute(entity, dt, current_time):
                return True
        return False

class Sequence(BehaviorNode):
    """Sequence: Execute children until one fails."""
    
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        for child in self.children:
            if not child.execute(entity, dt, current_time):
                return False
        return True

class ConditionNode(BehaviorNode):
    """Condition node: Check a condition and execute child if true."""
    
    def __init__(self, condition: Callable[['enemy1', float], bool], 
                 on_success: BehaviorNode):
        self.condition = condition
        self.on_success = on_success
    
    def execute(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        if self.condition(entity, current_time):
            return self.on_success.execute(entity, dt, current_time)
        return False

class PerformNextAction(BehaviorNode):
    """Execute the next action in the action list."""
    
    def __init__(self, action_map: Dict[str, Action]):
        self.action_map = action_map
    
    def execute(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
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
    """Refill the action list when it's empty."""
    
    def __init__(self, action_map: Dict[str, Action], combo: List[str]):
        self.action_map = action_map
        self.combo = combo
    
    def execute(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        if not entity.action_list:
            entity.action_list = self.combo.copy()
            print(f"Filled action_list with: {entity.action_list}")
            return True
        return False

class IdleNode(BehaviorNode):
    """Idle node: Do nothing."""
    
    def execute(self, entity: 'enemy1', dt: float, current_time: float) -> bool:
        if entity.current_action != 'idle':
            entity.current_action = 'idle'
            entity.velocity = (0.0, 0.0)
            entity.action_list.clear()
            print("Starting idle, cleared action_list")
        return True

class enemy1(CombatEntity):
    def __init__(self, x: float = 0, y: float = 0, w: int = 32, h: int = 32, 
                 image: Optional[pygame.Surface] = None, shape: str = "rect", 
                 game: 'Game' = None, tag: str = "", base_max_hp: int = 50, 
                 max_shield: int = 0, dodge_rate: float = 0.0, max_speed: float = 100.0, 
                 element: str = "untyped", resistances: Optional[Dict[str, float]] = None, 
                 damage_to_element: Optional[Dict[str, float]] = None, 
                 can_move: bool = True, can_attack: bool = True, invulnerable: bool = False):
        super().__init__(x, y, w, h, image, shape, game, tag, base_max_hp, max_shield, 
                         dodge_rate, max_speed, element, resistances, damage_to_element,
                         can_move, can_attack, invulnerable)
        
        # Additional attributes for behavior
        self.current_action = 'idle'
        self.action_list = []
        self.fire_rate = 1.5
        self.last_fired = 0.0
        self.bullet_speed = 400.0
        self.bullet_damage = 5
        self.bullet_size = 5
        self.bullet_effects = [ELEMENTBUFFLIBRARY['Burn']]
        self.vision_radius = 10  # In tiles
        
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
            'pause': WaitAction(duration=1.0, action_id='pause')
        }
        
        # Default combo sequence
        self.default_combo = ['attack', 'pause', 'attack', 'pause', 'chase']
        
        # Behavior tree
        def interrupt_condition(entity: 'enemy1', current_time: float) -> bool:
            if not entity.is_alive():
                print("Interrupt: Entity not alive")
                return True
            if not entity.game.player:
                print("Interrupt: No player")
                return True
            dx = entity.game.player.x - entity.x
            dy = entity.game.player.y - entity.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance >= entity.vision_radius * TILE_SIZE or distance <= 0:
                return True
            return False
        
        def action_list_has_actions(entity: 'enemy1', current_time: float) -> bool:
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
        if not self.game.player or self.game.player.invulnerable:
            return 0
        if current_time - self.last_fired < self.fire_rate:
            return 0
        if self.rect.colliderect(self.game.player.rect):
            killed, damage = self.game.player.take_damage(self.bullet_damage, self.element)
            self.last_fired = current_time
            if killed:
                print("Player died!")
            return damage
        return 0
    
    def update(self, dt: float, current_time: float) -> None:
        super().update(dt, current_time)
        if self.behavior_tree:
            self.behavior_tree.execute(self, dt, current_time)
        self.check_collision_with_player(current_time)