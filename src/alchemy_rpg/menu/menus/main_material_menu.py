# src/menu/menus/main_material_menu.py
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

class MainMaterialMenu(AbstractMenu):
    """主素材選擇菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options=None):
        self.game = game
        self.title = "Select Core Material"
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        
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
        """初始化按鈕位置與樣式"""
        self.buttons = []
        
        btn_width = 380
        btn_height = 70
        gap = 30
        
        # 定義選項
        options = [
            ("Attack Core (Magic Missile)", "missile", (255, 100, 100)), # 紅色: 攻擊
            ("Defense Core (Magic Shield)", "shield", (100, 200, 255)),  # 藍色: 防禦
            ("Mobility Core (Magic Step)", "step", (100, 255, 150))      # 綠色: 移動
        ]
        
        total_height = len(options) * (btn_height + gap) + 80
        start_y = (SCREEN_HEIGHT - total_height) // 2 + 60
        center_x = SCREEN_WIDTH // 2
        
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
        back_y = start_y + len(options) * (btn_height + gap) + 10
        back_btn = Button(
            center_x - btn_width // 2, back_y, btn_width, btn_height,
            "Cancel Selection",
            self._create_button_surface(btn_width, btn_height, (150, 150, 150)),
            "back",
            self.header_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建核心質感的按鈕表面"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 1. 深色背景
        surface.fill((20, 20, 30))
        
        # 2. 能量流動效果 (靜態繪製)
        for i in range(0, width, 4):
            factor = math.sin(i * 0.1) * 0.5 + 0.5
            start_color = (
                int(r * 0.2), int(g * 0.2), int(b * 0.2)
            )
            end_color = (
                int(r * 0.5 * factor), int(g * 0.5 * factor), int(b * 0.5 * factor)
            )
            pygame.draw.line(surface, end_color, (i, 0), (i, height), 2)
            
        # 3. 邊框
        pygame.draw.rect(surface, base_color, (0, 0, width, height), 2)
        # 內發光邊框
        pygame.draw.rect(surface, (
            min(255, int(r*0.7)), min(255, int(g*0.7)), min(255, int(b*0.7))
        ), (2, 2, width-4, height-4), 1)
        
        # 4. 角落強化
        corner_len = 8
        pygame.draw.circle(surface, base_color, (4, 4), 3)
        pygame.draw.circle(surface, base_color, (width-5, 4), 3)
        pygame.draw.circle(surface, base_color, (4, height-5), 3)
        pygame.draw.circle(surface, base_color, (width-5, height-5), 3)
        
        return surface

    def _init_particles(self):
        """初始化懸浮粒子"""
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(2, 5),
                'color': random.choice([
                    (255, 100, 100), (100, 100, 255), (100, 255, 100)
                ]),
                'speed': random.uniform(0.5, 1.5),
                'angle': random.uniform(0, math.pi * 2)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景 (科技魔法感)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((5, 10, 20))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子
        for p in self.particles:
            color = (*p['color'], 150)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
            p['x'] += math.cos(p['angle']) * p['speed']
            p['y'] += math.sin(p['angle']) * p['speed']
            
            if p['x'] < 0: p['x'] = SCREEN_WIDTH
            if p['x'] > SCREEN_WIDTH: p['x'] = 0
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT
            if p['y'] > SCREEN_HEIGHT: p['y'] = 0
        
        # 3. 標題
        title_y = 60
        # 簡單的動態標題背景
        w = 400
        h = 60
        bg_rect = pygame.Rect(SCREEN_WIDTH//2 - w//2, title_y - h//2, w, h)
        pygame.draw.line(screen, (100, 150, 255), (bg_rect.left, bg_rect.centery), (bg_rect.right, bg_rect.centery), 1)
        
        title_surf = self.title_font.render(self.title, True, (220, 220, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        # 光暈
        glow_surf = self.title_font.render(self.title, True, (100, 100, 200))
        screen.blit(glow_surf, (title_rect.x + 2, title_rect.y + 2))
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
        mm = self.game.menu_manager
        
        if action == "back":
            mm.close_menu(MenuNavigation.MAIN_MATERIAL_MENU)
            mm.open_menu(MenuNavigation.ALCHEMY_MENU)
            return BasicAction.EXIT_MENU
        else:
            # 選擇了主素材
            alchemy_menu = mm.menus.get(MenuNavigation.ALCHEMY_MENU)
            if alchemy_menu:
                alchemy_menu.set_main_material(action)
                
            mm.close_menu(MenuNavigation.MAIN_MATERIAL_MENU)
            mm.open_menu(MenuNavigation.ALCHEMY_MENU)
            return action

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