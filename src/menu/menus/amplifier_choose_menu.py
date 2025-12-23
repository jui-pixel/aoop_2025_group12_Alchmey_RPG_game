# src/menu/menus/amplifier_choose_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import math
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
from typing import List, Dict, Optional

class AmplifierChooseMenu(AbstractMenu):
    """增幅器選擇菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options=None):
        self.game = game
        self.title = "Enhance Power" # 更具魔法感的標題
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.text_font = pygame.font.SysFont(None, 36)
        
        # 數據
        self.amplifier_names = []  
        self.capped = {'elebuff': 1, 'remove_element': 1, 'remove_counter': 1}
        
        # UI 組件
        self.buttons = []
        self.scroll_offset = 0
        self.animation_time = 0
        
        # 返回按鈕
        self.back_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50, 
            "Done", 
            self._create_button_surface(200, 50, (100, 200, 100)), 
            "back", 
            self.header_font
        )
        self.buttons.append(self.back_button)

    def _create_button_surface(self, width, height, color=(50, 50, 80)):
        """創建按鈕表面"""
        surface = pygame.Surface((width, height))
        surface.fill(color)
        pygame.draw.rect(surface, (200, 200, 255), (0, 0, width, height), 2)
        return surface

    def update_amplifiers(self):
        """根據主材料更新可選增幅器"""
        mm = self.game.menu_manager
        alchemy_menu = mm.menus.get(MenuNavigation.ALCHEMY_MENU)
        
        if not alchemy_menu:
             # 安全回退
            self.amplifier_names = []
            return
            
        main = alchemy_menu.main_material
        if main == "missile":
            self.amplifier_names = [
                'damage_level', 'penetration_level', 'elebuff_level',
                'explosion_level', 'speed_level'
            ]
        elif main == "shield":
            self.amplifier_names = [
                'element_resistance_level', 'remove_element_level', 
                'counter_element_resistance_level', 'remove_counter_level',
                'duration_level', 'shield_level'
            ]
        elif main == "step":
            self.amplifier_names = [
                'avoid_level', 'speed_level', 'duration_level'
            ]
        else:
            self.amplifier_names = []
            
        # 重置按鈕佈局（如果需要針對不同數量調整）

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 繪製背景 (半透明深色)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((15, 15, 30))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 標題
        title_surf = self.title_font.render(self.title, True, (200, 200, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title_surf, title_rect)
        
        # 3. 繪製增幅器列表
        alchemy_menu = self.game.menu_manager.menus.get(MenuNavigation.ALCHEMY_MENU)
        if not alchemy_menu: 
            return

        start_y = 150
        item_height = 70
        width = 500
        center_x = SCREEN_WIDTH // 2
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, name in enumerate(self.amplifier_names):
            y = start_y + i * item_height
            
            # 背景條
            bg_rect = pygame.Rect(center_x - width//2, y, width, 50)
            
            # 滑鼠懸停效果
            if bg_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (50, 50, 100), bg_rect, border_radius=10)
                pygame.draw.rect(screen, (100, 100, 200), bg_rect, 2, border_radius=10)
            else:
                pygame.draw.rect(screen, (30, 30, 50), bg_rect, border_radius=10)
                pygame.draw.rect(screen, (60, 60, 80), bg_rect, 1, border_radius=10)
            
            # 名稱
            clean_name = name.replace('_level', '').capitalize()
            name_surf = self.header_font.render(clean_name, True, (220, 220, 220))
            screen.blit(name_surf, (bg_rect.left + 20, bg_rect.centery - name_surf.get_height()//2))
            
            # 數值控制
            current_level = alchemy_menu.amplifier_levels.get(name, 0)
            is_capped = name.replace('_level', '') in self.capped and current_level >= self.capped[name.replace('_level', '')]
            
            level_text = f"{current_level}"
            if is_capped:
                level_text += " (MAX)"
                val_color = (255, 200, 100)
            else:
                val_color = (150, 255, 150) if current_level > 0 else (100, 100, 100)
                
            val_surf = self.header_font.render(level_text, True, val_color)
            val_rect = val_surf.get_rect(midright=(bg_rect.right - 20, bg_rect.centery))
            screen.blit(val_surf, val_rect)
            
            # 簡單的操作提示
            hint_surf = self.text_font.render("[L-Click: +]  [R-Click: -]", True, (80, 80, 120))
            # 只有懸停時顯示提示
            if bg_rect.collidepoint(mouse_pos):
                screen.blit(hint_surf, (bg_rect.right + 20, bg_rect.centery - hint_surf.get_height()//2))

        # 4. 背部按鈕
        self.back_button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        alchemy_menu = self.game.menu_manager.menus.get(MenuNavigation.ALCHEMY_MENU)
        if not alchemy_menu: return ""

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 檢查是否點擊了增幅器條目
            start_y = 150
            item_height = 70
            width = 500
            center_x = SCREEN_WIDTH // 2
            
            for i, name in enumerate(self.amplifier_names):
                y = start_y + i * item_height
                rect = pygame.Rect(center_x - width//2, y, width, 50)
                
                if rect.collidepoint(event.pos):
                    # 左鍵增加
                    if event.button == 1: 
                        current = alchemy_menu.amplifier_levels.get(name, 0)
                        # 檢查上限
                        limit = self.capped.get(name.replace('_level', ''), 999)
                        if current < limit:
                            alchemy_menu.amplifier_levels[name] = current + 1
                            
                    # 右鍵減少
                    elif event.button == 3:
                        current = alchemy_menu.amplifier_levels.get(name, 0)
                        if current > 0:
                            alchemy_menu.amplifier_levels[name] = current - 1
                            if alchemy_menu.amplifier_levels[name] == 0:
                                del alchemy_menu.amplifier_levels[name]
                    return ""

        # 處理按鈕
        active, action = self.back_button.handle_event(event)
        if active and action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_CHOOSE_MENU)
            # 確保返回時打開 alchemy menu
            self.game.menu_manager.open_menu(MenuNavigation.ALCHEMY_MENU)
            return BasicAction.EXIT_MENU
            
        # 鍵盤 ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_CHOOSE_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.ALCHEMY_MENU)
            return BasicAction.EXIT_MENU
            
        return ""

    def get_selected_action(self) -> str:
        return ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            # 每次激活時刷新列表（如果需要）
            self.update_amplifiers()