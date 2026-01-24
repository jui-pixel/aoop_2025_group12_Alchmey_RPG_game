from abc import ABC, abstractmethod
import pygame
from typing import Optional, Any

class AbstractMenu(ABC):
    """
    Base class for all menus.
    """
    def __init__(self, engine=None):
        self.engine = engine
        self.is_visible = True
        
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input event, return action string if any."""
        pass
    
    @abstractmethod
    def update(self, dt: float):
        """Update menu state."""
        pass
    
    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """Render the menu."""
        pass
    
    def set_data(self, data: Any):
        """Set data for the menu (for initialization or refresh)."""
        pass
    
    def on_open(self):
        """Called when menu is opened."""
        pass
    
    def on_close(self):
        """Called when menu is closed."""
        pass
