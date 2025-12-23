# src/menu/menus/crystal_menu.py
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

class CrystalMenu(AbstractMenu):
    """水晶商店菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options: List[Dict] = None):
        """初始化水晶商店菜單"""
        self.game = game
        self.title = "Crystal Repository" # 更具魔法感的標題
        self.options = options
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.text_font = pygame.font.SysFont(None, 32)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        
        # 初始化按鈕
        self._init_buttons()
        # 註冊依賴的菜單
        self._register_menus()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True
            
        self._init_particles()

    def _init_buttons(self):
        """初始化按鈕位置與樣式"""
        btn_width = 300
        btn_height = 60
        gap = 25
        start_y = 180
        center_x = SCREEN_WIDTH // 2
        
        # 定義選單項
        menu_items = [
            ("Enhance Stats", "show_stat", (100, 200, 255)),     # 藍色: 屬性
            ("Amplifiers", "show_amplifier", (200, 100, 255)),   # 紫色: 增幅
            ("Elemental Tuning", "show_element", (255, 100, 100)),# 紅色: 元素
            ("Skill Library", "show_skill_library", (100, 255, 150)) # 綠色: 技能庫
        ]
        
        self.buttons = []
        
        # 主要功能按鈕
        for i, (text, action, color) in enumerate(menu_items):
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
            "Leave Repository",
            self._create_button_surface(btn_width, btn_height, (150, 150, 150)),
            "back",
            self.header_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建帶有水晶質感的按鈕表面"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 漸層填充
        for y in range(height):
            factor = 0.8 + (y / height) * 0.4
            color = (
                min(255, int(r * factor * 0.4)), 
                min(255, int(g * factor * 0.4)), 
                min(255, int(b * factor * 0.4))
            )
            pygame.draw.line(surface, color, (0, y), (width, y))
            
        # 內部邊框
        pygame.draw.rect(surface, (
            min(255, int(r*1.2)), min(255, int(g*1.2)), min(255, int(b*1.2))
        ), (2, 2, width-4, height-4), 1)
        
        # 外邊框
        pygame.draw.rect(surface, (
            min(255, int(r*0.6)), min(255, int(g*0.6)), min(255, int(b*0.6))
        ), (0, 0, width, height), 2)
        
        return surface

    def _init_particles(self):
        """初始化懸浮水晶粒子"""
        self.particles = []
        for _ in range(25):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'vy': random.uniform(-0.5, -1.5), # 向上浮動
                'size': random.randint(2, 6),
                'color': random.choice([
                    (150, 200, 255), (200, 150, 255), (255, 150, 150), (150, 255, 150)
                ]),
                'alpha': random.randint(50, 180)
            })

    def _register_menus(self):
        """註冊子菜單"""
        mm = self.game.menu_manager
        if not mm.menus.get(MenuNavigation.STAT_MENU):
            from src.menu.menus.stat_menu import StatMenu
            mm.register_menu(MenuNavigation.STAT_MENU, StatMenu(self.game, None))
        if not mm.menus.get(MenuNavigation.AMPLIFIER_MENU):
            from src.menu.menus.amplifier_menu import AmplifierMenu
            mm.register_menu(MenuNavigation.AMPLIFIER_MENU, AmplifierMenu(self.game, None))
        if not mm.menus.get(MenuNavigation.ELEMENT_MENU):
            from src.menu.menus.element_menu import ElementMenu
            mm.register_menu(MenuNavigation.ELEMENT_MENU, ElementMenu(self.game, None))
        if not mm.menus.get(MenuNavigation.SKILL_LIBRARY_MENU):
            from src.menu.menus.skill_library_menu import SkillLibraryMenu
            mm.register_menu(MenuNavigation.SKILL_LIBRARY_MENU, SkillLibraryMenu(self.game, None))

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 15, 20)) # 深青色背景
        overlay.set_alpha(230)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子效果
        for p in self.particles:
            alpha = int(p['alpha'] + 50 * math.sin(self.animation_time + p['x']))
            color = (*p['color'], max(0, min(255, alpha)))
            
            # 使用多邊形繪製類似水晶的形狀
            points = [
                (p['x'], p['y'] - p['size']),
                (p['x'] + p['size']*0.8, p['y']),
                (p['x'], p['y'] + p['size']),
                (p['x'] - p['size']*0.8, p['y'])
            ]
            
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, color, points)
            screen.blit(s, (0, 0))
            
            # 移動
            p['y'] += p['vy']
            if p['y'] < -10:
                p['y'] = SCREEN_HEIGHT + 10
                p['x'] = random.randint(0, SCREEN_WIDTH)

        # 3. 標題與裝飾
        title_y = 60
        # 標題背景光暈
        glow_radius = 150 + 20 * math.sin(self.animation_time)
        s = pygame.Surface((int(glow_radius*2), int(glow_radius*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (30, 50, 80, 50), (int(glow_radius), int(glow_radius)), int(glow_radius))
        screen.blit(s, (SCREEN_WIDTH//2 - glow_radius, title_y - glow_radius + 20))
        
        title_surface = self.title_font.render(self.title, True, (220, 240, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(title_surface, title_rect)
        
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
        mm = self.game.menu_manager
        
        if action == "back":
            mm.close_menu(MenuNavigation.CRYSTAL_MENU)
            return BasicAction.EXIT_MENU
        elif action == "show_stat":
            mm.open_menu(MenuNavigation.STAT_MENU)
            return action
        elif action == "show_amplifier":
            mm.open_menu(MenuNavigation.AMPLIFIER_MENU)
            return action
        elif action == "show_element":
            mm.open_menu(MenuNavigation.ELEMENT_MENU)
            return action
        elif action == "show_skill_library":
            mm.open_menu(MenuNavigation.SKILL_LIBRARY_MENU)
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