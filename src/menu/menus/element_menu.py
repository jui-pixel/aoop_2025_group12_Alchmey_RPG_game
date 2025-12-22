# src/menu/menus/element_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Dict, Tuple
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
class ElementMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: List[Dict]):
        """Initialize the element awakening menu.

        Args:
            game: The main game instance for accessing storage manager and menu management.
        """
        self.title = "Element Awakening"
        self.game = game
        self.elements = ["untyped", "metal", "wood", "water", "fire", "earth", "light", "dark", "wind", "thunder", "ice"]
        self.awaken_cost = 1  # Cost in mana to awaken each element
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                element.capitalize(),
                pygame.Surface((300, 40)), f"awaken_{element}",
                pygame.font.SysFont(None, 36)
            ) for i, element in enumerate(self.elements)
        ]
        self.buttons.append(
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + len(self.elements) * 50, 300, 40,
                "Back", pygame.Surface((300, 40)), "back",
                pygame.font.SysFont(None, 36)
            )
        )
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.message_font = pygame.font.SysFont(None, 36)
        self.message = None
        self.buttons[self.selected_index].is_selected = True

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the element menu, using gold background for awakened elements and gray for unawakened."""
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        awakened_elements = self.game.storage_manager.awakened_elements
        for button in self.buttons:
            if button.action != "back" and button.action.startswith("awaken_"):
                element = button.action.split("_")[1]
                if element in awakened_elements:
                    button.image.fill((255, 215, 0))  # Gold background for awakened
                else:
                    button.image.fill((50, 50, 50))  # Dark gray background for unawakened
            button.draw(screen)
        if self.message:
            msg_surface = self.message_font.render(self.message, True, (255, 0, 0))
            screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT - 100))

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle keyboard and mouse events for awakening elements or returning.

        Returns:
            str: The triggered action name.
        """
        if not self.active:
            return ""
        if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
            self.message = None
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.buttons[self.selected_index].is_selected = False
                    self.selected_index = i
                    self.buttons[self.selected_index].is_selected = True
                    break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_RETURN:
                action = self.buttons[self.selected_index].action
                if action == "back":
                    self.game.menu_manager.close_menu(MenuNavigation.ELEMENT_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
                    return BasicAction.EXIT_MENU
                elif action.startswith("awaken_"):
                    element = action.split("_")[1]
                    success, reason = self._awaken_element(element)
                    if success:
                        print(f"ElementMenu: Awakened {element} successfully")
                    else:
                        self.message = reason
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back":
                    self.game.menu_manager.close_menu(MenuNavigation.ELEMENT_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
                    return BasicAction.EXIT_MENU
                elif action.startswith("awaken_"):
                    element = action.split("_")[1]
                    success, reason = self._awaken_element(element)
                    if success:
                        print(f"ElementMenu: Awakened {element} successfully")
                    else:
                        self.message = reason
                    return action
        return ""

    def _awaken_element(self, element: str) -> Tuple[bool, str]:
        """Awaken the specified element, checking mana and awakening status.

        Args:
            element: The element to awaken.

        Returns:
            Tuple[bool, str]: (Success, Reason message).
        """
        return self.game.storage_manager.awaken_element(element, cost=self.awaken_cost)

    def get_selected_action(self) -> str:
        """Get the currently selected button action.

        Returns:
            str: The current selected action name.
        """
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        """Activate or deactivate the menu.

        Args:
            active: Whether to activate the menu.
        """
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False
            self.message = None