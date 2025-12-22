# src/menu/menus/alchemy_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import random
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
from typing import List, Dict

from src.menu.menus.amplifier_choose_menu import AmplifierChooseMenu
from ...utils.elements import ELEMENTS, WEAKTABLE

class AlchemyMenu(AbstractMenu):
    def __init__(self, game: 'Game', options = None):
        self.title = "Skill Crafting"
        self.game = game
        self.main_material = "missile"  # Default
        self.element = "untyped"  # Default
        self.amplifier_levels = {}  # Dict of name: level
        self.success_rate = 0
        self.message = ""
        self.buttons = [
            Button(100, 100, 200, 40, "Choose Main", pygame.Surface((200, 40)), "choose_main", pygame.font.SysFont(None, 36)),
            Button(SCREEN_WIDTH // 2 - 100, 100, 200, 40, "Choose Element", pygame.Surface((200, 40)), "choose_element", pygame.font.SysFont(None, 36)),
            Button(SCREEN_WIDTH - 300, 100, 200, 40, "Choose Amplifiers", pygame.Surface((200, 40)), "choose_amplifier", pygame.font.SysFont(None, 36)),
            Button(SCREEN_WIDTH - 300, SCREEN_HEIGHT - 100, 200, 40, "Synthesize", pygame.Surface((200, 40)), "synthesize", pygame.font.SysFont(None, 36)),
            Button(100, SCREEN_HEIGHT - 100, 200, 40, "Back", pygame.Surface((200, 40)), "back", pygame.font.SysFont(None, 36))
        ]
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 36)
        self.buttons[self.selected_index].is_selected = True
        self._register_menus()
    
    def _register_menus(self):
        # Register dependent menus if not already registered
        if not self.game.menu_manager.menus.get(MenuNavigation.MAIN_MATERIAL_MENU):
            from src.menu.menus.main_material_menu import MainMaterialMenu
            self.game.menu_manager.register_menu(MenuNavigation.MAIN_MATERIAL_MENU, MainMaterialMenu(self.game, None))
        if not self.game.menu_manager.menus.get(MenuNavigation.ELEMENT_CHOOSE_MENU):
            from src.menu.menus.element_choose_menu import ElementChooseMenu
            self.game.menu_manager.register_menu(MenuNavigation.ELEMENT_CHOOSE_MENU, ElementChooseMenu(self.game, None))

    def calculate_success_rate(self):
        if self.element != "untyped":  # Count as 1 if selected
            num_elements = 1
        else:
            num_elements = 0
        if num_elements > 1:
            self.success_rate = 0
            return
        if self.main_material == "missile":
            stat_level = self.game.storage_manager.attack_level
        elif self.main_material == "shield":
            stat_level = self.game.storage_manager.defense_level
        elif self.main_material == "step":
            stat_level = self.game.storage_manager.movement_level
        else:
            stat_level = 0
        max_cost = stat_level ** 2
        used_cost = sum(self.amplifier_levels.values())
        self.success_rate = max(0, min(100, (max_cost - used_cost) * 10 + 10))

    def create_skill_dict(self, name):
        if self.main_material == "missile":
            skill_type = "shooting"
            sub_type = None
            params = {k.replace('_level', ''): v for k, v in self.amplifier_levels.items()}
        elif self.main_material == "shield":
            skill_type = "buff"
            sub_type = "shield"
            params = {k.replace('_level', ''): v for k, v in self.amplifier_levels.items()}
        elif self.main_material == "step":
            skill_type = "buff"
            sub_type = "step"
            params = {k.replace('_level', ''): v for k, v in self.amplifier_levels.items()}
        else:
            return None
        return {
            'name': name,
            'type': skill_type,
            'sub_type': sub_type,
            'element': self.element,
            'params': params
        }

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        self.calculate_success_rate()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        # Display current choices
        main_text = self.font.render(f"Main: {self.main_material.capitalize()}", True, (255, 255, 255))
        screen.blit(main_text, (100, 150))
        elem_text = self.font.render(f"Element: {self.element.capitalize()}", True, (255, 255, 255))
        screen.blit(elem_text, (SCREEN_WIDTH // 2 - 100, 150))
        amp_text = self.font.render("Amplifiers:", True, (255, 255, 255))
        screen.blit(amp_text, (SCREEN_WIDTH - 300, 150))
        y = 200
        for name, level in self.amplifier_levels.items():
            amp_detail = self.font.render(f"{name.replace('_level', '').capitalize()}: {level}", True, (255, 255, 255))
            screen.blit(amp_detail, (SCREEN_WIDTH - 300, y))
            y += 50
        success_text = self.font.render(f"Success Rate: {self.success_rate}%", True, (255, 255, 255))
        screen.blit(success_text, (SCREEN_WIDTH - 300, SCREEN_HEIGHT // 2))
        material_text = self.font.render("Materials: 1 Mana", True, (255, 255, 255))
        screen.blit(material_text, (100, SCREEN_HEIGHT - 150))
        msg_text = self.font.render(self.message, True, (255, 0, 0))
        screen.blit(msg_text, (SCREEN_WIDTH // 2 - msg_text.get_width() // 2, SCREEN_HEIGHT - 200))
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
                self.game.menu_manager.close_menu(MenuNavigation.ALCHEMY_MENU)
                return BasicAction.EXIT_MENU
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
                    self.game.menu_manager.close_menu(MenuNavigation.ALCHMEY_MENU)
                    return BasicAction.EXIT_MENU
                elif action == "choose_main":
                    self.game.menu_manager.open_menu(MenuNavigation.MAIN_MATERIAL_MENU)
                    return "choose_main"
                elif action == "choose_element":
                    self.game.menu_manager.open_menu(MenuNavigation.ELEMENT_CHOOSE_MENU)
                    return "choose_element"
                elif action == "choose_amplifier":
                    amp_menu = self.game.menu_manager.menus[MenuNavigation.AMPLIFIER_CHOOSE_MENU]
                    if not amp_menu:
                        amp_menu = self.game.menu_manager.menus[MenuNavigation.AMPLIFIER_CHOOSE_MENU] = AmplifierChooseMenu(self.game, None)
                    amp_menu.update_amplifiers()
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_CHOOSE_MENU)
                    return "choose_amplifier"
                elif action == "synthesize":
                    if self.game.storage_manager.mana < 1:
                        self.message = "Not enough mana"
                        return ""
                    self.game.storage_manager.mana -= 1
                    if random.random() * 100 < self.success_rate:
                        self.message = "Synthesis Success! Enter name."
                        self.game.menu_manager.open_menu(MenuNavigation.NAMING_MENU)
                    else:
                        self.message = "Synthesis Failed"
                    return "synthesize"
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back":
                    self.game.menu_manager.close_menu(MenuNavigation.ALCHEMY_MENU)
                    return BasicAction.EXIT_MENU
                elif action == "choose_main":
                    self.game.menu_manager.open_menu(MenuNavigation.MAIN_MATERIAL_MENU)
                    return "choose_main"
                elif action == "choose_element":
                    self.game.menu_manager.open_menu(MenuNavigation.ELEMENT_CHOOSE_MENU)
                    return "choose_element"
                elif action == "choose_amplifier":
                    self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_CHOOSE_MENU)
                    amp_menu = self.game.menu_manager.menus[MenuNavigation.AMPLIFIER_CHOOSE_MENU]
                    if not amp_menu:
                        amp_menu = self.game.menu_manager.menus[MenuNavigation.AMPLIFIER_CHOOSE_MENU] = AmplifierChooseMenu(self.game, None)
                    amp_menu.update_amplifiers()
                    return "choose_amplifier"
                elif action == "synthesize":
                    if self.game.storage_manager.mana < 1:
                        self.message = "Not enough mana"
                        return ""
                    self.game.storage_manager.mana -= 1
                    if random.random() * 100 < self.success_rate:
                        self.message = "Synthesis Success! Enter name."
                        self.game.menu_manager.open_menu(MenuNavigation.NAMING_MENU)
                    else:
                        self.message = "Synthesis Failed"
                    return "synthesize"
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False
            
    def reset(self):
        self.main_material = "missile"
        self.element = "untyped"
        self.amplifier_levels = {}
        self.success_rate = 0
        self.message = ""
        
    def set_main_material(self, material: str) -> None:
        self.reset()
        self.main_material = material