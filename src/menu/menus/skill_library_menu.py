from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from math import ceil
from typing import List, Dict, Tuple

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
        self.skill_cost = 200  # Mana cost to acquire a skill
        self.skills = self.game.storage_manager.skills_library if self.game.storage_manager.skills_library else []
        self.total_pages = ceil(len(self.skills) / self.skills_per_page)
        self.buttons = []
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.message_font = pygame.font.SysFont(None, 36)
        self.message = None
        self._update_buttons()

    def _update_buttons(self):
        """Update the button list for the current page, showing skills and navigation buttons."""
        self.buttons = []
        start_idx = self.current_page * self.skills_per_page
        end_idx = min(start_idx + self.skills_per_page, len(self.skills))
        for i, idx in enumerate(range(start_idx, end_idx)):
            skill = self.skills[idx]
            button_text = f"{skill['name']} {'(Owned)' if skill['name'] in self.game.storage_manager.skills else f'(Cost: {self.skill_cost})'}"
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

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the skill library menu, showing the current page of skills and navigation buttons."""
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(f"{self.title} (Page {self.current_page + 1}/{self.total_pages})", True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        for button in self.buttons:
            button.draw(screen)
        if self.message:
            msg_surface = self.message_font.render(self.message, True, (255, 0, 0))
            screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT - 100))

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle keyboard and mouse events for navigating pages or selecting skills.

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
                if action == "crystal_menu":
                    self.game.hide_menu('skill_library_menu')
                    self.game.show_menu('crystal_menu')
                    return "crystal_menu"
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
                    skill_name = self.skills[skill_idx]['name']
                    success, reason = self.game.storage_manager.add_skill(skill_name, cost=self.skill_cost)
                    if success:
                        print(f"SkillLibraryMenu: Added skill {skill_name} to player")
                        self._update_buttons()  # Update buttons to reflect ownership
                    else:
                        self.message = reason
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "crystal_menu":
                    self.game.hide_menu('skill_library_menu')
                    self.game.show_menu('crystal_menu')
                    return "crystal_menu"
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
                    skill_name = self.skills[skill_idx]['name']
                    success, reason = self.game.storage_manager.add_skill(skill_name, cost=self.skill_cost)
                    if success:
                        print(f"SkillLibraryMenu: Added skill {skill_name} to player")
                        self._update_buttons()  # Update buttons to reflect ownership
                    else:
                        self.message = reason
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
            self.message = None