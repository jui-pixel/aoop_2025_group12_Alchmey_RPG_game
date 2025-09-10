from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Dict
class AlchemyMenu(AbstractMenu):
    def __init__(self, game: 'Game', options: List[Dict]):
        self.game = game
        self.options = options  # List of {'ingredients': [str], 'result': str}
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                f"{', '.join(opt['ingredients'])} -> {opt['result']}",
                pygame.Surface((300, 40)),
                f"synthesize_{i}"
            ) for i, opt in enumerate(options)
        ]
        self.buttons.append(
            Button(SCREEN_WIDTH // 2 - 150, 100 + len(options) * 50, 300, 40, "Exit", pygame.Surface((300, 40)), "exit")
        )
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 36)
        self.buttons[self.selected_index].is_selected = True

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        screen.fill((0, 0, 0))
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
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
                action = self.buttons[self.selected_index].action
                if action == "exit":
                    self.game.hide_menu('alchemy_menu')
                    return None
                if action.startswith("synthesize_"):
                    idx = int(action.split("_")[1])
                    for npc in self.game.entity_manager.npc_group:
                        if npc.tag == "alchemy_pot_npc":
                            npc.synthesize_item(self.options[idx]['ingredients'])
                            self.game.hide_menu('alchemy_menu')
                            break
                return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "exit":
                    self.game.hide_menu('alchemy_menu')
                    return None
                if action.startswith("synthesize_"):
                    idx = int(action.split("_")[1])
                    for npc in self.game.entity_manager.npc_group:
                        if npc.tag == "alchemy_pot_npc":
                            npc.synthesize_item(self.options[idx]['ingredients'])
                            self.game.hide_menu('alchemy_menu')
                            break
                return action
        return None

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else None

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False