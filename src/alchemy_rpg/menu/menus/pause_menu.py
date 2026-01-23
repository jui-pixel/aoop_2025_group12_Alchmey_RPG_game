# src/menu/menus/pause_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import MenuNavigation, BasicAction

class PauseMenu(AbstractMenu):
    """暫停菜單"""
    
    def __init__(self, game: 'Game', data = None) -> None:
        self.game = game
        self.title = "PAUSED"
        self.active = False
        
        # 字體設置
        self.title_font = pygame.font.SysFont(None, 80)
        self.button_font = pygame.font.SysFont(None, 40)
        
        # 初始化按鈕
        self._init_buttons()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _init_buttons(self):
        """初始化按鈕"""
        btn_width = 250
        btn_height = 50
        gap = 20
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        self.buttons = []
        
        # 定義按鈕選項
        options = [
            ("Resume Game", "back", (100, 255, 100)),        # 綠色: 繼續
            ("Return to Title", "return_to_title", (255, 100, 100)) # 紅色: 返回標題
        ]
        
        for i, (text, action, color) in enumerate(options):
            y = center_y + i * (btn_height + gap)
            
            # 簡單創建按鈕表面
            surface = pygame.Surface((btn_width, btn_height))
            surface.fill((50, 50, 50)) # 底色
            pygame.draw.rect(surface, color, (0, 0, btn_width, btn_height), 2) # 邊框
            
            btn = Button(
                center_x - btn_width // 2, y, btn_width, btn_height,
                text,
                surface,
                action,
                self.button_font
            )
            self.buttons.append(btn)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        # 1. 繪製半透明遮罩 (Overlay)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150) # 半透明
        screen.blit(overlay, (0, 0))
        
        # 2. 繪製標題
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(title_surf, title_rect)
        
        # 3. 繪製按鈕
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        # 鍵盤導航
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
                return self._process_action(self.buttons[self.selected_index].action)
            elif event.key == pygame.K_ESCAPE:
                # 再次按 ESC 視為繼續遊戲
                return self._process_action("back")

        # 滑鼠操作
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        self.buttons[self.selected_index].is_selected = True
                    break

        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
                
        return ""

    def _process_action(self, action: str) -> str:
        if action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.PAUSE_MENU)
            return BasicAction.EXIT_MENU
        elif action == "return_to_title":
            # 返回標題畫面的邏輯
            self.game.menu_manager.open_menu(MenuNavigation.MAIN_MENU)
            # 這裡回傳特殊的字串，讓 MenuManager 處理狀態切換
            return "RETURN_TO_MAIN_MENU"
            
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        # 每次打開都重置選擇
        if active:
            self.selected_index = 0
            for btn in self.buttons:
                btn.is_selected = False
            self.buttons[0].is_selected = True