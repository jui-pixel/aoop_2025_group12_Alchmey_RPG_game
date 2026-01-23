# src/menu/menus/main_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import math
import random
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

class MainMenu(AbstractMenu):
    """主菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options=None):
        self.game = game
        self.title = "Roguelike Dungeon"
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 84) # 更大的標題字體
        self.button_font = pygame.font.SysFont(None, 40)
        self.debug_font = pygame.font.SysFont(None, 24)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        
        # 初始化按鈕
        self._init_buttons()
        self._init_particles()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _init_buttons(self):
        """初始化主菜單按鈕"""
        self.buttons = []
        
        btn_width = 300
        btn_height = 60
        gap = 30
        start_y = SCREEN_HEIGHT // 2
        center_x = SCREEN_WIDTH // 2
        
        # 定義選項
        options = [
            ("Start Journey", "enter_lobby", (100, 200, 100)), # 綠色: 開始
            ("Settings", "show_setting", (100, 150, 200)),     # 藍色: 設置
            ("Exit Game", "exit", (200, 100, 100))             # 紅色: 退出
        ]
        
        for i, (text, action, color) in enumerate(options):
            y = start_y + i * (btn_height + gap)
            btn = Button(
                center_x - btn_width // 2, y, btn_width, btn_height,
                text,
                self._create_button_surface(btn_width, btn_height, color),
                action,
                self.button_font
            )
            self.buttons.append(btn)
            
        # 調試/額外功能 (Win Screen 測試)
        # 放與右下角，小一點
        win_btn = Button(
            SCREEN_WIDTH - 120, SCREEN_HEIGHT - 50, 100, 30,
            "Demo Win",
            self._create_button_surface(100, 30, (150, 150, 50)),
            "show_win",
            self.debug_font
        )
        self.buttons.append(win_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建主菜單風格按鈕"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 漸層背景
        for i in range(height):
            c = (
                max(0, int(r * (1 - i/height * 0.5))),
                max(0, int(g * (1 - i/height * 0.5))),
                max(0, int(b * (1 - i/height * 0.5)))
            )
            pygame.draw.line(surface, c, (0, i), (width, i))
            
        # 邊框
        pygame.draw.rect(surface, (200, 200, 200), (0, 0, width, height), 2)
        # 內層裝飾線
        pygame.draw.rect(surface, (
            min(255, int(r*1.2)), min(255, int(g*1.2)), min(255, int(b*1.2))
        ), (4, 4, width-8, height-8), 1)
        
        return surface

    def _init_particles(self):
        """初始化混合元素粒子"""
        self.particles = []
        colors = [
            (255, 100, 100), # Fire
            (100, 100, 255), # Water
            (100, 255, 100), # Wind
            (255, 255, 100), # Thunder
            (200, 100, 255)  # Magic
        ]
        for _ in range(40):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(2, 5),
                'color': random.choice(colors),
                'speed': random.uniform(0.5, 2.0),
                'angle': random.uniform(0, math.pi * 2)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.02
        
        # 1. 動態星空/深空背景
        screen.fill((10, 10, 20))
        
        # 2. 粒子
        for p in self.particles:
            color = (*p['color'], 150)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
            p['x'] += math.cos(p['angle']) * p['speed']
            p['y'] += math.sin(p['angle']) * p['speed']
            
            # 邊界循環
            if p['x'] < 0: p['x'] = SCREEN_WIDTH
            if p['x'] > SCREEN_WIDTH: p['x'] = 0
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT
            if p['y'] > SCREEN_HEIGHT: p['y'] = 0
            
        # 3. 標題 (Roguelike Dungeon)
        title_y = 120
        # 標題陰影
        shadow_surf = self.title_font.render(self.title, True, (50, 0, 50))
        shadow_rect = shadow_surf.get_rect(center=(SCREEN_WIDTH // 2 + 4, title_y + 4))
        screen.blit(shadow_surf, shadow_rect)
        
        # 標題本體 (根據時間顏色變化)
        r = int(150 + 100 * math.sin(self.animation_time))
        g = int(150 + 100 * math.sin(self.animation_time + 2))
        b = int(150 + 100 * math.sin(self.animation_time + 4))
        title_surf = self.title_font.render(self.title, True, (r, g, b))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(title_surf, title_rect)
        
        # 4. 按鈕
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    if self.selected_index != i:
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
                return self._process_action(self.buttons[self.selected_index].action)
                
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
        return ""
        
    def _process_action(self, action: str) -> str:
        if action == "exit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return BasicAction.EXIT_MENU
        if action == "enter_lobby":
            self.game.menu_manager.close_menu(MenuNavigation.MAIN_MENU)
            self.game.start_game()
            return BasicAction.EXIT_MENU
        if action == "show_setting":
            self.game.menu_manager.close_menu(MenuNavigation.MAIN_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.SETTINGS_MENU)
            return BasicAction.EXIT_MENU
        if action == "show_win":
            self.game.menu_manager.close_menu(MenuNavigation.MAIN_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.WIN_MENU)
            return BasicAction.EXIT_MENU
        return action

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            # 隨機重置粒子
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False
            
    def update(self, dt: float) -> None:
        pass