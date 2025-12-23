# src/menu/menus/setting_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Dict

class SettingsMenu(AbstractMenu):
    def __init__(self, game: 'Game', dungeons: List[Dict]):
        self.title = "Settings"
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                text, pygame.Surface((300, 40)), action,
                pygame.font.SysFont(None, 36)
            ) for i, (text, action) in enumerate([
                ("Sound: ON", "toggle_sound"),
                ("Back", "back")
            ])
        ]
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.buttons[self.selected_index].is_selected = True

    def draw(self, screen: pygame.Surface) -> None:
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
            print(f"SettingsMenu: Key pressed: {event.key}")
            if event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                print(f"SettingsMenu: Selected index: {self.selected_index}")
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                print(f"SettingsMenu: Selected index: {self.selected_index}")
            elif event.key == pygame.K_RETURN:
                action = self.buttons[self.selected_index].action
                print(f"SettingsMenu: Enter pressed, action: {action}")
                return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                print(f"SettingsMenu: Button clicked, action: {action}")
                return action
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
            print("SettingsMenu: Activated")
        else:
            self.buttons[self.selected_index].is_selected = False
            print("SettingsMenu: Deactivated")