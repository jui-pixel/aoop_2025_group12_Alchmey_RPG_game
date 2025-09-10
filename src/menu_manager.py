from src.menu.abstract_menu import AbstractMenu
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class MenuManager:
    def __init__(self, screen, game):
        self.screen = screen
        self.game = game
        self.menus = {}
        self.current_menu = None
        self.font = pygame.font.SysFont(None, 48)

    def register_menu(self, name, menu: AbstractMenu):
        self.menus[name] = menu
        menu.activate(False)
        print(f"MenuManager: Registered menu {name}")

    def set_menu(self, menu_name):
        if self.current_menu:
            self.current_menu.activate(False)
        if menu_name in self.menus:
            self.current_menu = self.menus[menu_name]
            self.current_menu.activate(True)
        else:
            self.current_menu = None
        print(f"MenuManager: Set menu to {menu_name}, current_menu: {self.current_menu.__class__.__name__ if self.current_menu else 'None'}")

    def draw(self):
        if self.current_menu:
            self.current_menu.draw(self.screen)
            pygame.display.flip()

    def handle_event(self, event):
        if self.current_menu:
            result = self.current_menu.handle_event(event)
            print(f"MenuManager: Handled event for {self.current_menu.__class__.__name__}, result: {result}")
            if self.current_menu.__class__.__name__ == "SettingsMenu" and result in ["toggle_sound", "back"]:
                if result == "toggle_sound":
                    print("MenuManager: Toggling sound (not implemented)")
                    # TODO: 實現音效開關
                elif result == "back":
                    self.game.hide_menu('settings_menu')
                return ""
            return result
        return ""