# src/menu/menus/skill_library_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from math import ceil
from typing import List, Dict, Tuple
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
class SkillLibraryMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: List[Dict]):
        """Initialize the skill library menu, displaying 8 skills per page with navigation buttons.

        Args:
            game: The main game instance for accessing skill data and menu management.
        """
        self.title = "Skill Library"
        self.game = game
        self.skills_per_page = 8
        self.current_page = 0
        self.skills = self.game.storage_manager.skills_library if self.game.storage_manager.skills_library else []
        self.total_pages = ceil(len(self.skills) / self.skills_per_page)
        self.buttons = []
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.message_font = pygame.font.SysFont(None, 36)
        self.selected_description = None
        self._update_buttons()

    def _update_buttons(self):
        """Update the button list for the current page, showing skills and navigation buttons."""
        self.buttons = []
        start_idx = self.current_page * self.skills_per_page
        end_idx = min(start_idx + self.skills_per_page, len(self.skills))
        for i, idx in enumerate(range(start_idx, end_idx)):
            skill = self.skills[idx]
            button_text = f"{skill['name']}"
            self.buttons.append(
                Button(
                    SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                    button_text,
                    pygame.Surface((300, 40)), f"skill_{idx}",
                    pygame.font.SysFont(None, 36)
                )
            )
        # Fill empty slots
        for i in range(end_idx - start_idx, self.skills_per_page):
            self.buttons.append(
                Button(
                    SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                    "Empty",
                    pygame.Surface((300, 40)), f"empty_{i}",
                    pygame.font.SysFont(None, 36)
                )
            )
        # Add navigation and back buttons
        y_offset = 100 + self.skills_per_page * 50
        if self.current_page > 0:
            self.buttons.append(
                Button(
                    SCREEN_WIDTH // 2 - 310, y_offset, 150, 40,
                    "Previous", pygame.Surface((150, 40)), "previous",
                    pygame.font.SysFont(None, 36)
                )
            )
        if self.current_page < self.total_pages - 1:
            self.buttons.append(
                Button(
                    SCREEN_WIDTH // 2 + 10, y_offset, 150, 40,
                    "Next", pygame.Surface((150, 40)), "next",
                    pygame.font.SysFont(None, 36)
                )
            )
        self.buttons.append(
            Button(
                SCREEN_WIDTH // 2 - 150, y_offset + (50 if self.current_page == 0 and self.current_page == self.total_pages - 1 else 0), 300, 40,
                "Back", pygame.Surface((300, 40)), "crystal_menu",
                pygame.font.SysFont(None, 36)
            )
        )
        self.selected_index = min(self.selected_index, len(self.buttons) - 1)
        self.buttons[self.selected_index].is_selected = True

    def _get_skill_description(self, skill: Dict) -> str:
        """Generate a description string for the skill.

        Args:
            skill: The skill dictionary.

        Returns:
            str: A formatted description of the skill's attributes.
        """
        desc = f"Name: {skill.get('name', 'Unknown')}\n"
        desc += f"Type: {skill.get('type', 'Unknown')}\n"
        if 'sub_type' in skill:
            desc += f"Sub Type: {skill.get('sub_type', 'None')}\n"
        desc += f"Element: {skill.get('element', 'Untyped')}\n"
        params = skill.get('params', {})
        if params:
            desc += "Parameters:\n"
            for key, value in params.items():
                desc += f"  {key.capitalize()}: {value}\n"
        return desc

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the skill library menu, showing the current page of skills and navigation buttons."""
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
        if self.selected_description:
            # Render multiline description
            lines = self.selected_description.split('\n')
            y = 100
            for line in lines:
                desc_surface = self.message_font.render(line, True, (255, 255, 255))
                # screen.blit(desc_surface, (SCREEN_WIDTH // 2 - desc_surface.get_width() // 2, y))
                screen.blit(desc_surface, (SCREEN_WIDTH // 2 + 200, y))
                y += desc_surface.get_height() + 5  # Spacing between lines

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle keyboard and mouse events for viewing skill descriptions or navigation.

        Returns:
            str: The triggered action name.
        """
        if not self.active:
            return ""
        if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
            self.selected_description = None
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
                    self.game.menu_manager.close_menu(MenuNavigation.SKILL_LIBRARY_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
                    return BasicAction.EXIT_MENU
                elif action == "previous" and self.current_page > 0:
                    self.current_page -= 1
                    self._update_buttons()
                    return "previous"
                elif action == "next" and self.current_page < self.total_pages - 1:
                    self.current_page += 1
                    self._update_buttons()
                    return "next"
                elif action.startswith("skill_"):
                    skill_idx = int(action.split("_")[1])
                    skill = self.skills[skill_idx]
                    self.selected_description = self._get_skill_description(skill)
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "crystal_menu":
                    self.game.menu_manager.close_menu(MenuNavigation.SKILL_LIBRARY_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
                    return BasicAction.EXIT_MENU
                elif action == "previous" and self.current_page > 0:
                    self.current_page -= 1
                    self._update_buttons()
                    return "previous"
                elif action == "next" and self.current_page < self.total_pages - 1:
                    self.current_page += 1
                    self._update_buttons()
                    return "next"
                elif action.startswith("skill_"):
                    skill_idx = int(action.split("_")[1])
                    skill = self.skills[skill_idx]
                    self.selected_description = self._get_skill_description(skill)
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
            self._update_buttons()
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False
            self.selected_description = None