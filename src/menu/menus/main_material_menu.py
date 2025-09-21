# src/menu/menus/main_material_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class MainMaterialMenu(AbstractMenu):
    def __init__(self, game: 'Game', options=None):
        self.title = "Choose Main Material"
        self.game = game
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 100, 300, 40, "Attack (Magic Missile)", pygame.Surface((300, 40)), "missile", pygame.font.SysFont(None, 36)),
            Button(SCREEN_WIDTH // 2 - 150, 150, 300, 40, "Defense (Magic Shield)", pygame.Surface((300, 40)), "shield", pygame.font.SysFont(None, 36)),
            Button(SCREEN_WIDTH // 2 - 150, 200, 300, 40, "Movement (Magic Step)", pygame.Surface((300, 40)), "step", pygame.font.SysFont(None, 36)),
            Button(SCREEN_WIDTH // 2 - 150, 250, 300, 40, "Back", pygame.Surface((300, 40)), "back", pygame.font.SysFont(None, 36))
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
                    self.game.show_menu('alchemy_menu')
                    return "back"
                else:
                    alchemy_menu = self.game.menu_manager.menus['alchemy_menu']
                    alchemy_menu.set_main_material(action)
                    self.game.show_menu('alchemy_menu')
                    return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back":
                    self.game.show_menu('alchemy_menu')
                    return "back"
                else:
                    alchemy_menu = self.game.menu_manager.menus['alchemy_menu']
                    alchemy_menu.set_main_material(action)
                    self.game.show_menu('alchemy_menu')
                    return action
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False