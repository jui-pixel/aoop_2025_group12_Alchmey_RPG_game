from typing import Dict, List, Optional, Any
import pygame

class MenuManager:
    """
    Manages the menu stack for the UI system.
    """
    def __init__(self, engine=None):
        self.engine = engine
        self.menus: Dict[str, Any] = {}  # Registered menu instances
        self.active_menus: List[Any] = []  # Stack of active menus
        
    def register_menu(self, name: str, menu_instance: Any):
        """Register a menu by name."""
        self.menus[name] = menu_instance
        
    def open_menu(self, name: str, data: Any = None):
        """Open a menu and push it onto the stack."""
        if name in self.menus:
            menu = self.menus[name]
            if menu is None:
                # Lazy init placeholder
                print(f"MenuManager: Menu '{name}' needs lazy initialization")
                return
            if data and hasattr(menu, 'set_data'):
                menu.set_data(data)
            self.active_menus.append(menu)
            print(f"MenuManager: Opened '{name}', stack size: {len(self.active_menus)}")
        else:
            print(f"MenuManager: Menu '{name}' not registered")
    
    def close_menu(self, menu=None):
        """Close the top menu or a specific menu."""
        if menu and menu in self.active_menus:
            self.active_menus.remove(menu)
        elif self.active_menus:
            self.active_menus.pop()
            
    def close_all_menus(self):
        """Close all active menus."""
        self.active_menus.clear()
        
    def set_menu(self, menu):
        """Set a single active menu (clears stack)."""
        self.active_menus = [menu] if menu else []
        
    def get_current_menu(self) -> Optional[Any]:
        """Get the topmost active menu."""
        return self.active_menus[-1] if self.active_menus else None
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Pass event to topmost menu."""
        current = self.get_current_menu()
        if current and hasattr(current, 'handle_event'):
            return current.handle_event(event)
        return None
    
    def update_current_menus(self, dt: float):
        """Update all active menus."""
        for menu in self.active_menus:
            if hasattr(menu, 'update'):
                menu.update(dt)
                
    def draw(self, screen: pygame.Surface):
        """Draw all active menus in order."""
        for menu in self.active_menus:
            if hasattr(menu, 'draw'):
                menu.draw(screen)
