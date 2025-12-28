# src/menu/menus/skill_library_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import math
import random
from math import ceil
from typing import List, Dict, Tuple
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

class SkillLibraryMenu(AbstractMenu):
    """技能圖書館菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options: List[Dict]):
        self.game = game
        self.title = "Arcane Library"
        self.active = False
        
        self.skills_per_page = 10 # 增加每頁顯示數量
        self.current_page = 0
        self.skills = [] # 在 activate 時更新
        self.total_pages = 1
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.item_font = pygame.font.SysFont(None, 32)
        self.desc_font = pygame.font.SysFont(None, 28)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        self.selected_description = None
        
        # 初始化
        self.buttons = []
        self._init_particles()
        
        self.selected_index = 0
        
    def _update_buttons(self):
        """更新技能列表按鈕"""
        self.buttons = []
        self.skills = self.game.storage_manager.skills_library if self.game.storage_manager.skills_library else []
        self.total_pages = ceil(len(self.skills) / self.skills_per_page) if self.skills else 1
        
        start_idx = self.current_page * self.skills_per_page
        end_idx = min(start_idx + self.skills_per_page, len(self.skills))
        
        # 左右兩列佈局
        left_x = 100
        right_x = SCREEN_WIDTH // 2 + 20
        start_y = 150
        btn_w = 350
        btn_h = 45
        gap_y = 10
        
        for i, idx in enumerate(range(start_idx, end_idx)):
            skill = self.skills[idx]
            
            col = i % 2
            row = i // 2
            
            x = left_x if col == 0 else right_x
            y = start_y + row * (btn_h + gap_y)
            
            btn = Button(
                x, y, btn_w, btn_h,
                skill['name'],
                self._create_button_surface(btn_w, btn_h, (100, 150, 200)),
                f"skill_{idx}",
                self.item_font
            )
            self.buttons.append(btn)
            
        # 翻頁按鈕
        nav_y = start_y + 5 * (btn_h + gap_y) + 20
        nav_w = 120
        
        if self.current_page > 0:
            self.buttons.append(
                Button(
                    SCREEN_WIDTH // 2 - nav_w - 20, nav_y, nav_w, 40,
                    "< Previous",
                    self._create_button_surface(nav_w, 40, (150, 150, 100)),
                    "previous",
                    self.item_font
                )
            )
            
        if self.current_page < self.total_pages - 1:
            self.buttons.append(
                Button(
                    SCREEN_WIDTH // 2 + 20, nav_y, nav_w, 40,
                    "Next >",
                    self._create_button_surface(nav_w, 40, (150, 150, 100)),
                    "next",
                    self.item_font
                )
            )
            
        # 返回按鈕
        back_w = 200
        self.buttons.append(
            Button(
                SCREEN_WIDTH // 2 - back_w // 2, SCREEN_HEIGHT - 80, back_w, 50,
                "Close Library",
                self._create_button_surface(back_w, 50, (200, 100, 100)),
                "crystal_menu",
                self.header_font
            )
        )
        
        # 確保選中索引有效
        if self.selected_index >= len(self.buttons):
            self.selected_index = len(self.buttons) - 1
        elif self.selected_index < 0:
            self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _create_button_surface(self, width, height, base_color):
        s = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 書卷/條目風格
        s.fill((40, 40, 50))
        pygame.draw.rect(s, (60, 60, 70), (0, 0, width, height), 1)
        
        # 左側裝飾條
        pygame.draw.rect(s, base_color, (0, 0, 4, height))
        
        return s

    def _init_particles(self):
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'color': (200, 255, 255),
                'speed': random.uniform(0.2, 0.6)
            })

    def _get_skill_description(self, skill: Dict) -> str:
        desc = f"Name: {skill.get('name', 'Unknown')}\n"
        desc += f"Type: {skill.get('type', 'Unknown')}\n"
        sub_type = skill.get('sub_type')
        if sub_type:
            desc += f"Sub Type: {sub_type}\n"
        desc += f"Element: {skill.get('element', 'Untyped')}\n"
        
        params = skill.get('params', {})
        if params:
            desc += "\nProperties:\n"
            for key, value in params.items():
                if isinstance(value, float):
                    val_str = f"{value:.1f}"
                else:
                    val_str = str(value)
                desc += f"  {key.replace('_', ' ').capitalize()}: {val_str}\n"
        return desc

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.02
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 15, 20))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 裝飾性線條
        pygame.draw.line(screen, (50, 60, 80), (SCREEN_WIDTH//2, 140), (SCREEN_WIDTH//2, SCREEN_HEIGHT-140), 1)
        
        # 3. 粒子
        for p in self.particles:
            color = (*p['color'], 100)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            p['y'] -= p['speed']
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT
            
        # 4. 標題
        title_surf = self.title_font.render(self.title, True, (200, 220, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title_surf, title_rect)
        
        page_surf = self.header_font.render(f"Page {self.current_page+1} / {self.total_pages}", True, (150, 150, 150))
        page_rect = page_surf.get_rect(center=(SCREEN_WIDTH // 2, 110))
        screen.blit(page_surf, page_rect)
        
        # 5. 按鈕
        for button in self.buttons:
            button.draw(screen)
            if button.is_selected:
                pygame.draw.rect(screen, (255, 255, 255), button.rect, 1)

        # 6. 信息框 (當選中技能時顯示詳細描述的懸浮窗)
        if self.selected_description:
            self._draw_description_box(screen)

    def _draw_description_box(self, screen):
        # 創建半透明黑框
        box_w = 400
        box_h = 300
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2
        
        s = pygame.Surface((box_w, box_h))
        s.fill((10, 10, 15))
        s.set_alpha(230)
        screen.blit(s, (box_x, box_y))
        
        # 邊框
        pygame.draw.rect(screen, (100, 150, 200), (box_x, box_y, box_w, box_h), 2)
        
        # 內容
        lines = self.selected_description.split('\n')
        y = box_y + 20
        for line in lines:
            line_surf = self.desc_font.render(line, True, (220, 220, 220))
            screen.blit(line_surf, (box_x + 20, y))
            y += 30

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
        
        # 鍵盤或點擊都會清除描述框 ?? 
        # 優化：如果是按回車查看描述，再按其他鍵才清除？
        # 目前保持：如果是查看描述狀態，按任意鍵關閉描述
        if self.selected_description and event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
            self.selected_description = None
            return "" # 消耗事件
            
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
                # 特殊導航邏輯：如果是雙列
                # 但這裡簡化為簡單列表遍歷
                if self.selected_index > 0:
                    self.selected_index -= 1
                else:
                    self.selected_index = len(self.buttons) - 1
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                if self.selected_index < len(self.buttons) - 1:
                    self.selected_index += 1
                else:
                    self.selected_index = 0
                self.buttons[self.selected_index].is_selected = True
                
            # 左右鍵在雙列佈局中也很有用
            elif event.key == pygame.K_LEFT:
                 # 簡單處理，也可以做更複雜的網格導航
                 pass
            elif event.key == pygame.K_RIGHT:
                 pass
                 
            elif event.key == pygame.K_RETURN:
                return self._process_action(self.buttons[self.selected_index].action)
                
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
                
        return ""
        
    def _process_action(self, action: str) -> str:
        if action == "crystal_menu":
            self.game.menu_manager.close_menu(MenuNavigation.SKILL_LIBRARY_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
            return BasicAction.EXIT_MENU
            
        elif action == "previous":
            if self.current_page > 0:
                self.current_page -= 1
                self._update_buttons()
            return action
            
        elif action == "next":
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self._update_buttons()
            return action
            
        elif action.startswith("skill_"):
            skill_idx = int(action.split("_")[1])
            skill = self.skills[skill_idx]
            self.selected_description = self._get_skill_description(skill)
            return action
            
        return action

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            # 總是確保數據是最新的
            self.current_page = 0
            self._update_buttons()
            if self.buttons:
                self.selected_index = 0
                self.buttons[0].is_selected = True
            
            self.animation_time = 0
            self._init_particles()
            self.selected_description = None
    
    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""