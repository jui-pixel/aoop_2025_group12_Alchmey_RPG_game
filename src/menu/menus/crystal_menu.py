from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import Dict, List

class CrystalMenu(AbstractMenu):
    def __init__(self, game: 'Game', crystals: Dict[str, Dict]):
        self.title = "Crystal Shop"
        self.game = game
        self.crystals = list(crystals.items())
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                f"{crystal_type} (Price: {info['price']} Gold)",
                pygame.Surface((300, 40)), f"purchase_{crystal_type}",
                pygame.font.SysFont(None, 36)
            ) for i, (crystal_type, info) in enumerate(self.crystals)
        ]
        self.buttons.append(
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + len(self.crystals) * 50, 300, 40,
                "Exit", pygame.Surface((300, 40)), "exit",
                pygame.font.SysFont(None, 36)
            )
        )
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
                    self.game.hide_menu('crystal_shop')
                    return "exit"
                if action.startswith("purchase_"):
                    crystal_type = action.split("_")[1]
                    for npc in self.game.entity_manager.npc_group:
                        if npc.tag == "magic_crystal_npc":
                            npc.purchase_crystal(crystal_type)
                            self.game.hide_menu('crystal_shop')
                            break
                return action
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "exit":
                    self.game.hide_menu('crystal_shop')
                    return "exit"
                if action.startswith("purchase_"):
                    crystal_type = action.split("_")[1]
                    for npc in self.game.entity_manager.npc_group:
                        if npc.tag == "magic_crystal_npc":
                            npc.purchase_crystal(crystal_type)
                            self.game.hide_menu('crystal_shop')
                            break
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