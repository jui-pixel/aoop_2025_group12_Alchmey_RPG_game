"""
Entity Interface System
Based on the draw.io diagram, this module defines the core entity interface and its components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import pygame


class EntityInterface(ABC):
    """
    Main entity interface that defines the core structure for all game entities.
    This is the central hub that coordinates all component interfaces.
    """
    
    def __init__(self, entity_id: int, x: float, y: float, w: int, h: int, 
                 image: pygame.Surface, shape: str, game: 'Game', tag: str = ""):
        self.id = entity_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = image
        self.shape = shape
        self.game = game
        self.tag = tag
        
        # Component references
        self.basic_component: Optional['BasicComponent'] = None
        self.combat_component: Optional['CombatComponent'] = None
        self.movement_component: Optional['MovementComponent'] = None
        self.buff_component: Optional['BuffComponent'] = None
        self.collision_component: Optional['CollisionComponent'] = None
        self.behavior_component: Optional['BehaviorComponent'] = None
        self.timing_component: Optional['TimingComponent'] = None
    
    @abstractmethod
    def init(self) -> None:
        """Initialize the entity and all its components."""
        pass
    
    @abstractmethod
    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw the entity on the screen."""
        pass
    
    @abstractmethod
    def update(self, dt: float, current_time: float) -> None:
        """Update the entity and all its components."""
        pass


class ComponentInterface(ABC):
    """Base interface for all entity components."""
    
    def __init__(self, entity: EntityInterface):
        self.entity = entity
    
    @abstractmethod
    def init(self) -> None:
        """Initialize the component."""
        pass
    
    @abstractmethod
    def update(self, dt: float, current_time: float) -> None:
        """Update the component."""
        pass
