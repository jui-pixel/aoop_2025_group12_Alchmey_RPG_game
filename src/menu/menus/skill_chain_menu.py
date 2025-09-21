# src/menu/menus/naming_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class SkillChainMenu(AbstractMenu):
    def __init__(self, game: 'Game', options=None):
        """Initialize the skill chain menu with 9 slots for skill chains 1-9 and a complete button."""
        self.title = "Skill Chains"
        self.game = game
        self.options = options
        self.buttons = []
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self._update_buttons()

    def _update_buttons(self):
        """Update the button list for the 3x3 grid of skill chains and the complete button."""
        self.buttons = []
        for i in range(9):
            row = i // 3
            col = i % 3
            button_text = f"Chain {i+1}"
            self.buttons.append(
                Button(
                    SCREEN_WIDTH // 2 - 150 + col * 110, 100 + row * 50, 100, 40,
                    button_text, pygame.Surface((100, 40)), f"edit_chain_{i}",
                    pygame.font.SysFont(None, 36)
                )
            )
        # Add complete button at bottom right
        self.buttons.append(
            Button(
                SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100, 150, 40,
                "Complete", pygame.Surface((150, 40)), "close",
                pygame.font.SysFont(None, 36)
            )
        )
        self.buttons[self.selected_index].is_selected = True

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the skill chain menu, including title and buttons."""
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
        """Handle keyboard and mouse events for editing chains or completing.

        Returns:
            str: The triggered action name.
        """
        if not self.active:
            return ""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.hide_menu('skill_chain_menu')
                return "close"
            elif event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 3) % len(self.buttons) if self.selected_index >= 3 else self.selected_index
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 3) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_LEFT:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_RIGHT:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_RETURN:
                action = self.buttons[self.selected_index].action
                if action.startswith("edit_chain_"):
                    chain_idx = int(action.split("_")[2])
                    self.game.show_menu('skill_chain_edit_menu', chain_idx=chain_idx)
                    return f"edit_chain_{chain_idx}"
                elif action == "close":
                    self.game.hide_menu('skill_chain_menu')
                    return "close"
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.buttons[self.selected_index].is_selected = False
                    self.selected_index = i
                    self.buttons[self.selected_index].is_selected = True
                    break
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action.startswith("edit_chain_"):
                    chain_idx = int(action.split("_")[2])
                    self.game.show_menu('skill_chain_edit_menu', chain_idx=chain_idx)
                    return f"edit_chain_{chain_idx}"
                elif action == "close":
                    self.game.hide_menu('skill_chain_menu')
                    return "close"
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self._update_buttons()
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False