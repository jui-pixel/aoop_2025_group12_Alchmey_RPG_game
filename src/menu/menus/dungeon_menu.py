# src/menu/menus/dungeon_menu.py (修正版本)

from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Dict, TYPE_CHECKING, Optional

# 由於我們需要引用 DungeonPortalNPC，這裡使用 TYPE_CHECKING 避免循環依賴
if TYPE_CHECKING:
    from src.game import Game
    from src.entities.npc.dungeon_portal_npc import DungeonPortalNPC # 假設此為 Facade

class DungeonMenu(AbstractMenu):
    """地牢選擇菜單，直接操作開啟它的 DungeonPortalNPC 門面。"""
    
    def __init__(self, game: 'Game', dungeons: List[Dict], npc_facade: 'Optional[DungeonPortalNPC]' = None):
        """
        初始化地牢菜單。
        :param game: 遊戲實例。
        :param dungeons: 可選地牢列表。
        :param npc_facade: 開啟此菜單的 DungeonPortalNPC 門面實例。
        """
        self.title = "Dungeon Selection"
        self.game = game
        self.dungeons = dungeons
        # 【新增】儲存 DungeonPortalNPC 門面實例
        self.npc_facade = npc_facade 
        if not dungeons:
            dungeons = []
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + i * 50, 300, 40,
                f"{dungeon['name']} (Level {dungeon['level']})",
                pygame.Surface((300, 40)), f"enter_{dungeon['name']}",
                pygame.font.SysFont(None, 36)
            ) for i, dungeon in enumerate(dungeons)
        ]
        self.buttons.append(
            Button(
                SCREEN_WIDTH // 2 - 150, 100 + len(dungeons) * 50, 300, 40,
                "Back", pygame.Surface((300, 40)), "back_to_lobby",
                pygame.font.SysFont(None, 36)
            )
        )
        self.selected_index = 0
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        # 檢查按鈕列表是否為空
        if self.buttons:
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

    def _handle_enter_action(self, dungeon_name: str) -> str:
        """處理進入地牢的邏輯，使用 stored npc_facade。"""
        if self.npc_facade:
            # 【關鍵修正】直接調用 Facade 的方法，而不是在 Entity Manager 中搜索
            self.npc_facade.enter_dungeon(dungeon_name)
            self.game.menu_manager.set_menu(None) # 進入地牢後關閉所有菜單
        else:
            print("DungeonMenu: 錯誤！找不到 DungeonPortalNPC 門面實例。")
            
        return f"enter_{dungeon_name}"

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        # 處理鼠標懸停
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.buttons[self.selected_index].is_selected = False
                    self.selected_index = i
                    self.buttons[self.selected_index].is_selected = True
                    break
        
        # 處理鍵盤輸入
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
                if action == "back_to_lobby":
                    self.game.menu_manager.set_menu(None) # 返回時關閉菜單
                    return "back_to_lobby"
                if action.startswith("enter_"):
                    dungeon_name = action.split("_", 1)[1] # 處理多個下劃線的情況
                    return self._handle_enter_action(dungeon_name)
                return action
                
        # 處理鼠標點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back_to_lobby":
                    self.game.menu_manager.set_menu(None) # 返回時關閉菜單
                    return "back_to_lobby"
                if action.startswith("enter_"):
                    dungeon_name = action.split("_", 1)[1]
                    return self._handle_enter_action(dungeon_name)
                return action
                
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if self.buttons:
            if active:
                self.buttons[self.selected_index].is_selected = True
            else:
                self.buttons[self.selected_index].is_selected = False
                
    def update_npc_facade(self, npc_facade: 'DungeonPortalNPC') -> None:
        """更新存儲的 DungeonPortalNPC 門面實例。"""
        self.npc_facade = npc_facade