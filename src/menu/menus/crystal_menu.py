# src/menu/menus/crystal_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from typing import List, Dict
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
class CrystalMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: List[Dict]):
        """Initialize the crystal shop menu with options for stat, amplifier, element, skill library, and back.

        Args:
            game: The main game instance for accessing storage manager and menu management.
        """
        self.title = "Crystal Shop"
        self.game = game
        self.options = options
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                text, pygame.Surface((300, 40)), action,
                pygame.font.SysFont(None, 36)
            ) for i, (text, action) in enumerate([
                ("Stat", "show_stat"),
                ("Amplifier", "show_amplifier"),
                ("Element", "show_element"),
                ("Skill Library", "show_skill_library"),
                ("Back", "back")
            ])
        ]
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.buttons[self.selected_index].is_selected = True
        self._register_menus()
        
    def _register_menus(self):
        # Register dependent menus if not already registered
        if not self.game.menu_manager.menus.get(MenuNavigation.STAT_MENU):
            from src.menu.menus.stat_menu import StatMenu
            self.game.menu_manager.register_menu(MenuNavigation.STAT_MENU, StatMenu(self.game, None))
        if not self.game.menu_manager.menus.get(MenuNavigation.AMPLIFIER_MENU):
            from src.menu.menus.amplifier_menu import AmplifierMenu
            self.game.menu_manager.register_menu(MenuNavigation.AMPLIFIER_MENU, AmplifierMenu(self.game, None))
        if not self.game.menu_manager.menus.get(MenuNavigation.ELEMENT_MENU):
            from src.menu.menus.element_menu import ElementMenu
            self.game.menu_manager.register_menu(MenuNavigation.ELEMENT_MENU, ElementMenu(self.game, None))
        if not self.game.menu_manager.menus.get(MenuNavigation.SKILL_LIBRARY_MENU):
            from src.menu.menus.skill_library_menu import SkillLibraryMenu
            self.game.menu_manager.register_menu(MenuNavigation.SKILL_LIBRARY_MENU, SkillLibraryMenu(self.game, None))

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the crystal menu, including title and buttons."""
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle keyboard and mouse events for showing sub-menus or returning.

        Returns:
            str: The triggered action name.
        """
        if not self.active:
            return ""
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
                    self.game.menu_manager.close_menu(MenuNavigation.CRYSTAL_MENU)
                    return "back"
                elif action == "show_stat":
                    self.game.menu_manager.open_menu(MenuNavigation.STAT_MENU)
                    return action
                elif action == "show_amplifier":
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_MENU)
                    return action
                elif action == "show_element":
                    self.game.menu_manager.open_menu(MenuNavigation.ELEMENT_MENU)
                    return action
                elif action == "show_skill_library":
                    self.game.menu_manager.open_menu(MenuNavigation.SKILL_LIBRARY_MENU)
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back":
                    self.game.menu_manager.close_menu(MenuNavigation.CRYSTAL_MENU)
                    return "back"
                elif action == "show_stat":
                    self.game.menu_manager.open_menu(MenuNavigation.STAT_MENU)
                    return action
                elif action == "show_amplifier":
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_MENU)
                    return action
                elif action == "show_element":
                    self.game.menu_manager.open_menu(MenuNavigation.ELEMENT_MENU)
                    return action
                elif action == "show_skill_library":
                    self.game.menu_manager.open_menu(MenuNavigation.SKILL_LIBRARY_MENU)
                    return action
        return ""

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