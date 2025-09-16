from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class AmplifierChooseMenu(AbstractMenu):
    def __init__(self, game: 'Game', options=None):
        self.title = "Choose Amplifiers"
        self.game = game
        self.active = False
        self.font = pygame.font.SysFont(None, 36)
        self.rects = []
        self.back_button = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 300, 40, "Back", pygame.Surface((300, 40)), "back", self.font)
        self.amplifier_names = []  # Will be set based on main material
        self.capped = {'elebuff': 1, 'remove_element': 1, 'remove_counter': 1}  # Names with max 1

    def update_amplifiers(self):
        alchemy_menu = self.game.menu_manager.menus['alchemy_menu']
        main = alchemy_menu.main_material
        if main == "missile":
            self.amplifier_names = ['damage_level', 'penetration_level', 'elebuff_level', 'explosion_level', 'speed_level']
        elif main == "shield":
            self.amplifier_names = ['element_resistance_level', 'remove_element_level', 'counter_element_resistance_level', 'remove_counter_level', 'duration_level', 'shield_level']
        elif main == "step":
            self.amplifier_names = ['avoid_level', 'speed_level', 'duration_level']
        else:
            self.amplifier_names = []

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        self.rects = []
        alchemy_menu = self.game.menu_manager.menus['alchemy_menu']
        for i, name in enumerate(self.amplifier_names):
            level = alchemy_menu.amplifier_levels.get(name, 0)
            text = f"{name.replace('_level', '').capitalize()}: {level}"
            surf = self.font.render(text, True, (255, 255, 255))
            rect = surf.get_rect(topleft=(SCREEN_WIDTH // 2 - 150, 100 + i * 50))
            screen.blit(surf, rect)
            self.rects.append(rect)
        self.back_button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(pos):
                    name = self.amplifier_names[i]
                    alchemy_menu = self.game.menu_manager.menus['alchemy_menu']
                    if event.button == 1:  # Left click increase
                        alchemy_menu.amplifier_levels[name] = alchemy_menu.amplifier_levels.get(name, 0) + 1
                        if name.replace('_level', '') in self.capped:
                            alchemy_menu.amplifier_levels[name] = min(alchemy_menu.amplifier_levels[name], self.capped[name.replace('_level', '')])
                    elif event.button == 3:  # Right click decrease
                        alchemy_menu.amplifier_levels[name] = max(0, alchemy_menu.amplifier_levels.get(name, 0) - 1)
                    return ""
            if self.back_button.rect.collidepoint(pos):
                self.game.show_menu('alchemy_menu')
                return "back"
        active, action = self.back_button.handle_event(event)
        if active and action == "back":
            self.game.show_menu('alchemy_menu')
            return "back"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.show_menu('alchemy_menu')
            return "back"
        return ""

    def get_selected_action(self) -> str:
        return ""

    def activate(self, active: bool) -> None:
        self.active = active