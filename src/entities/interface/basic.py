"""
Basic Entity Implementation
This module provides a basic implementation of the EntityInterface for simple entities.
"""

import pygame
from typing import List, Optional, TYPE_CHECKING
from .entity_interface import EntityInterface

if TYPE_CHECKING:
    from src.game import Game
from .basic_component import BasicComponent
from .combat_component import CombatComponent
from .movement_component import MovementComponent
from .buff_component import BuffComponent
from .collision_component import CollisionComponent
from .behavior_component import BehaviorComponent
from .timing_component import TimingComponent


class Basic(EntityInterface, pygame.sprite.Sprite):
    """
    Basic entity implementation that uses the component-based interface system.
    This serves as a foundation for all game entities.
    """
    
    def __init__(self, x: float, y: float, w: int, h: int, image: pygame.Surface, 
                 shape: str, game: 'Game', tag: str = ""):
        # Initialize pygame sprite
        pygame.sprite.Sprite.__init__(self)
        
        # Initialize entity interface
        super().__init__(id(self), x, y, w, h, image, shape, game, tag)
        
        # Create and initialize components
        self.basic_component = BasicComponent(self)
        self.combat_component = CombatComponent(self)
        self.movement_component = MovementComponent(self)
        self.buff_component = BuffComponent(self)
        self.collision_component = CollisionComponent(self)
        self.behavior_component = BehaviorComponent(self)
        self.timing_component = TimingComponent(self)
        
        # Initialize all components
        self.init()
    
    def init(self) -> None:
        """Initialize the entity and all its components."""
        self.basic_component.init()
        self.combat_component.init()
        self.movement_component.init()
        self.buff_component.init()
        self.collision_component.init()
        self.behavior_component.init()
        self.timing_component.init()
        
        # Set up pygame sprite properties
        self.rect = self.basic_component.get_rect()
        self.image = self.basic_component.image
    
    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw the entity on the screen."""
        if not self.basic_component or not self.basic_component.image:
            return
        
        # Calculate screen position with camera offset
        screen_x = self.basic_component.position[0] + camera_offset[0] - self.basic_component.size[0] // 2
        screen_y = self.basic_component.position[1] + camera_offset[1] - self.basic_component.size[1] // 2
        
        # Draw the entity
        screen.blit(self.basic_component.image, (screen_x, screen_y))
        
        # Draw health bar if entity has combat component
        if self.combat_component and self.combat_component.is_alive():
            self._draw_health_bar(screen, camera_offset)
    
    def update(self, dt: float, current_time: float) -> None:
        """Update the entity and all its components."""
        # Update all components
        self.basic_component.update(dt, current_time)
        self.combat_component.update(dt, current_time)
        self.movement_component.update(dt, current_time)
        self.buff_component.update(dt, current_time)
        self.collision_component.update(dt, current_time)
        self.behavior_component.update(dt, current_time)
        self.timing_component.update(dt, current_time)
        
        # Update pygame sprite rect
        if self.basic_component:
            self.rect = self.basic_component.get_rect()
        
        # Check if entity should be destroyed
        if self.timing_component and self.timing_component.is_expired():
            self.kill()
    
    def _draw_health_bar(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw a health bar above the entity."""
        if not self.combat_component or not self.basic_component:
            return
        
        # Health bar dimensions
        bar_width = self.basic_component.size[0]
        bar_height = 5
        
        # Calculate position
        screen_x = self.basic_component.position[0] + camera_offset[0] - bar_width // 2
        screen_y = self.basic_component.position[1] + camera_offset[1] - self.basic_component.size[1] // 2 - 10
        
        # Background (red)
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y, bar_width, bar_height))
        
        # Foreground (green), scaled by health percentage
        health_ratio = self.combat_component.get_health_percentage()
        health_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y, health_width, bar_height))
    
    def move(self, dx: float, dy: float, dt: float) -> None:
        """Move the entity using the movement component."""
        if self.movement_component:
            self.movement_component.move(dx, dy, dt)
    
    def take_damage(self, damage: int, element: str) -> tuple:
        """Take damage using the combat component."""
        if self.combat_component:
            return self.combat_component.take_damage(damage, element)
        return False, 0
    
    def add_buff(self, buff) -> None:
        """Add a buff using the buff component."""
        if self.buff_component:
            self.buff_component.add_buff(buff)
    
    def set_behavior(self, behavior_state) -> None:
        """Set behavior state using the behavior component."""
        if self.behavior_component:
            self.behavior_component.set_behavior(behavior_state)
    
    def set_lifetime(self, lifetime: float) -> None:
        """Set entity lifetime using the timing component."""
        if self.timing_component:
            self.timing_component.set_lifetime(lifetime)
