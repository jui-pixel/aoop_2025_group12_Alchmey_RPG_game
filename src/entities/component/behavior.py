"""
Behavior Tree System
This module implements a behavior tree system based on the basic_enemy.py structure.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Dict, Optional, Any
import math
import pygame
from .entity_interface import ComponentInterface


class Action(ABC):
    """Base class for all actions in the behavior tree."""
    
    def __init__(self, action_id: str, duration: float = 0.0):
        self.action_id = action_id
        self.duration = duration
        self.timer = 0.0
    
    @abstractmethod
    def start(self, entity: 'EntityInterface', current_time: float) -> None:
        """Called when the action starts."""
        pass
    
    @abstractmethod
    def update(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
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
                 direction_source: Callable[['EntityInterface'], Tuple[float, float]]):
        super().__init__(action_id, duration)
        self.direction_source = direction_source
    
    def start(self, entity: 'EntityInterface', current_time: float) -> None:
        self.timer = self.duration
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            print(f"{self.action_id} completed")
            return False
        
        if not entity.movement_component:
            print(f"{self.action_id} failed: No movement component")
            return False
        
        # Get direction from the direction source
        dx, dy = self.direction_source(entity)
        entity.movement_component.move(dx, dy, dt)
        
        self.timer -= dt
        print(f"Executing {self.action_id}: timer={self.timer:.2f}")
        return True


class AttackAction(Action):
    """Attack action: Perform an attack."""
    
    def __init__(self, action_id: str, damage: int = 10, element: str = 'untyped', 
                 range: float = 500.0):
        super().__init__(action_id, duration=0.0)
        self.damage = damage
        self.element = element
        self.range = range
    
    def start(self, entity: 'EntityInterface', current_time: float) -> None:
        print(f"Starting {self.action_id}")
    
    def update(self, entity: 'EntityInterface', dt: float, current_time: float) -> None:
        if self.timer <= 0:
            # Check if entity can attack
            if (entity.combat_component and 
                not entity.combat_component.can_attack):
                print(f"{self.action_id} skipped: Cannot attack")
                return False
            
            # Find target (this would be implemented based on your game logic)
            target = self._find_target(entity)
            if not target:
                print(f"{self.action_id} failed: No target found")
                return False
            
            # Check range
            if entity.basic_component and target.basic_component:
                distance = self._calculate_distance(entity, target)
                if distance > self.range:
                    print(f"{self.action_id} failed: Target out of range")
                    return False
            
            # Perform attack
            self._perform_attack(entity, target)
            print(f"{self.action_id} completed")
            return False
        
        self.timer -= dt
        return True
    
    def _find_target(self, entity: 'EntityInterface') -> Optional['EntityInterface']:
        """Find a target to attack. This should be implemented based on your game logic."""
        # This is a placeholder - you would implement target finding logic here
        return None
    
    def _calculate_distance(self, entity: 'EntityInterface', target: 'EntityInterface') -> float:
        """Calculate distance between entity and target."""
        if not entity.basic_component or not target.basic_component:
            return float('inf')
        
        pos1 = entity.basic_component.get_center()
        pos2 = target.basic_component.get_center()
        
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx**2 + dy**2)
    
    def _perform_attack(self, entity: 'EntityInterface', target: 'EntityInterface') -> None:
        """Perform the actual attack."""
        if entity.collision_component and target.combat_component:
            entity.collision_component.handle_collision(target)


class WaitAction(Action):
    """Wait action: Pause for a specified duration."""
    
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
    
    def start(self, entity: 'EntityInterface', current_time: float) -> None:
        self.timer = self.duration
        # Stop movement
        if entity.movement_component:
            entity.movement_component.stop()
        print(f"Starting {self.action_id}: timer={self.timer:.2f}")
    
    def update(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        if self.timer <= 0:
            print(f"{self.action_id} completed")
            return False
        
        self.timer -= dt
        # Ensure entity stays stopped
        if entity.movement_component:
            entity.movement_component.stop()
        print(f"Executing {self.action_id}: timer={self.timer:.2f}")
        return True


class BehaviorNode(ABC):
    """Base class for all behavior tree nodes."""
    
    @abstractmethod
    def execute(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        """
        Execute the behavior node.
        Returns True if the node succeeded, False otherwise.
        """
        pass


class Selector(BehaviorNode):
    """Selector: Execute children until one succeeds."""
    
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        for child in self.children:
            if child.execute(entity, dt, current_time):
                return True
        return False


class Sequence(BehaviorNode):
    """Sequence: Execute children until one fails."""
    
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        for child in self.children:
            if not child.execute(entity, dt, current_time):
                return False
        return True


class ConditionNode(BehaviorNode):
    """Condition node: Check a condition and execute child if true."""
    
    def __init__(self, condition: Callable[['EntityInterface', float], bool], 
                 on_success: BehaviorNode):
        self.condition = condition
        self.on_success = on_success
    
    def execute(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        if self.condition(entity, current_time):
            return self.on_success.execute(entity, dt, current_time)
        return False


class PerformNextAction(BehaviorNode):
    """Execute the next action in the action list."""
    
    def __init__(self, action_map: Dict[str, Action]):
        self.action_map = action_map
    
    def execute(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        if not hasattr(entity, 'action_list') or not entity.action_list:
            print("No actions in action_list")
            return False
        
        action_id = entity.action_list[0]
        action = self.action_map.get(action_id)
        
        if not action:
            print(f"Invalid action_id: {action_id}")
            entity.action_list.pop(0)
            return False
        
        # Check if this is a new action
        if not hasattr(entity, 'current_action') or entity.current_action != action_id:
            entity.current_action = action_id
            action.start(entity, current_time)
        
        # Update the action
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
    
    def execute(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        if not hasattr(entity, 'action_list') or not entity.action_list:
            entity.action_list = self.combo.copy()
            print(f"Filled action_list with: {entity.action_list}")
            return True
        return False


class IdleNode(BehaviorNode):
    """Idle node: Do nothing."""
    
    def execute(self, entity: 'EntityInterface', dt: float, current_time: float) -> bool:
        if not hasattr(entity, 'current_action') or entity.current_action != 'idle':
            entity.current_action = 'idle'
            if entity.movement_component:
                entity.movement_component.stop()
            if hasattr(entity, 'action_list'):
                entity.action_list.clear()
            print("Starting idle, cleared action_list")
        return True


class BehaviorTreeComponent(ComponentInterface):
    """
    Behavior tree component that manages AI behavior using a behavior tree structure.
    """
    
    def __init__(self, entity: 'EntityInterface'):
        super().__init__(entity)
        self.behavior_tree: Optional[BehaviorNode] = None
        self.actions: Dict[str, Action] = {}
        self.default_combo: List[str] = []
        self.current_action: str = 'idle'
        self.action_list: List[str] = []
        
        # Initialize default actions
        self._initialize_default_actions()
    
    def init(self) -> None:
        """Initialize the behavior tree component."""
        self.current_action = 'idle'
        self.action_list = []
        self._build_behavior_tree()
    
    def update(self, dt: float, current_time: float) -> None:
        """Update the behavior tree."""
        if self.behavior_tree:
            self.behavior_tree.execute(self.entity, dt, current_time)
    
    def add_action(self, action_id: str, action: Action) -> None:
        """Add an action to the action map."""
        self.actions[action_id] = action
    
    def set_default_combo(self, combo: List[str]) -> None:
        """Set the default action combo."""
        self.default_combo = combo.copy()
    
    def add_action_to_list(self, action_id: str) -> None:
        """Add an action to the current action list."""
        if action_id in self.actions:
            self.action_list.append(action_id)
    
    def clear_action_list(self) -> None:
        """Clear the current action list."""
        self.action_list.clear()
    
    def set_behavior_tree(self, tree: BehaviorNode) -> None:
        """Set a custom behavior tree."""
        self.behavior_tree = tree
    
    def _initialize_default_actions(self) -> None:
        """Initialize default actions."""
        # Chase action
        self.actions['chase'] = ChaseAction(
            duration=2.0,
            action_id='chase',
            direction_source=self._get_chase_direction
        )
        
        # Attack action
        self.actions['attack'] = AttackAction(
            action_id='attack',
            damage=10,
            element='untyped',
            range=100.0
        )
        
        # Wait action
        self.actions['wait'] = WaitAction(
            duration=1.0,
            action_id='wait'
        )
        
        # Set default combo
        self.default_combo = ['attack', 'wait', 'attack', 'wait', 'chase']
    
    def _get_chase_direction(self, entity: 'EntityInterface') -> Tuple[float, float]:
        """Get the direction to chase (placeholder implementation)."""
        # This should be implemented based on your game's target finding logic
        return (0.0, 0.0)
    
    def _build_behavior_tree(self) -> None:
        """Build the default behavior tree."""
        # Interrupt condition: Check if entity should stop current behavior
        def interrupt_condition(entity: 'EntityInterface', current_time: float) -> bool:
            if not entity.combat_component:
                return True
            
            # Check if entity is stunned, frozen, etc.
            if (hasattr(entity.combat_component, 'paralysis') and entity.combat_component.paralysis):
                print("Interrupt: Paralysis")
                return True
            
            if (hasattr(entity.combat_component, 'freeze') and entity.combat_component.freeze):
                print("Interrupt: Freeze")
                return True
            
            if (hasattr(entity.combat_component, 'petrochemical') and entity.combat_component.petrochemical):
                print("Interrupt: Petrochemical")
                return True
            
            return False
        
        # Check if action list has actions
        def action_list_has_actions(entity: 'EntityInterface', current_time: float) -> bool:
            return bool(self.action_list)
        
        # Build the behavior tree
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
    
    def get_current_action(self) -> str:
        """Get the current action."""
        return self.current_action
    
    def get_action_list(self) -> List[str]:
        """Get the current action list."""
        return self.action_list.copy()
    
    def is_idle(self) -> bool:
        """Check if the entity is idle."""
        return self.current_action == 'idle'
