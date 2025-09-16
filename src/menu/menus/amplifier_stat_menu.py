from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from typing import List, Dict, Tuple
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class AmplifierStatMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: Dict):
        """Initialize the amplifier effect menu for the specified amplifier type.

        Args:
            game: The main game instance for accessing storage manager and menu management.
            options: Dict containing 'type' for the amplifier type.
        """
        amplifier_type = options.get('type', 'magic_missile')
        self.title = f"{amplifier_type.replace('_', ' ').title()} Effects"
        self.game = game
        self.amplifier_type = amplifier_type
        self.effect_cost = 300  # Cost in mana to apply each effect
        self.effects = {
            "magic_missile": ["Increase Damage", "Increase Speed", "Pierce"],
            "magic_shield": ["Increase Duration", "Increase Strength", "Reflect"],
            "magic_step": ["Increase Speed", "Reduce Cooldown", "Dash Distance"]
        }.get(amplifier_type, [])
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                effect, pygame.Surface((300, 40)), f"apply_{effect.lower().replace(' ', '_')}",
                pygame.font.SysFont(None, 36)
            ) for i, effect in enumerate(self.effects)
        ]
        self.buttons.append(
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + len(self.effects) * 50, 300, 40,
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
        """Draw the amplifier effect menu, including title and buttons."""
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
        if self.message:
            msg_surface = self.message_font.render(self.message, True, (255, 0, 0))
            screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT - 100))

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle keyboard and mouse events for applying effects or returning.

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
                    self.game.hide_menu('amplifier_stat_menu')
                    self.game.show_menu('amplifier_menu')
                    return "back"
                elif action.startswith("apply_"):
                    effect = action.split("_")[1]
                    success, reason = self._apply_effect(effect)
                    if success:
                        print(f"AmplifierStatMenu: Applied {effect} to {self.amplifier_type}")
                    else:
                        self.message = reason
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back":
                    self.game.hide_menu('amplifier_stat_menu')
                    self.game.show_menu('amplifier_menu')
                    return "back"
                elif action.startswith("apply_"):
                    effect = action.split("_")[1]
                    success, reason = self._apply_effect(effect)
                    if success:
                        print(f"AmplifierStatMenu: Applied {effect} to {self.amplifier_type}")
                    else:
                        self.message = reason
                    return action
        return ""

    def _apply_effect(self, effect: str) -> Tuple[bool, str]:
        """Apply the specified amplifier effect, checking mana.

        Args:
            effect: The effect name.

        Returns:
            Tuple[bool, str]: (Success, Reason message).
        """
        return self.game.storage_manager.add_amplifier_effect(self.amplifier_type, effect, cost=self.effect_cost)

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