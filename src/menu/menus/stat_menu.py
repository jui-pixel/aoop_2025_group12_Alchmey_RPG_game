# src/menu/menus/stat_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Dict, Tuple

class StatMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: List[Dict]):
        """Initialize the stat upgrade menu with options for attack, defense, movement, health, and back.

        Args:
            game: The main game instance for accessing storage manager and menu management.
        """
        self.title = "Stat Upgrade"
        self.game = game
        self.costs = [cost for cost in range(1, 101, 1)]  # Upgrade costs per level
        self.max_level = 100  # Maximum level for each stat
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                self._get_button_text(stat),
                pygame.Surface((300, 40)), action,
                pygame.font.SysFont(None, 36)
            ) for i, (stat, action) in enumerate([
                ("attack", "upgrade_attack"),
                ("defense", "upgrade_defense"),
                ("movement", "upgrade_movement"),
                ("health", "upgrade_health"),
                ("Back", "crystal_menu")
            ])
        ]
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.message_font = pygame.font.SysFont(None, 36)
        self.message = None
        self.buttons[self.selected_index].is_selected = True

    def _get_button_text(self, stat: str) -> str:
        """Generate button text with current level and upgrade cost.

        Args:
            stat: The stat name (attack, defense, movement, health).

        Returns:
            str: Button display text.
        """
        if stat == "Back":
            return "Back"
        level = getattr(self.game.storage_manager, f"{stat}_level", 0)
        cost = self.costs[level] if level < self.max_level else "Max"
        return f"{stat.capitalize()} (Level {level}, Cost: {cost})"

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the stat menu, including title and buttons."""
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        # Update button text to reflect current levels and costs
        for i, button in enumerate(self.buttons):
            if button.action != "crystal_menu":
                stat = button.action.split("_")[1]
                button.text = self._get_button_text(stat)
        for button in self.buttons:
            button.draw(screen)
        if self.message:
            msg_surface = self.message_font.render(self.message, True, (255, 0, 0))
            screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT - 100))

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle keyboard and mouse events for upgrading stats or returning.

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
                    self.game.hide_menu('stat_menu')
                    self.game.show_menu('crystal_menu')
                    return "crystal_menu"
                elif action.startswith("upgrade_"):
                    stat = action.split("_")[1]
                    success, reason = self._upgrade_stat(stat)
                    if success:
                        print(f"StatMenu: Upgraded {stat} successfully")
                    else:
                        self.message = reason
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "crystal_menu":
                    self.game.hide_menu('stat_menu')
                    self.game.show_menu('crystal_menu')
                    return "crystal_menu"
                elif action.startswith("upgrade_"):
                    stat = action.split("_")[1]
                    success, reason = self._upgrade_stat(stat)
                    if success:
                        print(f"StatMenu: Upgraded {stat} successfully")
                    else:
                        self.message = reason
                    return action
        return ""

    def _upgrade_stat(self, stat: str) -> Tuple[bool, str]:
        """Upgrade the specified stat, checking mana and level limits.

        Args:
            stat: The stat to upgrade (attack, defense, movement, health).

        Returns:
            Tuple[bool, str]: (Success, Reason message).
        """
        current_level = getattr(self.game.storage_manager, f"{stat}_level", 0)
        if current_level >= self.max_level:
            return False, "Max level reached"
        cost = self.costs[current_level]
        if self.game.storage_manager.mana < cost:
            return False, "Insufficient mana"
        self.game.storage_manager.mana -= cost
        setattr(self.game.storage_manager, f"{stat}_level", current_level + 1)
        self.game.storage_manager.save_to_json()  # Save updated stats and mana to JSON
        self.game.storage_manager.apply_stats_to_player()  # Apply updated stats to player
        return True, ""

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