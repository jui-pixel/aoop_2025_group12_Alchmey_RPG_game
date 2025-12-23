# src/menu/menus/element_choose_menu.py
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

class ElementChooseMenu(AbstractMenu):
    """元素選擇菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options=None):
        self.game = game
        self.title = "Attune Element" # 更具魔法感的標題
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
        """初始化元素選擇按鈕"""
        self.buttons = []
        
        # 獲取已覺醒的元素
        awakened = list(self.game.storage_manager.awakened_elements)
        
        # 元素顏色映射
        elem_colors = {
            'fire': (255, 100, 80), 
            'water': (80, 180, 255), 
            'earth': (160, 120, 80), 
            'wind': (150, 255, 180),
            'light': (255, 255, 200), 
            'dark': (120, 50, 150),
            'none': (150, 150, 150)
        }
        
        # 構建選項列表
        options = ["none"] + awakened
        
        # 佈局計算
        btn_width = 300
        btn_height = 50
        gap = 20
        total_height = len(options) * (btn_height + gap) + 80 # +80 for back button space
        start_y = (SCREEN_HEIGHT - total_height) // 2 + 50
        center_x = SCREEN_WIDTH // 2
        
        # 生成元素按鈕
        for i, elem in enumerate(options):
            y = start_y + i * (btn_height + gap)
            text = "No Element" if elem == "none" else elem.capitalize()
            color = elem_colors.get(elem, (150, 150, 150))
            
            btn = Button(
                center_x - btn_width // 2, y, btn_width, btn_height,
                text,
                self._create_button_surface(btn_width, btn_height, color),
                elem,
                self.header_font
            )
            self.buttons.append(btn)
            
        # 返回按鈕
        back_y = start_y + len(options) * (btn_height + gap) + 10
        back_btn = Button(
            center_x - btn_width // 2, back_y, btn_width, btn_height,
            "Cancel",
            self._create_button_surface(btn_width, btn_height, (200, 100, 100)),
            "back",
            self.header_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建元素風格的按鈕表面"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 漸層背景
        for y in range(height):
            factor = 0.6 + (y / height) * 0.4
            color = (
                min(255, int(r * factor)), 
                min(255, int(g * factor)), 
                min(255, int(b * factor))
            )
            pygame.draw.line(surface, color, (0, y), (width, y))
            
        # 亮邊框
        pygame.draw.rect(surface, (
            min(255, int(r*1.3)), min(255, int(g*1.3)), min(255, int(b*1.3))
        ), (0, 0, width, height), 2)
        
        return surface

    def _init_particles(self):
        """初始化元素粒子"""
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(2, 5),
                'color': random.choice([
                    (255, 100, 100), (100, 100, 255), (100, 255, 100), (255, 255, 100)
                ]),
                'speed': random.uniform(0.5, 2.0),
                'angle': random.uniform(0, math.pi * 2)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景 (半透明黑色)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 10, 15))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子背景
        for p in self.particles:
            color = (*p['color'], 150)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
            # 隨機飄動
            p['x'] += math.cos(p['angle']) * p['speed']
            p['y'] += math.sin(p['angle']) * p['speed']
            
            # 邊界循環
            if p['x'] < 0: p['x'] = SCREEN_WIDTH
            if p['x'] > SCREEN_WIDTH: p['x'] = 0
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT
            if p['y'] > SCREEN_HEIGHT: p['y'] = 0
        
        # 3. 標題
        title_y = 60 + math.sin(self.animation_time) * 5
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, int(title_y)))
        # 光暈
        glow_surf = self.title_font.render(self.title, True, (100, 200, 255))
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
        mm = self.game.menu_manager
        
        if action == "back":
            mm.close_menu(MenuNavigation.ELEMENT_CHOOSE_MENU)
            mm.open_menu(MenuNavigation.ALCHEMY_MENU)
            return BasicAction.EXIT_MENU
        else:
            # 選擇了元素
            alchemy_menu = mm.menus.get(MenuNavigation.ALCHEMY_MENU)
            if alchemy_menu:
                # 設置元素 (none -> untyped, 其他保持原樣)
                alchemy_menu.element = action if action != "none" else "untyped"
            
            mm.close_menu(MenuNavigation.ELEMENT_CHOOSE_MENU)
            mm.open_menu(MenuNavigation.ALCHEMY_MENU)
            return action

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            # 每次激活重新初始化，以防覺醒元素列表更新
            self._init_buttons()
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False