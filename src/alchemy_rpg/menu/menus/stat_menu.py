# src/menu/menus/stat_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import math
import random
from typing import List, Dict, Tuple
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

class StatMenu(AbstractMenu):
    """屬性升級菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options: List[Dict]):
        self.game = game
        self.title = "Core Enhancement"
        self.active = False
        
        self.costs = [cost for cost in range(1, 101, 1)]  # 升級消耗
        self.max_level = 100  # 最大等級
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.info_font = pygame.font.SysFont(None, 28)
        self.btn_font = pygame.font.SysFont(None, 36)
        
        self.message = None
        self.msg_timer = 0
        
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
        """初始化升級按鈕"""
        self.buttons = []
        
        stats = [
            ("attack", "Attack Power", (255, 100, 100)),
            ("defense", "Defense", (100, 150, 255)),
            ("movement", "Agility", (100, 255, 150)),
            ("health", "Max Health", (255, 100, 255))
        ]
        
        start_y = 150
        btn_h = 70
        btn_w = 400
        gap = 30
        center_x = SCREEN_WIDTH // 2
        
        for i, (stat_key, display_name, color) in enumerate(stats):
            y = start_y + i * (btn_h + gap)
            
            # 按鈕文本將在 draw 中動態繪製，這裡留空
            btn = Button(
                center_x - btn_w // 2, y, btn_w, btn_h,
                "", # 動態繪製
                self._create_stat_surface(btn_w, btn_h, color),
                f"upgrade_{stat_key}",
                self.btn_font
            )
            # 存儲額外數據
            btn.stat_key = stat_key
            btn.stat_name = display_name
            btn.base_color = color
            self.buttons.append(btn)
            
        # 返回按鈕
        back_w = 200
        back_y = start_y + len(stats) * (btn_h + gap) + 30
        self.buttons.append(
            Button(
                center_x - back_w // 2, back_y, back_w, 50,
                "Return",
                self._create_button_surface(back_w, 50, (150, 150, 150)),
                "crystal_menu",
                self.header_font
            )
        )

    def _create_stat_surface(self, width, height, base_color):
        s = pygame.Surface((width, height))
        s.fill((30, 30, 40))
        # 邊框
        pygame.draw.rect(s, base_color, (0, 0, width, height), 2)
        return s
        
    def _create_button_surface(self, width, height, base_color):
        s = pygame.Surface((width, height))
        s.fill(base_color)
        # 簡單按鈕樣式
        pygame.draw.rect(s, (255, 255, 255), (0, 0, width, height), 2)
        return s

    def _init_particles(self):
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'color': (255, 255, 255),
                'speed': random.uniform(0.1, 0.5)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((15, 15, 20))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子
        for p in self.particles:
            color = (*p['color'], 50)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            p['y'] -= p['speed']
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT
        
        # 3. 標題與 Mana 顯示
        title_surf = self.title_font.render(self.title, True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title_surf, title_rect)
        
        mana = self.game.storage_manager.mana
        mana_text = self.header_font.render(f"Mana Crystals: {mana}", True, (100, 200, 255))
        mana_rect = mana_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(mana_text, mana_rect)
        
        # 4. 按鈕與信息
        for button in self.buttons:
            # 如果是升級按鈕，動態繪製內容
            if hasattr(button, 'stat_key'):
                self._draw_stat_button_content(screen, button)
            else:
                button.draw(screen)
                
            # 選中光效
            if button.is_selected:
                glow_rect = button.rect.inflate(6, 6)
                pygame.draw.rect(screen, (255, 255, 255), glow_rect, 2)
                
        # 5. 消息提示
        if self.message:
            self.msg_timer -= 1
            if self.msg_timer > 0:
                msg_surf = self.btn_font.render(self.message, True, (255, 100, 100))
                msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
                screen.blit(msg_surf, msg_rect)
            else:
                self.message = None

    def _draw_stat_button_content(self, screen, button):
        # 獲取屬性信息
        level = getattr(self.game.storage_manager, f"{button.stat_key}_level", 0)
        cost = self.costs[level] if level < self.max_level else "MAX"
        
        # 繪製背景
        button.draw(screen)
        
        rect = button.rect
        # 圖標/標題
        name_surf = self.header_font.render(button.stat_name, True, button.base_color)
        screen.blit(name_surf, (rect.x + 20, rect.y + 10))
        
        # 等級與花費 (右側)
        if cost == "MAX":
            cost_text = "MAX LEVEL"
            color = (255, 215, 0)
        else:
            cost_text = f"Cost: {cost}"
            color = (200, 200, 200) if self.game.storage_manager.mana >= cost else (255, 100, 100)
            
        lvl_surf = self.info_font.render(f"Lv.{level}", True, (255, 255, 255))
        cost_surf = self.info_font.render(cost_text, True, color)
        
        screen.blit(lvl_surf, (rect.right - 140, rect.y + 10))
        screen.blit(cost_surf, (rect.right - 140, rect.y + 35))
        
        # 進度條 (底部)
        bar_x = rect.x + 20
        bar_y = rect.bottom - 15
        bar_w = rect.width - 180 # 留空給右側文字
        bar_h = 6
        
        # 背景槽
        pygame.draw.rect(screen, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h))
        # 填充
        fill_w = int(bar_w * (level / self.max_level))
        pygame.draw.rect(screen, button.base_color, (bar_x, bar_y, fill_w, bar_h))

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
            # 清除消息 (如果有的話，可以優化體驗)
            pass
            
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
        if action == "crystal_menu":
            self.game.menu_manager.close_menu(MenuNavigation.STAT_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
            return BasicAction.EXIT_MENU
            
        elif action.startswith("upgrade_"):
            stat = action.split("_")[1]
            success, reason = self._upgrade_stat(stat)
            if success:
                print(f"StatMenu: Upgraded {stat} successfully")
                # 播放成功特效? (這裡簡化，僅更新UI)
            else:
                self.message = reason
                self.msg_timer = 60
            return action
            
        return action

    def _upgrade_stat(self, stat: str) -> Tuple[bool, str]:
        current_level = getattr(self.game.storage_manager, f"{stat}_level", 0)
        
        if current_level >= self.max_level:
            return False, "Max level reached"
            
        cost = self.costs[current_level]
        if self.game.storage_manager.mana < cost:
            return False, "Insufficient Mana"
            
        self.game.storage_manager.mana -= cost
        setattr(self.game.storage_manager, f"{stat}_level", current_level + 1)
        self.game.storage_manager.save_to_json()
        self.game.storage_manager.apply_stats_to_player()
        return True, ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self.message = None
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False