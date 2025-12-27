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
    """水晶商店菜單 - 輕量化版"""
    
    def __init__(self, game: 'Game', options: List[Dict] = None):
        """初始化水晶商店菜單"""
        self.game = game
        self.title = "Crystal Repository"
        self.options = options
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.text_font = pygame.font.SysFont(None, 32)
        
        # 視覺效果變數
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
            ("Enhance Stats", "show_stat", (80, 120, 180)),      # 深藍
            ("Amplifiers", "show_amplifier", (120, 80, 180)),    # 深紫
            ("Elemental Tuning", "show_element", (180, 80, 80)), # 深紅
            ("Skill Library", "show_skill_library", (80, 160, 100)) # 深綠
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
            self._create_button_surface(btn_width, btn_height, (100, 100, 100)),
            "back",
            self.header_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建帶有水晶質感的按鈕表面 (簡化版)"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 簡化 1: 直接填充底色，不做逐行漸層
        surface.fill((r, g, b))
        
        # 簡化 2: 簡單的高亮邊框模擬水晶邊緣
        pygame.draw.rect(surface, (
            min(255, int(r * 1.5)), 
            min(255, int(g * 1.5)), 
            min(255, int(b * 1.5))
        ), (0, 0, width, height), 2)
        
        pygame.draw.rect(surface, (
            max(0, int(r * 0.7)), 
            max(0, int(g * 0.7)), 
            max(0, int(b * 0.7))
        ), (2, 2, width-4, height-4), 1)
        
        return surface

    def _init_particles(self):
        """初始化背景粒子 (數量減少)"""
        self.particles = []
        # 簡化 3: 粒子數量減少至 15
        for _ in range(15):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'vy': random.uniform(-0.5, -1.0), 
                'size': random.randint(2, 4),
                'color': random.choice([
                    (150, 200, 255), (200, 150, 255), (255, 150, 150)
                ]),
                'alpha': random.randint(100, 200)
            })

    def _register_menus(self):
        """註冊子菜單 (邏輯不變)"""
        mm = self.game.menu_manager
        # 避免循環導入，使用延遲導入
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
        overlay.fill((10, 15, 20)) 
        overlay.set_alpha(230)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子效果 (簡化版)
        for p in self.particles:
            # 簡化 4: 改用簡單圓形，移除多邊形計算
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], 150), (p['size'], p['size']), p['size'])
            screen.blit(s, (p['x'], p['y']))
            
            # 移動
            p['y'] += p['vy']
            if p['y'] < -10:
                p['y'] = SCREEN_HEIGHT + 10
                p['x'] = random.randint(0, SCREEN_WIDTH)

        # 3. 標題與裝飾
        title_y = 60
        # 簡化 5: 靜態光暈，移除 sin 波運算
        glow_radius = 120
        s = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (30, 50, 80, 40), (glow_radius, glow_radius), glow_radius)
        screen.blit(s, (SCREEN_WIDTH//2 - glow_radius, title_y - glow_radius + 20))
        
        title_surface = self.title_font.render(self.title, True, (220, 240, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        screen.blit(title_surface, title_rect)
        
        # 4. 按鈕
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        """事件處理 (邏輯完全保留)"""
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
        """處理按鈕動作 (邏輯完全保留)"""
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