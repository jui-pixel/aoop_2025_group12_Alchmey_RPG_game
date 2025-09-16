from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from typing import List, Dict
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

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
                ("Back", "back_to_lobby")
            ])
        ]
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.buttons[self.selected_index].is_selected = True

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
                if action == "back_to_lobby":
                    self.game.hide_menu('crystal_menu')
                    return "back_to_lobby"
                elif action == "show_stat":
                    self.game.show_menu('stat_menu')
                    return action
                elif action == "show_amplifier":
                    self.game.show_menu('amplifier_menu')
                    return action
                elif action == "show_element":
                    self.game.show_menu('element_menu')
                    return action
                elif action == "show_skill_library":
                    self.game.show_menu('skill_library_menu')
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back_to_lobby":
                    self.game.hide_menu('crystal_menu')
                    return "back_to_lobby"
                elif action == "show_stat":
                    self.game.show_menu('stat_menu')
                    return action
                elif action == "show_amplifier":
                    self.game.show_menu('amplifier_menu')
                    return action
                elif action == "show_element":
                    self.game.show_menu('element_menu')
                    return action
                elif action == "show_skill_library":
                    self.game.show_menu('skill_library_menu')
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