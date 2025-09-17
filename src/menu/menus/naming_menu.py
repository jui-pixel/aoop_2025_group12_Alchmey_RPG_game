from src.menu.abstract_menu import AbstractMenu
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class NamingMenu(AbstractMenu):
    def __init__(self, game: 'Game', options=None):
        self.title = "Name Your Skill"
        self.game = game
        self.name = ""
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.message = ""

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        name_surf = self.font.render(self.name, True, (255, 255, 255))
        screen.blit(name_surf, (SCREEN_WIDTH // 2 - name_surf.get_width() // 2, SCREEN_HEIGHT // 2))
        msg_surf = self.font.render(self.message, True, (255, 0, 0))
        screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.name:
                    alchemy_menu = self.game.menu_manager.menus['alchemy_menu']
                    skill_dict = alchemy_menu.create_skill_dict(self.name)
                    if skill_dict:
                        self.game.storage_manager.add_skill_to_library(skill_dict)
                        self.game.storage_manager.save_to_json()
                        print(f"Skill {self.name} added to library")
                        alchemy_menu.reset()  # Reset AlchemyMenu state
                    self.game.show_menu('alchemy_menu')
                    return "confirm"
                else:
                    self.message = "Name cannot be empty"
            elif event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
        elif event.type == pygame.TEXTINPUT:
            self.name += event.text
        return ""

    def get_selected_action(self) -> str:
        return ""

    def activate(self, active: bool) -> None:
        self.active = active
        self.name = ""
        self.message = ""