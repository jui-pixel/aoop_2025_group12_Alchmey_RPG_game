"""
Behavior Component Interface
Handles AI behavior using behavior tree system based on basic_enemy.py structure.
"""

from typing import Optional, Dict, Any, Callable, List, TYPE_CHECKING
from enum import Enum
from .entity_interface import ComponentInterface
from .behavior_tree import BehaviorTreeComponent, Action, BehaviorNode

if TYPE_CHECKING:
    from .entity_interface import EntityInterface


class BehaviorState(Enum):
    """Enumeration of possible behavior states."""
    IDLE = "idle"
    MOVING = "moving"
    ATTACKING = "attacking"
    FLEEING = "fleeing"
    PATROLLING = "patrolling"
    CHASING = "chasing"
    SEARCHING = "searching"
    STUNNED = "stunned"
    DEAD = "dead"


class BehaviorComponent(ComponentInterface):
    """
    Behavior component that handles AI behavior using behavior tree system.
    This is a wrapper around BehaviorTreeComponent for backward compatibility.
    """
    
    def __init__(self, entity: 'EntityInterface'):
        super().__init__(entity)
        # Create the behavior tree component
        self.behavior_tree_component = BehaviorTreeComponent(entity)
        
        # Legacy properties for backward compatibility
        self.current_behavior: BehaviorState = BehaviorState.IDLE
        self.previous_behavior: Optional[BehaviorState] = None
        self.target: Optional['EntityInterface'] = None
        self.target_position: Optional[tuple] = None
        self.behavior_data: Dict[str, Any] = {}
        self.state_timer: float = 0.0
    
    def init(self) -> None:
        """Initialize behavior component."""
        self.behavior_tree_component.init()
        self.current_behavior = BehaviorState.IDLE
        self.previous_behavior = None
        self.target = None
        self.target_position = None
        self.behavior_data = {}
        self.state_timer = 0.0
    
    def update(self, dt: float, current_time: float) -> None:
        """Update behavior component and execute behavior tree."""
        self.state_timer += dt
        self.behavior_tree_component.update(dt, current_time)
        
        # Update legacy behavior state based on current action
        current_action = self.behavior_tree_component.get_current_action()
        self._update_legacy_behavior_state(current_action)
    
    def set_behavior(self, new_behavior: BehaviorState, force: bool = False) -> None:
        """
        Set new behavior state.
        This method provides backward compatibility with the old behavior system.
        """
        # Store previous behavior
        self.previous_behavior = self.current_behavior
        
        # Set new behavior
        self.current_behavior = new_behavior
        self.state_timer = 0.0
        
        # Convert behavior state to action list
        self._convert_behavior_to_actions(new_behavior)
        
        print(f"Behavior changed: {self.previous_behavior} -> {self.current_behavior}")
    
    def _update_legacy_behavior_state(self, current_action: str) -> None:
        """Update legacy behavior state based on current action."""
        action_to_behavior = {
            'idle': BehaviorState.IDLE,
            'chase': BehaviorState.CHASING,
            'attack': BehaviorState.ATTACKING,
            'wait': BehaviorState.IDLE,
            'move': BehaviorState.MOVING,
            'flee': BehaviorState.FLEEING,
            'patrol': BehaviorState.PATROLLING,
            'search': BehaviorState.SEARCHING
        }
        
        new_behavior = action_to_behavior.get(current_action, BehaviorState.IDLE)
        if new_behavior != self.current_behavior:
            self.previous_behavior = self.current_behavior
            self.current_behavior = new_behavior
    
    def _convert_behavior_to_actions(self, behavior: BehaviorState) -> None:
        """Convert behavior state to action list."""
        behavior_to_actions = {
            BehaviorState.IDLE: ['idle'],
            BehaviorState.CHASING: ['chase'],
            BehaviorState.ATTACKING: ['attack'],
            BehaviorState.FLEEING: ['flee'],
            BehaviorState.PATROLLING: ['patrol'],
            BehaviorState.SEARCHING: ['search'],
            BehaviorState.MOVING: ['move']
        }
        
        actions = behavior_to_actions.get(behavior, ['idle'])
        self.behavior_tree_component.clear_action_list()
        for action in actions:
            self.behavior_tree_component.add_action_to_list(action)
    
    def set_target(self, target: Optional['EntityInterface']) -> None:
        """Set the target entity."""
        self.target = target
        if target and target.basic_component:
            self.target_position = target.basic_component.get_center()
    
    def set_target_position(self, position: tuple) -> None:
        """Set target position."""
        self.target_position = position
        self.target = None
    
    def get_target(self) -> Optional['EntityInterface']:
        """Get current target entity."""
        return self.target
    
    def get_target_position(self) -> Optional[tuple]:
        """Get current target position."""
        if self.target and self.target.basic_component:
            return self.target.basic_component.get_center()
        return self.target_position
    
    def clear_target(self) -> None:
        """Clear current target."""
        self.target = None
        self.target_position = None
    
    def is_in_state(self, state: BehaviorState) -> bool:
        """Check if currently in a specific state."""
        return self.current_behavior == state
    
    def get_state_duration(self) -> float:
        """Get duration of current state."""
        return self.state_timer
    
    def set_behavior_data(self, key: str, value: Any) -> None:
        """Set behavior-specific data."""
        self.behavior_data[key] = value
    
    def get_behavior_data(self, key: str, default: Any = None) -> Any:
        """Get behavior-specific data."""
        return self.behavior_data.get(key, default)
    
    # Behavior Tree Component Methods (Delegation)
    def add_action(self, action_id: str, action: Action) -> None:
        """Add an action to the behavior tree."""
        self.behavior_tree_component.add_action(action_id, action)
    
    def set_default_combo(self, combo: List[str]) -> None:
        """Set the default action combo."""
        self.behavior_tree_component.set_default_combo(combo)
    
    def add_action_to_list(self, action_id: str) -> None:
        """Add an action to the current action list."""
        self.behavior_tree_component.add_action_to_list(action_id)
    
    def clear_action_list(self) -> None:
        """Clear the current action list."""
        self.behavior_tree_component.clear_action_list()
    
    def set_behavior_tree(self, tree: BehaviorNode) -> None:
        """Set a custom behavior tree."""
        self.behavior_tree_component.set_behavior_tree(tree)
    
    def get_current_action(self) -> str:
        """Get the current action."""
        return self.behavior_tree_component.get_current_action()
    
    def get_action_list(self) -> List[str]:
        """Get the current action list."""
        return self.behavior_tree_component.get_action_list()
    
    def is_idle(self) -> bool:
        """Check if the entity is idle."""
        return self.behavior_tree_component.is_idle()
    
