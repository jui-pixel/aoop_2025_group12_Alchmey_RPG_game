# src/menu/menus/skill_chain_menu.py
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

class SkillChainMenu(AbstractMenu):
    """技能鏈選擇菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options=None):
        self.game = game
        self.title = "Skill Matrix"
        self.options = options
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.btn_font = pygame.font.SysFont(None, 32)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        
        # 註冊依賴
        self._register_menus()
        
        # 初始化
        self._update_buttons()
        self._init_particles()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _register_menus(self):
        # 確保 SkillChainEditMenu 已註冊
        if not self.game.menu_manager.menus.get(MenuNavigation.SKILL_CHAIN_EDIT_MENU):
            from src.menu.menus.skill_chain_edit_menu import SkillChainEditMenu
            # 默認鏈 0
            self.game.menu_manager.register_menu(MenuNavigation.SKILL_CHAIN_EDIT_MENU, SkillChainEditMenu(self.game, 0))

    def _update_buttons(self):
        """更新按鈕 (3x3 網格)"""
        self.buttons = []
        
        grid_start_x = SCREEN_WIDTH // 2 - 200
        grid_start_y = 150
        cell_w = 120
        cell_h = 60
        gap_x = 40
        gap_y = 40
        
        for i in range(9):
            row = i // 3
            col = i % 3
            
            x = grid_start_x + col * (cell_w + gap_x)
            y = grid_start_y + row * (cell_h + gap_y)
            
            # 檢查該鏈是否有技能
            has_skills = False
            player = self.game.entity_manager.get_player_component()
            if player and i < len(player.skill_chain):
                if any(player.skill_chain[i]): # 如果鏈中有非 None 的技能
                    has_skills = True
            
            color = (100, 200, 255) if has_skills else (80, 80, 90)
            text = f"Chain {i+1}"
            
            self.buttons.append(
                Button(
                    x, y, cell_w, cell_h,
                    text,
                    self._create_button_surface(cell_w, cell_h, color, has_skills),
                    f"edit_chain_{i}",
                    self.btn_font
                )
            )
            
        # 完成/返回按鈕
        back_w = 200
        self.buttons.append(
            Button(
                SCREEN_WIDTH // 2 - back_w // 2, SCREEN_HEIGHT - 100, back_w, 50,
                "Close Matrix",
                self._create_button_surface(back_w, 50, (200, 100, 100), True),
                "close",
                self.header_font
            )
        )

    def _create_button_surface(self, width, height, base_color, active_style=False):
        s = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 科技/插槽風格
        s.fill((30, 30, 40))
        
        if active_style:
            # 激活樣式 (高亮邊框)
            pygame.draw.rect(s, base_color, (0, 0, width, height), 2)
            # 內部填充
            fill = pygame.Surface((width-4, height-4))
            fill.fill(base_color)
            fill.set_alpha(50)
            s.blit(fill, (2, 2))
        else:
            # 未激活樣式 (暗淡)
            pygame.draw.rect(s, (60, 60, 70), (0, 0, width, height), 2)
            
        # 角落裝飾
        corner_len = 6
        pygame.draw.line(s, (255, 255, 255), (0, 0), (corner_len, 0))
        pygame.draw.line(s, (255, 255, 255), (0, 0), (0, corner_len))
        
        return s

    def _init_particles(self):
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'color': (100, 200, 255),
                'speed': random.uniform(0.2, 0.8)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((5, 10, 15))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 網格背景裝飾
        grid_color = (30, 40, 50)
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(screen, grid_color, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(screen, grid_color, (0, y), (SCREEN_WIDTH, y))
            
        # 3. 粒子
        for p in self.particles:
            color = (*p['color'], 100)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            p['y'] -= p['speed']
            if p['y'] < 0: p['y'] = SCREEN_WIDTH
            
        # 4. 標題
        title_surf = self.title_font.render(self.title, True, (200, 220, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title_surf, title_rect)
        
        # 5. 按鈕
        for button in self.buttons:
            button.draw(screen)
            
            # 額外選中效果
            if button.is_selected:
                glow_rect = button.rect.inflate(8, 8)
                pygame.draw.rect(screen, (255, 255, 255), glow_rect, 1)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.menu_manager.close_menu(MenuNavigation.SKILL_CHAIN_MENU)
                return BasicAction.EXIT_MENU
                
            # 網格導航
            # 3x3 網格 (索引 0-8) + 1 個底部按鈕 (索引 9)
            if event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                if self.selected_index == 9: # 從底部按鈕向上
                    self.selected_index = 7 # 回到中間列最下
                elif self.selected_index >= 3:
                     self.selected_index -= 3
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                if self.selected_index < 6:
                    self.selected_index += 3
                else:
                    self.selected_index = 9 # 去到底部按鈕
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_LEFT:
                self.buttons[self.selected_index].is_selected = False
                if self.selected_index < 9: # 網格內
                    if self.selected_index % 3 > 0:
                        self.selected_index -= 1
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_RIGHT:
                self.buttons[self.selected_index].is_selected = False
                if self.selected_index < 9: # 網格內
                    if self.selected_index % 3 < 2:
                        self.selected_index += 1
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_RETURN:
                return self._process_action(self.buttons[self.selected_index].action)
                
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        self.buttons[self.selected_index].is_selected = True
                    break
                    
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
                
        return ""
        
    def _process_action(self, action: str) -> str:
        if action.startswith("edit_chain_"):
            chain_idx = int(action.split("_")[2])
            menu = self.game.menu_manager.menus.get(MenuNavigation.SKILL_CHAIN_EDIT_MENU)
            if menu:
                menu.update_slots_for_chain(chain_idx)
                self.game.menu_manager.open_menu(MenuNavigation.SKILL_CHAIN_EDIT_MENU)
                return f"edit_chain_{chain_idx}"
        elif action == "close":
            self.game.menu_manager.close_menu(MenuNavigation.SKILL_CHAIN_MENU)
            return BasicAction.EXIT_MENU
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self._update_buttons()
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False