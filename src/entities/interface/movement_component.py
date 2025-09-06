"""
Movement Component Interface
Handles movement-related properties like velocity, speed, friction, and movement logic.
"""

from typing import Tuple, Optional
import math
from .entity_interface import ComponentInterface


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
        self.friction_coefficient: float = 0.8  # Friction coefficient (only on ice)
        self.speed: float = 100.0  # Current effective speed
        
        # Physics properties
        self.acceleration: float = 1000.0  # Acceleration rate
        self.deceleration: float = 1000.0  # Deceleration rate
        self.turn_boost: float = 2.0  # Multiplier for acceleration when reversing direction
        
        # State flags
        self.on_ice: bool = False  # Whether entity is on ice surface
    
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
