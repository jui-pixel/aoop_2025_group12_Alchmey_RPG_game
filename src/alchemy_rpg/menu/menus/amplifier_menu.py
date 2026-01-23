# src/menu/menus/amplifier_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import math
import random
from typing import List, Dict
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

class AmplifierMenu(AbstractMenu):
    """增幅器類型選擇菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options: List[Dict] = None):
        """初始化增幅器選擇菜單"""
        self.game = game
        self.title = "Amplifier Selection"
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        
        # 初始化按鈕
        self._init_buttons()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _init_buttons(self):
        """初始化按鈕位置與樣式"""
        btn_width = 320
        btn_height = 60
        start_y = 200
        gap = 30
        center_x = SCREEN_WIDTH // 2
        
        # 定義選項
        options = [
            ("Magic Missile", "show_magic_missile", (100, 100, 255)),  # 藍色系
            ("Magic Shield", "show_magic_shield", (100, 255, 100)),    # 綠色系
            ("Magic Step", "show_magic_step", (255, 255, 100)),        # 黃色系
        ]
        
        self.buttons = []
        
        # 類型按鈕
        for i, (text, action, color) in enumerate(options):
            y = start_y + i * (btn_height + gap)
            btn = Button(
                center_x - btn_width // 2, y, btn_width, btn_height,
                text,
                self._create_button_surface(btn_width, btn_height, color),
                action,
                self.header_font
            )
            self.buttons.append(btn)
            
        # 返回按鈕
        back_y = SCREEN_HEIGHT - 100
        back_btn = Button(
            center_x - btn_width // 2, back_y, btn_width, btn_height,
            "Back",
            self._create_button_surface(btn_width, btn_height, (200, 100, 100)),
            "crystal_menu",
            self.header_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建帶有水晶質感的按鈕表面"""
        surface = pygame.Surface((width, height))
        # 漸層背景
        r, g, b = base_color
        for y in range(height):
            factor = 1 - (y / height) * 0.3
            color = (int(r * factor * 0.5), int(g * factor * 0.5), int(b * factor * 0.5))
            pygame.draw.line(surface, color, (0, y), (width, y))
            
        # 邊框
        pygame.draw.rect(surface, (min(255, int(r*1.5)), min(255, int(g*1.5)), min(255, int(b*1.5))), (0, 0, width, height), 2)
        return surface

    def _init_particles(self):
        """初始化背景粒子"""
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(2, 4),
                'speed': random.uniform(0.5, 2.0),
                'alpha': random.randint(50, 200)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背境
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((20, 15, 25))
        overlay.set_alpha(230)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子效果
        for p in self.particles:
            color = (150, 150, 255, p['alpha'])
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
            # 移動
            p['y'] -= p['speed']
            if p['y'] < 0:
                p['y'] = SCREEN_HEIGHT
                p['x'] = random.randint(0, SCREEN_WIDTH)
        
        # 3. 標題
        title_y = 60 + math.sin(self.animation_time) * 5
        title_surf = self.title_font.render(self.title, True, (220, 220, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, int(title_y)))
        # 標題光暈
        glow_surf = self.title_font.render(self.title, True, (100, 100, 200))
        screen.blit(glow_surf, (title_rect.x + 2, title_rect.y + 2))
        screen.blit(title_surf, title_rect)
        
        # 4. 按鈕
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        # 鼠標
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        self.buttons[self.selected_index].is_selected = True
                    break
                    
        # 鍵盤
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
                
        # 按鈕點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
                
        return ""
        
    def _process_action(self, action: str) -> str:
        if action == "crystal_menu":
            self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
            return BasicAction.EXIT_MENU
            
        elif action.startswith("show_"):
            # 解析動作名稱 show_magic_missile -> magic_missile
            parts = action.split("_")
            if len(parts) >= 3:
                amplifier_type = parts[1] + "_" + parts[2]
                
                # 更新狀態菜單（如果有的話）
                stat_menu = self.game.menu_manager.menus.get('amplifier_stat_menu')
                if stat_menu:
                    # 使用 getattr 以防方法名稱不同，或直接調用
                    if hasattr(stat_menu, 'update_type'):
                        stat_menu.update_type(amplifier_type)
                        
                # 傳遞數據並打開菜單
                self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_STAT_MENU, data={'type': amplifier_type})
                return action
                
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False