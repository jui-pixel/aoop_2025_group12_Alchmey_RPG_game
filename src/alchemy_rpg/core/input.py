import pygame
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class InputContext:
    active_context: str = "playing"  # 'playing', 'menu', 'lobby'

class InputManager:
    """
    Handles raw Pygame inputs and maps them to logical game actions.
    """
    def __init__(self):
        self.context = InputContext()
        # Key mappings could be loaded from config
        self.key_bindings = {
            "move_up": pygame.K_w,
            "move_down": pygame.K_s,
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "interact": pygame.K_e,
            "pause": pygame.K_ESCAPE,
            "skill_1": pygame.K_1,
            "skill_2": pygame.K_2,
            "skill_3": pygame.K_3,
            "skill_4": pygame.K_4,
        }
        self.mouse_position = (0, 0)
        self.mouse_buttons = {1: False, 2: False, 3: False}

    def process_events(self, events: List[pygame.event.Event]) -> List[str]:
        """
        Process a list of Pygame events and return a list of logical actions.
        """
        actions = []
        self.mouse_position = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                action = self._map_key_to_action(event.key)
                if action:
                    actions.append(action)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_buttons[event.button] = True
                actions.append(f"mouse_click_{event.button}")
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_buttons[event.button] = False
                
        return actions

    def _map_key_to_action(self, key_code: int) -> Optional[str]:
        for action, key in self.key_bindings.items():
            if key == key_code:
                return action
        return None

    def get_axis(self) -> tuple[float, float]:
        """Returns (dx, dy) based on held keys for movement."""
        dx, dy = 0.0, 0.0
        keys = pygame.key.get_pressed()
        if keys[self.key_bindings["move_up"]]:
            dy -= 1
        if keys[self.key_bindings["move_down"]]:
            dy += 1
        if keys[self.key_bindings["move_left"]]:
            dx -= 1
        if keys[self.key_bindings["move_right"]]:
            dx += 1
        return dx, dy
