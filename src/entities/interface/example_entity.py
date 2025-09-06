"""
Example Entity Implementation
This module demonstrates how to use the new entity interface system.
"""

import pygame
import math
from typing import List, Tuple, Optional
from .basic import Basic
from .behavior_component import BehaviorState
from .behavior_tree import (ChaseAction, AttackAction, WaitAction, 
                          Selector, ConditionNode, PerformNextAction, 
                          RefillActionList, IdleNode)


class ExampleEnemy(Basic):
    """
    Example enemy entity that demonstrates the use of the behavior tree system.
    This enemy can move, attack, and has AI behavior using behavior trees.
    """
    
    def __init__(self, x: float, y: float, game: 'Game', target: 'EntityInterface' = None):
        # Create a simple red square image
        image = pygame.Surface((32, 32))
        image.fill((255, 0, 0))  # Red color
        
        # Initialize the basic entity
        super().__init__(x, y, 32, 32, image, "rectangle", game, "enemy")
        
        # Configure combat properties
        self.combat_component.base_max_hp = 50
        self.combat_component.max_hp = 50
        self.combat_component.current_hp = 50
        self.combat_component.element = 'fire'
        self.combat_component.can_move = True
        self.combat_component.can_attack = True
        self.combat_component.dodge_rate = 0.1  # 10% dodge chance
        
        # Configure movement properties
        self.movement_component.base_max_speed = 100.0
        self.movement_component.max_speed = 100.0
        self.movement_component.speed = 100.0
        
        # Configure collision properties
        self.collision_component.damage = 10
        self.collision_component.element = 'fire'
        self.collision_component.max_penetration_count = 1
        
        # Set up behavior tree
        self._setup_behavior_tree(target)
        
        # Set lifetime (optional)
        self.timing_component.set_lifetime(60.0)  # 60 seconds
    
    def _setup_behavior_tree(self, target: Optional['EntityInterface']) -> None:
        """Set up the behavior tree for this enemy."""
        # Define actions
        actions = {
            'chase': ChaseAction(
                duration=2.0,
                action_id='chase',
                direction_source=self._get_chase_direction
            ),
            'attack': AttackAction(
                action_id='attack',
                damage=10,
                element='fire',
                range=100.0
            ),
            'wait': WaitAction(
                duration=1.0,
                action_id='wait'
            )
        }
        
        # Add actions to behavior component
        for action_id, action in actions.items():
            self.behavior_component.add_action(action_id, action)
        
        # Set default combo
        default_combo = ['attack', 'wait', 'attack', 'wait', 'chase']
        self.behavior_component.set_default_combo(default_combo)
        
        # Set target if provided
        if target:
            self.behavior_component.set_target(target)
        
        # Build behavior tree
        self._build_behavior_tree()
    
    def _get_chase_direction(self, entity: 'EntityInterface') -> Tuple[float, float]:
        """Get the direction to chase the target."""
        target = self.behavior_component.get_target()
        if not target or not target.basic_component or not entity.basic_component:
            return (0.0, 0.0)
        
        current_pos = entity.basic_component.get_center()
        target_pos = target.basic_component.get_center()
        
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        
        # Normalize direction
        length = math.sqrt(dx**2 + dy**2)
        if length > 0:
            return (dx / length, dy / length)
        return (0.0, 0.0)
    
    def _build_behavior_tree(self) -> None:
        """Build the behavior tree for this enemy."""
        # Interrupt condition: Check if entity should stop current behavior
        def interrupt_condition(entity: 'EntityInterface', current_time: float) -> bool:
            if not entity.combat_component:
                return True
            
            # Check if entity is stunned, frozen, etc.
            if (hasattr(entity.combat_component, 'paralysis') and 
                getattr(entity.combat_component, 'paralysis', False)):
                print("Interrupt: Paralysis")
                return True
            
            if (hasattr(entity.combat_component, 'freeze') and 
                getattr(entity.combat_component, 'freeze', False)):
                print("Interrupt: Freeze")
                return True
            
            if (hasattr(entity.combat_component, 'petrochemical') and 
                getattr(entity.combat_component, 'petrochemical', False)):
                print("Interrupt: Petrochemical")
                return True
            
            return False
        
        # Check if action list has actions
        def action_list_has_actions(entity: 'EntityInterface', current_time: float) -> bool:
            return bool(self.behavior_component.get_action_list())
        
        # Build the behavior tree
        behavior_tree = Selector([
            ConditionNode(
                condition=interrupt_condition,
                on_success=IdleNode()
            ),
            ConditionNode(
                condition=action_list_has_actions,
                on_success=PerformNextAction(self.behavior_component.behavior_tree_component.actions)
            ),
            RefillActionList(self.behavior_component.behavior_tree_component.actions, 
                           self.behavior_component.behavior_tree_component.default_combo),
            IdleNode()
        ])
        
        # Set the behavior tree
        self.behavior_component.set_behavior_tree(behavior_tree)
    
    def update(self, dt: float, current_time: float) -> None:
        """Update the enemy entity."""
        super().update(dt, current_time)
        
        # Custom update logic can be added here
        # For example, check if target is still alive
        target = self.behavior_component.get_target()
        if (target and target.combat_component and
            not target.combat_component.is_alive()):
            self.behavior_component.clear_target()
            print("Target died, clearing target")


