"""
Basic Component Interface
Handles fundamental entity properties like ID, position, size, image, and shape.
"""

from typing import Tuple, Optional, TYPE_CHECKING
import pygame
from .entity_interface import ComponentInterface

if TYPE_CHECKING:
    from .entity_interface import EntityInterface


class BasicComponent(ComponentInterface):
    """
    Basic component that handles fundamental entity properties:
    - ID: Unique identifier
    - Position: (x, y) coordinates
    - Size: (width, height) dimensions
    - Image: Visual representation
    - Shape: Collision shape type
    - Game: Reference to game instance
    """
    
    def __init__(self, entity: 'EntityInterface'):
        super().__init__(entity)
        self.id: int = 0
        self.position: Tuple[float, float] = (0.0, 0.0)
        self.size: Tuple[int, int] = (0, 0)
        self.image: Optional[pygame.Surface] = None
        self.shape: str = "rectangle"
        self.game: Optional[object] = None
        self.dungeon: Optional[object] = None
    
    def init(self) -> None:
        """Initialize basic component properties."""
        self.id = id(self.entity)
        self.position = (self.entity.x, self.entity.y)
        self.size = (self.entity.w, self.entity.h)
        self.image = self.entity.image
        self.shape = self.entity.shape
        self.game = self.entity.game
        self.dungeon = self.entity.game.dungeon_manager.get_dungeon()
    
    def update(self, dt: float, current_time: float) -> None:
        """Update basic component (position synchronization)."""
        self.position = (self.entity.x, self.entity.y)
    
    def get_rect(self) -> pygame.Rect:
        """Get the entity's rectangle for collision detection."""
        return pygame.Rect(self.position[0] - self.size[0] // 2, 
                          self.position[1] - self.size[1] // 2, 
                          self.size[0], self.size[1])
    
    def set_position(self, x: float, y: float) -> None:
        """Set the entity's position."""
        self.entity.x = x
        self.entity.y = y
        self.position = (x, y)
    
    def get_center(self) -> Tuple[float, float]:
        """Get the center position of the entity."""
        return (self.position[0], self.position[1])
