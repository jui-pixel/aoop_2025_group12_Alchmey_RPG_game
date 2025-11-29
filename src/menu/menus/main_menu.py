# src/menu/menus/main_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Dict

class MainMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: List[Dict]=None):
        self.title = "Main Menu"
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                text, pygame.Surface((300, 40)), action,
                pygame.font.SysFont(None, 36)
            ) for i, (text, action) in enumerate([
                ("Enter Lobby", "enter_lobby"),
                ("Settings", "show_setting"),
                ("Exit", "exit")
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
            print(f"MainMenu: Key pressed: {event.key}")
            if event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                print(f"MainMenu: Selected index: {self.selected_index}")
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                print(f"MainMenu: Selected index: {self.selected_index}")
            elif event.key == pygame.K_RETURN:
                action = self.buttons[self.selected_index].action
                print(f"MainMenu: Enter pressed, action: {action}")
                if action == "exit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                print(f"MainMenu: Button clicked, action: {action}")
                if action == "exit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                return action
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
            print("MainMenu: Activated")
        else:
            self.buttons[self.selected_index].is_selected = False
            print("MainMenu: Deactivated")
    
    def update(self, dt: float) -> None:
        pass  # MainMenu 不需要更新邏輯