class ExampleProjectile(Basic):
    """
    Example projectile entity that demonstrates collision and timing components.
    """
    
    def __init__(self, x: float, y: float, direction: tuple, game: 'Game', 
                 damage: int = 20, element: str = 'untyped', lifetime: float = 5.0):
        # Create a small projectile image
        image = pygame.Surface((8, 8))
        image.fill((255, 255, 0))  # Yellow color
        
        # Initialize the basic entity
        super().__init__(x, y, 8, 8, image, "rectangle", game, "projectile")
        
        # Configure combat properties (projectiles don't have HP)
        self.combat_component.base_max_hp = 1
        self.combat_component.max_hp = 1
        self.combat_component.current_hp = 1
        self.combat_component.can_move = False
        self.combat_component.can_attack = False
        
        # Configure movement properties
        self.movement_component.base_max_speed = 300.0
        self.movement_component.max_speed = 300.0
        self.movement_component.speed = 300.0
        
        # Set initial velocity based on direction
        speed = 300.0
        self.movement_component.velocity = (direction[0] * speed, direction[1] * speed)
        
        # Configure collision properties
        self.collision_component.damage = damage
        self.collision_component.element = element
        self.collision_component.max_penetration_count = 3  # Can hit 3 enemies
        self.collision_component.set_collision_cooldown(0.1)  # 100ms cooldown
        
        # Configure timing
        self.timing_component.set_lifetime(lifetime)
        
        # Configure behavior (simple movement)
        self.behavior_component.set_behavior(BehaviorState.MOVING)
    
    def update(self, dt: float, current_time: float) -> None:
        """Update the projectile."""
        super().update(dt, current_time)
        
        # Move in the direction of velocity
        if self.movement_component:
            dx = self.movement_component.velocity[0] * dt
            dy = self.movement_component.velocity[1] * dt
            self.move(dx, dy, dt)
    
    def on_collision(self, other_entity: 'EntityInterface') -> bool:
        """Handle collision with another entity."""
        if self.collision_component:
            return self.collision_component.handle_collision(other_entity)
        return False


class ExampleBuffEntity(Basic):
    """
    Example entity that demonstrates buff system usage.
    """
    
    def __init__(self, x: float, y: float, game: 'Game'):
        # Create a blue square image
        image = pygame.Surface((24, 24))
        image.fill((0, 0, 255))  # Blue color
        
        # Initialize the basic entity
        super().__init__(x, y, 24, 24, image, "rectangle", game, "buff_entity")
        
        # Configure combat properties
        self.combat_component.base_max_hp = 30
        self.combat_component.max_hp = 30
        self.combat_component.current_hp = 30
        self.combat_component.element = 'water'
        
        # Configure movement properties
        self.movement_component.base_max_speed = 80.0
        self.movement_component.max_speed = 80.0
        self.movement_component.speed = 80.0
        
        # Set up periodic buff application
        self.timing_component.add_periodic(2.0, self._apply_healing_buff)
        self.timing_component.add_periodic(5.0, self._apply_speed_buff)
        
        # Configure behavior
        self.behavior_component.set_behavior(BehaviorState.IDLE)
    
    def _apply_healing_buff(self, entity: 'EntityInterface') -> None:
        """Apply a healing buff to the entity."""
        # This would create and apply a healing buff
        # For demonstration, we'll just heal directly
        if self.combat_component:
            self.combat_component.heal(5)
            print(f"Healed {self.__class__.__name__} for 5 HP")
    
    def _apply_speed_buff(self, entity: 'EntityInterface') -> None:
        """Apply a speed buff to the entity."""
        # This would create and apply a speed buff
        # For demonstration, we'll just increase speed temporarily
        if self.movement_component:
            self.movement_component.set_max_speed(self.movement_component.max_speed * 1.5)
            print(f"Increased speed for {self.__class__.__name__}")
            
            # Reset speed after 3 seconds
            self.timing_component.add_timeout(3.0, self._reset_speed)
    
    def _reset_speed(self, entity: 'EntityInterface') -> None:
        """Reset speed to normal."""
        if self.movement_component:
            self.movement_component.set_max_speed(self.movement_component.base_max_speed)
            print(f"Reset speed for {self.__class__.__name__}")
