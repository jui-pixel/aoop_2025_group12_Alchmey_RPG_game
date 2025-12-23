# src/menu/menus/naming_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
class NamingMenu(AbstractMenu):
    def __init__(self, game: 'Game', options=None):
        self.title = "Name Your Skill"
        self.game = game
        self.skill_name = ""
        self.message = "Enter skill name and press Enter"
        self.font = pygame.font.SysFont(None, 36)
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 40, "Confirm", pygame.Surface((200, 40)), "back_to_lobby", self.font),
            Button(100, SCREEN_HEIGHT - 100, 200, 40, "Back", pygame.Surface((200, 40)), "back_to_alchemy", self.font)
        ]
        self.selected_index = 0
        self.active = False
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
        name_surface = self.font.render(f"Skill Name: {self.skill_name}", True, (255, 255, 255))
        screen.blit(name_surface, (SCREEN_WIDTH // 2 - name_surface.get_width() // 2, SCREEN_HEIGHT // 2))
        msg_surface = self.font.render(self.message, True, (255, 0, 0))
        screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
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
            if event.key == pygame.K_ESCAPE:
                self.game.menu_manager.close_menu(MenuNavigation.NAMING_MENU)
                self.game.menu_manager.open_menu(MenuNavigation.ALCHEMY_MENU)
                return BasicAction.EXIT_MENU
            elif event.key == pygame.K_RETURN:
                if self.skill_name:
                    alchemy_menu = self.game.menu_manager.menus.get(MenuNavigation.ALCHEMY_MENU)
                    if alchemy_menu:
                        skill_dict = alchemy_menu.create_skill_dict(self.skill_name)
                        if skill_dict:
                            self.game.storage_manager.add_skill_to_library(skill_dict)
                            self.game.storage_manager.apply_skills_to_player()
                            self.game.menu_manager.close_menu(MenuNavigation.NAMING_MENU)
                            alchemy_menu.reset()
                            return BasicAction.EXIT_MENU
                        else:
                            self.message = "Invalid skill parameters"
                    else:
                        self.message = "Alchemy menu not found"
                else:
                    self.message = "Please enter a skill name"
            elif event.key == pygame.K_BACKSPACE:
                self.skill_name = self.skill_name[:-1]
            else:
                char = event.unicode
                if char.isalnum() or char in ['_', ' ']:
                    self.skill_name += char
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back_to_alchemy":
                    self.game.menu_manager.close_menu(MenuNavigation.NAMING_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.ALCHEMY_MENU)
                    return BasicAction.EXIT_MENU
                elif action == "back_to_lobby" and self.skill_name:
                    alchemy_menu = self.game.menu_manager.menus.get(MenuNavigation.ALCHEMY_MENU)
                    if alchemy_menu:
                        skill_dict = alchemy_menu.create_skill_dict(self.skill_name)
                        if skill_dict:
                            self.game.storage_manager.add_skill_to_library(skill_dict)
                            self.game.storage_manager.apply_skills_to_player()
                            self.game.menu_manager.close_menu(MenuNavigation.NAMING_MENU)
                            alchemy_menu.reset()
                            self.game.menu_manager.close_all_menus()
                            return BasicAction.EXIT_MENU
                        else:
                            self.message = "Invalid skill parameters"
                    else:
                        self.message = "Alchemy menu not found"
        return ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
            self.skill_name = ""
            self.message = "Enter skill name and press Enter"
        else:
            self.buttons[self.selected_index].is_selected = False
        
    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""