# src/menu/menus/settings_menu.py
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

class SettingsMenu(AbstractMenu):
    """設置菜單 - 優化版"""
    
    def __init__(self, game: 'Game', data=None):
        self.game = game
        self.title = "Configuration"
        self.active = False
        
        # 設置狀態
        self.sound_enabled = True # 假設默認開啟，實際應從遊戲設置讀取
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.button_font = pygame.font.SysFont(None, 40)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        
        # 初始化
        self._init_buttons()
        self._init_particles()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _init_buttons(self):
        """初始化按鈕"""
        self.buttons = []
        
        btn_width = 300
        btn_height = 60
        gap = 30
        start_y = 250
        center_x = SCREEN_WIDTH // 2
        
        # 選項
        sound_text = "Sound: ON" if self.sound_enabled else "Sound: OFF"
        sound_color = (100, 200, 100) if self.sound_enabled else (150, 150, 150)
        
        # 聲音開關按鈕
        sound_btn = Button(
            center_x - btn_width // 2, start_y, btn_width, btn_height,
            sound_text,
            self._create_button_surface(btn_width, btn_height, sound_color),
            "toggle_sound",
            self.button_font
        )
        self.buttons.append(sound_btn)
        
        # 返回按鈕
        back_y = start_y + btn_height + gap
        back_btn = Button(
            center_x - btn_width // 2, back_y, btn_width, btn_height,
            "Save & Return",
            self._create_button_surface(btn_width, btn_height, (100, 150, 200)),
            "back",
            self.button_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建齒輪/機械風格按鈕"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 金屬質感背景
        surface.fill((30, 30, 35))
        pygame.draw.rect(surface, (
            int(r*0.5), int(g*0.5), int(b*0.5)
        ), (2, 2, width-4, height-4))
        
        # 鉚釘裝飾
        rivet_color = (200, 200, 200)
        pygame.draw.circle(surface, rivet_color, (5, 5), 2)
        pygame.draw.circle(surface, rivet_color, (width-5, 5), 2)
        pygame.draw.circle(surface, rivet_color, (5, height-5), 2)
        pygame.draw.circle(surface, rivet_color, (width-5, height-5), 2)
        
        # 邊框
        pygame.draw.rect(surface, (150, 150, 160), (0, 0, width, height), 2)
        
        return surface

    def _init_particles(self):
        """初始化機械/魔法微粒"""
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'color': (200, 200, 220),
                'speed': random.uniform(0.2, 0.8),
                'angle': random.uniform(0, math.pi * 2)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.02
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((15, 15, 20))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 齒輪裝飾 (背景旋轉)
        self._draw_gear(screen, SCREEN_WIDTH - 100, 100, 80, 12, 0.5, (50, 50, 60))
        self._draw_gear(screen, SCREEN_WIDTH - 200, 200, 50, 8, -0.8, (40, 40, 50))
        self._draw_gear(screen, 100, SCREEN_HEIGHT - 100, 120, 16, 0.3, (40, 40, 50))
        
        # 3. 粒子
        for p in self.particles:
            color = (*p['color'], 100)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
            p['x'] += math.cos(p['angle']) * p['speed']
            p['y'] += math.sin(p['angle']) * p['speed']
            
            if p['x'] < 0: p['x'] = SCREEN_WIDTH
            if p['x'] > SCREEN_WIDTH: p['x'] = 0
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT
            if p['y'] > SCREEN_HEIGHT: p['y'] = 0
        
        # 4. 標題
        title_y = 80
        title_surf = self.title_font.render(self.title, True, (220, 220, 230))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(title_surf, title_rect)
        pygame.draw.line(screen, (100, 100, 150), 
                         (title_rect.left - 20, title_rect.bottom + 5),
                         (title_rect.right + 20, title_rect.bottom + 5), 2)
        
        # 5. 按鈕
        for button in self.buttons:
            button.draw(screen)

    def _draw_gear(self, screen, x, y, radius, teeth, speed, color):
        """繪製簡單的旋轉齒輪"""
        angle_offset = self.animation_time * speed
        
        # 繪製齒
        for i in range(teeth):
            angle = angle_offset + i * (2 * math.pi / teeth)
            
            # 齒的外端
            ox = x + math.cos(angle) * (radius + 15)
            oy = y + math.sin(angle) * (radius + 15)
            # 齒的基部 (簡單用線條表示)
            ix = x + math.cos(angle) * (radius - 5)
            iy = y + math.sin(angle) * (radius - 5)
            
            pygame.draw.line(screen, color, (ix, iy), (ox, oy), 8)
            
        # 齒輪主體
        pygame.draw.circle(screen, color, (x, y), radius)
        # 中心孔
        pygame.draw.circle(screen, (15, 15, 20), (x, y), radius // 3)

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
        if action == "toggle_sound":
            self.sound_enabled = not self.sound_enabled
            # 更新按鈕文本和顏色
            self._init_buttons() 
            # 保持選中狀態
            if self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            return action
            
        if action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.SETTINGS_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.MAIN_MENU)
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
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False