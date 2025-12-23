# src/menu/menus/amplifier_stat_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from typing import List, Dict, Tuple
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

class AmplifierStatMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: Dict = None):
        """Initialize the amplifier effect menu for viewing effect descriptions.

        Args:
            game: The main game instance for accessing storage manager and menu management.
            options: Dict containing 'type' for the amplifier type (default: 'magic_missile').
        """
        self.game = game
        self.amplifier_type = 'magic_missile'  # Default type
        self.title = "Magic Missile Effects"  # Default title
        self.effect_mapping = self._get_effect_mapping(self.amplifier_type)
        self.buttons = self._create_buttons()
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.message_font = pygame.font.SysFont(None, 36)
        self.selected_description = None
        # Apply initial options if provided
        if options and 'type' in options:
            self.update_type(options['type'])
        self.buttons[self.selected_index].is_selected = True

    def _get_effect_mapping(self, amplifier_type: str) -> List[Tuple[str, str, str]]:
        """Get the effect mapping for the given amplifier type."""
        mapping = {
            "magic_missile": [
                ("Increase Damage", "damage_level", "Increases missile damage by 10 per level"),
                ("Pierce", "penetration_level", "Allows missile to hit one additional enemy per level"),
                ("Elemental Buff", "elebuff_level", "Enhances elemental damage by 5% (max level 1)"),
                ("Explosion", "explosion_level", "Adds explosion with radius 50 per level"),
                ("Increase Speed", "speed_level", "Increases missile speed by 50 units per level")
            ],
            "magic_shield": [
                ("Element Resistance", "element_resistance_level", "Reduces elemental damage taken by 10% per level"),
                ("Remove Element", "remove_element_level", "Grants chance to negate elemental effects (max level 1)"),
                ("Counter Resistance", "counter_element_resistance_level", "Reflects 10% of elemental damage (max level 1)"),
                ("Remove Counter", "remove_counter_level", "Grants chance to negate counterattacks (max level 1)"),
                ("Increase Duration", "duration_level", "Extends shield duration by 1 second per level"),
                ("Increase Strength", "shield_level", "Increases shield health by 20 per level")
            ],
            "magic_step": [
                ("Reduce Cooldown", "avoid_level", "Reduces step cooldown by 0.5 seconds per level"),
                ("Increase Speed", "speed_level", "Increases movement speed by 20 units per level"),
                ("Dash Distance", "duration_level", "Extends dash distance by 10 units per level")
            ]
        }
        return mapping.get(amplifier_type, [])

    def _create_buttons(self) -> List[Button]:
        """Create buttons based on current effect_mapping."""
        buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                effect_name,
                pygame.Surface((300, 40)), f"view_{effect_name.lower().replace(' ', '_')}",
                pygame.font.SysFont(None, 36)
            ) for i, (effect_name, _, description) in enumerate(self.effect_mapping)
        ]
        buttons.append(
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + len(self.effect_mapping) * 50, 300, 40,
                "Back", pygame.Surface((300, 40)), "back",
                pygame.font.SysFont(None, 36)
            )
        )
        return buttons

    def update_type(self, amplifier_type: str) -> None:
        """Update the menu to display effects for a new amplifier type.

        Args:
            amplifier_type: The new amplifier type (e.g., 'magic_shield').
        """
        self.amplifier_type = amplifier_type
        self.title = f"{amplifier_type.replace('_', ' ').title()} Effects"
        self.effect_mapping = self._get_effect_mapping(amplifier_type)
        self.buttons = self._create_buttons()
        self.selected_index = 0
        self.selected_description = None
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True
        print(f"AmplifierStatMenu: Updated to type '{amplifier_type}'")

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the amplifier effect menu, including title, buttons, and selected effect description."""
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
            desc_surface = self.message_font.render(self.selected_description, True, (255, 255, 255))
            screen.blit(desc_surface, (SCREEN_WIDTH // 2 - desc_surface.get_width() // 2, SCREEN_HEIGHT - 150))

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle keyboard and mouse events to view effect descriptions or return.

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
                if action == "back":
                    self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_STAT_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_MENU)
                    return BasicAction.EXIT_MENU
                elif action.startswith("view_"):
                    effect = "_".join(action.split("_")[1:])  # Join all parts after 'view_'
                    for effect_name, _, description in self.effect_mapping:
                        if effect_name.lower().replace(' ', '_') == effect:
                            self.selected_description = description
                            break
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back":
                    self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_STAT_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_MENU)
                    return BasicAction.EXIT_MENU
                elif action.startswith("view_"):
                    effect = "_".join(action.split("_")[1:])  # Join all parts after 'view_'
                    for effect_name, _, description in self.effect_mapping:
                        if effect_name.lower().replace(' ', '_') == effect:
                            self.selected_description = description
                            break
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
            self.selected_description = None