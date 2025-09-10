from ..abstract_menu import AbstractMenu
from ..button import Button
import pygame
from ...config import SCREEN_WIDTH, SCREEN_HEIGHT


class MainMenu(AbstractMenu):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.title = "main_manu"
        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.font = pygame.rect
        self.buttons = [
            Button(10, 50 , 180, 30, "Enter Lobby", pygame.Surface((180, 30)), "enter_lobby"),
            Button(10, 90, 180, 30, "Setting", pygame.Surface((180, 30)), "show_setting"),
        ]
        self.selected_index = 0
        self.active = False
        self.buttons[self.selected_index].is_selected = True

    def draw(self, screen):
        if not self.active:
            return
        # 繪製選單背景
        pygame.draw.rect(screen, (50, 50, 50), (self.x, self.y, 200, len(self.buttons) * 40 + 50))
        # 繪製標題
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (self.x + 10, self.y + 10))
        # 繪製按鈕
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event):
        if not self.active:
            return None
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
                return self.buttons[self.selected_index].action, self.buttons[self.selected_index].text
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return action, button.text
        return None

    def get_selected_action(self):
        return self.buttons[self.selected_index].action if self.active else None

    def activate(self, active: bool):
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False