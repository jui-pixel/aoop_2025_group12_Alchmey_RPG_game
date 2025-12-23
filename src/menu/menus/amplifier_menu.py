# src/menu/menus/amplifier_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from typing import List, Dict
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
class AmplifierMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: List[Dict]):
        """Initialize the amplifier selection menu with options for magic missile, shield, step, and back.

        Args:
            game: The main game instance for accessing storage manager and menu management.
        """
        self.title = "Amplifier Selection"
        self.game = game
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                text, pygame.Surface((300, 40)), action,
                pygame.font.SysFont(None, 36)
            ) for i, (text, action) in enumerate([
                ("Magic Missile", "show_magic_missile"),
                ("Magic Shield", "show_magic_shield"),
                ("Magic Step", "show_magic_step"),
                ("Back", "crystal_menu")
            ])
        ]
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.buttons[self.selected_index].is_selected = True
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the amplifier menu, including title and buttons."""
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
                if action == "crystal_menu":
                    self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
                    return BasicAction.EXIT_MENU
                elif action.startswith("show_"):
                    amplifier_type = action.split("_")[1] + "_" + action.split("_")[2]
                    if self.game.menu_manager.menus['amplifier_stat_menu'] is not None:
                        self.game.menu_manager.menus['amplifier_stat_menu'].update_type(amplifier_type)
                    data = {'type': amplifier_type}
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_STAT_MENU)
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "crystal_menu":
                    self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
                    return BasicAction.EXIT_MENU
                elif action.startswith("show_"):
                    amplifier_type = action.split("_")[1] + "_" + action.split("_")[2]
                    if self.game.menu_manager.menus['amplifier_stat_menu'] is not None:
                        self.game.menu_manager.menus['amplifier_stat_menu'].update_type(amplifier_type)
                    data = {'type': amplifier_type}
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_STAT_MENU)
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