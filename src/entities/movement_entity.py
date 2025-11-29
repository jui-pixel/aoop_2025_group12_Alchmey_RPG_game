```python
from src.ecs.components import Velocity, Collider
import math
from .basic_entity import BasicEntity
from src.config import TILE_SIZE, PASSABLE_TILES

class MovementEntity(BasicEntity):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = 32, h: int = 32,
                 image=None, shape="rect", game=None, tag="", 
                 max_speed: float = 100.0, can_move: bool = True, pass_wall: bool = False,
                 init_basic: bool = True):
        if init_basic:
            super().__init__(x, y, w, h, image, shape, game, tag)
            
        self.max_speed = max_speed
        self.can_move = can_move
        self._pass_wall = pass_wall
        self.velocity = (0.0, 0.0)
        self.displacement = (0.0, 0.0)
        
        # ECS Setup
        if self.game and hasattr(self.game, 'ecs_world') and self.ecs_entity is not None:
            if not self.game.ecs_world.has_component(self.ecs_entity, Velocity):
                self.game.ecs_world.add_component(self.ecs_entity, Velocity(x=0.0, y=0.0, speed=max_speed))
            if not self.game.ecs_world.has_component(self.ecs_entity, Collider):
                self.game.ecs_world.add_component(self.ecs_entity, Collider(w=w, h=h, pass_wall=pass_wall))

    @property
    def velocity(self):
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            vel = self.game.ecs_world.component_for_entity(self.ecs_entity, Velocity)
            return (vel.x, vel.y)
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            vel = self.game.ecs_world.component_for_entity(self.ecs_entity, Velocity)
            vel.x = value[0]
            vel.y = value[1]
        self._velocity = value

    def move(self, dx: float, dy: float, dt: float) -> None:
        """Move the entity based on displacement (dx, dy)."""
        # This method is kept for compatibility but should eventually delegate to ECS or be removed.
        # Currently, InputSystem sets velocity, and MovementSystem handles position update.
        # So this method might be redundant if called every frame by legacy code.
        # If legacy code calls this, we should update Velocity component.
        
        if dx != 0 or dy != 0:
            magnitude = math.sqrt(dx**2 + dy**2)
            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude
            self.velocity = (dx * self.max_speed, dy * self.max_speed)
        else:
            # Friction logic handled in MovementSystem or here if we want to keep it hybrid
```python
from src.ecs.components import Velocity, Collider
import math
from .basic_entity import BasicEntity
from src.config import TILE_SIZE, PASSABLE_TILES

class MovementEntity(BasicEntity):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = 32, h: int = 32,
                 image=None, shape="rect", game=None, tag="", 
                 max_speed: float = 100.0, can_move: bool = True, pass_wall: bool = False,
                 init_basic: bool = True):
        if init_basic:
            super().__init__(x, y, w, h, image, shape, game, tag)
            
        self.max_speed = max_speed
        self.can_move = can_move
        self._pass_wall = pass_wall
        self.velocity = (0.0, 0.0)
        self.displacement = (0.0, 0.0)
        
        # ECS Setup
        if self.game and hasattr(self.game, 'ecs_world') and self.ecs_entity is not None:
            if not self.game.ecs_world.has_component(self.ecs_entity, Velocity):
                self.game.ecs_world.add_component(self.ecs_entity, Velocity(x=0.0, y=0.0, speed=max_speed))
            if not self.game.ecs_world.has_component(self.ecs_entity, Collider):
                self.game.ecs_world.add_component(self.ecs_entity, Collider(w=w, h=h, pass_wall=pass_wall))

    @property
    def velocity(self):
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            vel = self.game.ecs_world.component_for_entity(self.ecs_entity, Velocity)
            return (vel.x, vel.y)
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            vel = self.game.ecs_world.component_for_entity(self.ecs_entity, Velocity)
            vel.x = value[0]
            vel.y = value[1]
        self._velocity = value

    def move(self, dx: float, dy: float, dt: float) -> None:
        """Move the entity based on displacement (dx, dy)."""
        # This method is kept for compatibility but should eventually delegate to ECS or be removed.
        # Currently, InputSystem sets velocity, and MovementSystem handles position update.
        # So this method might be redundant if called every frame by legacy code.
        # If legacy code calls this, we should update Velocity component.
        
        if dx != 0 or dy != 0:
            magnitude = math.sqrt(dx**2 + dy**2)
            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude
            self.velocity = (dx * self.max_speed, dy * self.max_speed)
        else:
            # Friction logic handled in MovementSystem or here if we want to keep it hybrid
            pass
        
        # We DO NOT update position here anymore to avoid double movement.
        # MovementSystem will handle it.
        pass

    def update(self, dt: float, current_time: float) -> None:
        """Update movement entity position based on velocity."""
        # Logic moved to MovementSystem
        pass
```