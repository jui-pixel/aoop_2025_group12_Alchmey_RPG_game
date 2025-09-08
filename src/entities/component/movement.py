"""
Movement Component Interface
Handles movement-related properties like velocity, speed, friction, and movement logic.
"""

from typing import Tuple, Optional
import math
from .entity_interface import ComponentInterface
from config import TILE_SIZE, PASSABLE_TILES

class MovementComponent(ComponentInterface):
    """
    Movement component that handles all movement-related properties:
    - Velocity and displacement
    - Speed (base and current)
    - Friction coefficient
    - Movement logic and physics
    """
    
    def __init__(self, entity: 'EntityInterface'):
        super().__init__(entity)
        # Movement properties
        self.displacement: Tuple[float, float] = (0.0, 0.0)  # (dx, dy)
        self.velocity: Tuple[float, float] = (0.0, 0.0)  # Current velocity
        self.base_max_speed: float = 100.0  # Base maximum speed
        self.max_speed: float = 100.0  # Current maximum speed (after buffs)
        self.speed: float = 100.0  # Current effective speed
        
        # Physics properties
        self.acceleration: float = 1000.0  # Acceleration rate
        self.deceleration: float = 1000.0  # Deceleration rate
        self.turn_boost: float = 2.0  # Multiplier for acceleration when reversing direction
        
        # State flags
        self.pass_wall: bool = False
    
    def init(self) -> None:
        """Initialize movement component with default values."""
        self.max_speed = self.base_max_speed
        self.speed = self.base_max_speed
    
    def update(self, dt: float, current_time: float) -> None:
        """Update movement component (apply physics, friction, etc.)."""
        # Apply friction if on ice
        if self.on_ice and self.friction_coefficient < 1.0:
            self.velocity = (
                self.velocity[0] * self.friction_coefficient,
                self.velocity[1] * self.friction_coefficient
            )
        
        # Apply deceleration when no input
        if self.displacement == (0.0, 0.0):
            vel_length = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
            if vel_length > 0:
                new_vel_length = max(0, vel_length - self.deceleration * dt)
                if new_vel_length > 0:
                    self.velocity = (
                        self.velocity[0] * new_vel_length / vel_length,
                        self.velocity[1] * new_vel_length / vel_length
                    )
                else:
                    self.velocity = (0.0, 0.0)
    
    def move(self, dx: float, dy: float, dt: float) -> None:
        """
        Move the entity with acceleration-based movement.
        Args:
            dx, dy: Input direction (normalized or not)
            dt: Delta time
        """
        if not self.entity.combat_component or not self.entity.combat_component.can_move:
            self.velocity = (0.0, 0.0)
            return
        
        # Normalize input
        length = math.sqrt(dx**2 + dy**2)
        if length == 0:
            self.displacement = (0.0, 0.0)
            return
        
        dx, dy = dx / length, dy / length
        self.displacement = (dx, dy)
        
        # Calculate acceleration
        vel_length = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
        if vel_length > 0:
            # Check if reversing direction
            input_dir = (dx, dy)
            vel_dir = (self.velocity[0] / vel_length, self.velocity[1] / vel_length)
            dot_product = input_dir[0] * vel_dir[0] + input_dir[1] * vel_dir[1]
            
            # If reversing direction (angle > 120 degrees), apply turn boost
            if dot_product < -0.5:
                self.velocity = (
                    self.velocity[0] * 0.5,  # Reduce current velocity
                    self.velocity[1] * 0.5
                )
                accel = self.acceleration * self.turn_boost
            else:
                accel = self.acceleration
        else:
            accel = self.acceleration
        
        # Apply acceleration
        self.velocity = (
            self.velocity[0] + dx * accel * dt,
            self.velocity[1] + dy * accel * dt
        )
        
        # Limit speed
        vel_length = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
        if vel_length > self.max_speed:
            self.velocity = (
                self.velocity[0] * self.max_speed / vel_length,
                self.velocity[1] * self.max_speed / vel_length
            )
        
        # Update entity position
        if self.entity.basic_component:
            new_x = self.entity.x + self.velocity[0] * dt
            new_y = self.entity.y + self.velocity[1] * dt
            if not self.pass_wall:
                tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
                if 0 <= tile_x < self.dungeon.grid_width and 0 <= tile_y < self.dungeon.grid_height:
                    tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile in PASSABLE_TILES:
                    self.pos = [new_x, new_y]
                    self.rect.center = self.pos
                else:
                    # 嘗試沿X或Y軸滑動
                    y_allowed = 0 <= int(new_y // TILE_SIZE) < self.dungeon.grid_height and \
                                self.dungeon.dungeon_tiles[int(new_y // TILE_SIZE)][int(self.pos[0] // TILE_SIZE)] in PASSABLE_TILES
                    x_allowed = 0 <= int(new_x // TILE_SIZE) < self.dungeon.grid_width and \
                                self.dungeon.dungeon_tiles[int(self.pos[1] // TILE_SIZE)][int(new_x // TILE_SIZE)] in PASSABLE_TILES

                    if y_allowed:
                        self.pos[1] = new_y
                        self.rect.centery = new_y
                        self.velocity[1] *= max(0, 1 - self.deceleration * dt / self.speed)
                    if x_allowed:
                        self.pos[0] = new_x
                        self.rect.centerx = new_x
                        self.velocity[0] *= max(0, 1 - self.deceleration * dt / self.speed)
                    if not (x_allowed or y_allowed):
                        self.velocity = [self.velocity[0] * max(0, 1 - self.deceleration * dt / self.speed),
                                        self.velocity[1] * max(0, 1 - self.deceleration * dt / self.speed)]
            else:
                self.entity.basic_component.set_position(new_x, new_y)
    
    def set_max_speed(self, new_speed: float) -> None:
        """Set new maximum speed."""
        self.max_speed = new_speed
        self.speed = new_speed
    
    def set_base_max_speed(self, new_base_speed: float) -> None:
        """Set new base maximum speed."""
        self.base_max_speed = new_base_speed
        self.max_speed = new_base_speed
        self.speed = new_base_speed
    
    def set_friction_coefficient(self, friction: float) -> None:
        """Set friction coefficient (only applies on ice)."""
        self.friction_coefficient = max(0.0, min(1.0, friction))
    
    def set_on_ice(self, on_ice: bool) -> None:
        """Set whether the entity is on ice surface."""
        self.on_ice = on_ice
    
    def set_pass_wall(self, pass_wall: bool) -> None:
        """Set whether the entity won't blocked by wall."""
        self.pass_wall = pass_wall
    
    def get_speed(self) -> float:
        """Get current effective speed."""
        return math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
    
    def stop(self) -> None:
        """Stop the entity immediately."""
        self.velocity = (0.0, 0.0)
        self.displacement = (0.0, 0.0)
    
    def add_velocity(self, dx: float, dy: float) -> None:
        """Add velocity to the current velocity."""
        self.velocity = (self.velocity[0] + dx, self.velocity[1] + dy)
        
        # Limit speed
        vel_length = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
        if vel_length > self.max_speed:
            self.velocity = (
                self.velocity[0] * self.max_speed / vel_length,
                self.velocity[1] * self.max_speed / vel_length
            )
