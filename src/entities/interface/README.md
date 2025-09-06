# Entity Interface System

This module implements a comprehensive entity interface system based on the draw.io diagram specifications. The system uses a component-based architecture where each entity is composed of multiple specialized components.

## Architecture Overview

The interface system consists of:

1. **EntityInterface** - Base interface for all entities
2. **ComponentInterface** - Base interface for all components
3. **Basic** - Basic entity implementation using all components
4. **Various Components** - Specialized components for different aspects of entities

## Components

### BasicComponent
Handles fundamental entity properties:
- ID: Unique identifier
- Position: (x, y) coordinates
- Size: (width, height) dimensions
- Image: Visual representation
- Shape: Collision shape type
- Game: Reference to game instance

### CombatComponent
Manages combat-related properties:
- HP system (current HP, max HP, base max HP)
- Shield system (current shield, max shield)
- Elemental resistances
- Combat flags (can move, can attack, invulnerable, dodge rate)
- Damage calculation

### MovementComponent
Handles movement mechanics:
- Velocity and displacement
- Speed (base and current)
- Friction coefficient (only on ice)
- Movement logic and physics
- Acceleration and deceleration

### BuffComponent
Manages buffs and effects:
- Buff management (add, remove, update)
- Modifier calculation
- Effect application
- Buff synthesis
- Periodic effects

### CollisionComponent
Handles collision detection and response:
- Collision detection and response
- Penetration mechanics
- Explosion mechanics
- Collision cooldown and tracking

### BehaviorComponent
Manages AI behavior using behavior tree system:
- Behavior tree execution
- Action management
- State transitions (legacy compatibility)
- Target tracking
- Action list management

### TimingComponent
Handles time-based functionality:
- Lifetime management
- Timeout handling
- Periodic updates
- Time-based effects

### BehaviorTreeComponent
Handles behavior tree execution:
- Action execution and management
- Behavior tree node processing
- Action list management
- Custom behavior tree support

### DamageCalculator
Utility class for damage calculation:
- Elemental affinity calculation
- Resistance application
- Shield mechanics
- Dodge calculation

## Usage Examples

### Creating a Basic Entity

```python
import pygame
from src.entities.interface import Basic

# Create a simple entity
image = pygame.Surface((32, 32))
image.fill((255, 0, 0))  # Red square

entity = Basic(x=100, y=100, w=32, h=32, image=image, 
               shape="rectangle", game=game_instance, tag="enemy")

# Configure properties
entity.combat_component.base_max_hp = 100
entity.movement_component.base_max_speed = 150.0
entity.collision_component.damage = 20
```

### Creating an Enemy with Behavior Tree AI

```python
from src.entities.interface.example_entity import ExampleEnemy
from src.entities.interface.behavior_tree import ChaseAction, AttackAction, WaitAction

# Create enemy with target
enemy = ExampleEnemy(x=200, y=200, game=game_instance, target=player)

# The enemy will automatically use behavior tree AI
# You can add custom actions
enemy.behavior_component.add_action('custom_attack', AttackAction('custom_attack', damage=15))

# You can change behavior (legacy compatibility)
enemy.set_behavior(BehaviorState.FLEEING)
```

### Creating Custom Behavior Trees

```python
from src.entities.interface.behavior_tree import (Selector, ConditionNode, 
                                                  PerformNextAction, IdleNode)

# Create custom behavior tree
def custom_condition(entity, current_time):
    return entity.combat_component.health < 50

custom_tree = Selector([
    ConditionNode(
        condition=custom_condition,
        on_success=IdleNode()  # Flee when low health
    ),
    PerformNextAction(actions),  # Normal behavior
    IdleNode()
])

# Set custom behavior tree
entity.behavior_component.set_behavior_tree(custom_tree)
```

### Creating a Projectile

```python
from src.entities.interface.example_entity import ExampleProjectile

# Create projectile moving right
projectile = ExampleProjectile(x=100, y=100, direction=(1, 0), 
                              game=game_instance, damage=25, element='fire')
```

### Adding Buffs

```python
# Add a speed buff
entity.add_buff(speed_buff)

# Add a healing buff
entity.add_buff(healing_buff)

# Check active buffs
active_buffs = entity.buff_component.get_active_buffs()
```

### Setting Entity Lifetime

```python
# Set entity to live for 10 seconds
entity.set_lifetime(10.0)

# Check remaining lifetime
remaining = entity.timing_component.get_remaining_lifetime()
```

## Component Interaction

Components work together to provide full entity functionality:

1. **BasicComponent** provides fundamental properties
2. **CombatComponent** handles health and damage
3. **MovementComponent** manages movement and physics
4. **BuffComponent** applies and manages effects
5. **CollisionComponent** handles interactions
6. **BehaviorComponent** controls AI and state
7. **TimingComponent** manages time-based events

## Damage Calculation

The system implements the damage calculation logic from the draw.io diagram:

1. Check for dodge (combat attributes -> dodge rate%)
2. Calculate damage = original_damage * (elemental_affinity?) * elemental_resistance
3. If shield exists, deduct from shield first
4. If shield <= 0, remaining damage is lost
5. If no shield, apply damage directly to HP

## Elemental System

The system supports elemental affinities and resistances:

- **Light vs Dark**: 1.5x damage
- **Elemental Cycle**: Metal > Wood > Earth > Water > Fire > Metal (1.5x damage)
- **Special Affinities**: Earth vs Electric, Wood vs Wind, Fire vs Ice (1.5x damage)

## Best Practices

1. **Always initialize components** after creating an entity
2. **Use the component system** instead of direct property access when possible
3. **Handle component dependencies** (e.g., movement requires combat component for can_move)
4. **Use the damage calculator** for consistent damage calculation
5. **Implement proper cleanup** in destroy callbacks
6. **Use behavior states** for complex AI logic
7. **Leverage the timing system** for time-based effects

## Integration with Existing Code

To integrate with existing entity classes:

1. Inherit from `Basic` instead of `pygame.sprite.Sprite`
2. Use component properties instead of direct attributes
3. Update the `update()` method to call `super().update()`
4. Use the component system for new functionality

## Performance Considerations

- Components are lightweight and only update when necessary
- Buff calculations are cached and only recalculated when buffs change
- Collision detection uses pygame's built-in rect collision
- Behavior states prevent unnecessary calculations

## Future Extensions

The system is designed to be extensible:

- Add new component types by inheriting from `ComponentInterface`
- Extend behavior states for more complex AI
- Add new damage calculation methods
- Implement more sophisticated buff synthesis rules
