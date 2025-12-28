# src/menu/menus/skill_chain_edit_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import math
import random
from math import ceil
from typing import List, Optional
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.skills.skill import create_skill_from_dict
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

class SkillChainEditMenu(AbstractMenu):
    """技能鏈編輯菜單 - 優化版"""
    
    def __init__(self, game: 'Game', chain_idx: int, options=None):
        self.game = game
        self.chain_idx = chain_idx
        self.options = options
        self.title = f"Chain Configuration I" if chain_idx == 0 else f"Chain Configuration II"
        
        # 初始數據
        self.slots: List[Optional['Skill']] = []
        self._load_current_chain()
        
        self.marked_slot: Optional[int] = None
        self.current_page = 0
        self.skills = self.game.storage_manager.skills_library
        self.skills_per_page = 6 # 調整每頁顯示數量以適應新佈局
        self.total_pages = ceil(len(self.skills) / self.skills_per_page) if self.skills else 1
        
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.item_font = pygame.font.SysFont(None, 32)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        
        # 初始化
        self._update_buttons()
        self._init_particles()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _load_current_chain(self):
        """重新加載當前技能鏈數據"""
        player = self.game.entity_manager.get_player_component()
        if player and player.skill_chain:
            # 確保索引正確
            if 0 <= self.chain_idx < len(player.skill_chain):
                self.slots = player.skill_chain[self.chain_idx][:]
                # 補齊空位至8個
                self.slots += [None] * (8 - len(self.slots))
            else:
                self.slots = [None] * 8
        else:
            self.slots = [None] * 8

    def _update_buttons(self):
        """更新所有按鈕 (插槽 + 技能庫)"""
        self.buttons = []
        
        # 1. 技能鏈插槽 (中心左側)
        # 8個插槽排成兩列
        slot_w = 200
        slot_h = 50
        start_x = 100
        start_y = 150
        gap_y = 60
        gap_x = 220
        
        for i in range(8):
            col = i // 4
            row = i % 4
            
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            
            skill_name = self.slots[i].name if self.slots[i] else "Empty Slot"
            is_marked = (self.marked_slot == i)
            
            # 根據是否有技能顯示不同顏色
            color = (100, 200, 255) if self.slots[i] else (60, 60, 70) 
            if is_marked:
                color = (255, 200, 50) # 高亮選中
                
            btn = Button(
                x, y, slot_w, slot_h,
                skill_name,
                self._create_slot_surface(slot_w, slot_h, color, is_marked),
                f"mark_slot_{i}",
                self.item_font
            )
            self.buttons.append(btn)

        # 2. 技能庫 (右側面板)
        lib_start_x = SCREEN_WIDTH - 350
        lib_start_y = 150
        lib_w = 280
        
        # 頁碼標題 (非按鈕)
        # 這裡我們不繪製它，而是在draw中繪製文字
        
        start_idx = self.current_page * self.skills_per_page
        end_idx = min(start_idx + self.skills_per_page, len(self.skills))
        
        for i, idx in enumerate(range(start_idx, end_idx)):
            skill_dict = self.skills[idx]
            y = lib_start_y + i * 60
            
            btn = Button(
                lib_start_x, y, lib_w, 50,
                skill_dict['name'],
                self._create_button_surface(lib_w, 50, (100, 150, 100)),
                f"assign_skill_{idx}",
                self.item_font
            )
            self.buttons.append(btn)
            
        # 翻頁按鈕
        nav_y = lib_start_y + self.skills_per_page * 60 + 20
        
        if self.current_page > 0:
            prev_btn = Button(
                lib_start_x, nav_y, 100, 40,
                "< Prev",
                self._create_button_surface(100, 40, (100, 100, 150)),
                "previous",
                self.item_font
            )
            self.buttons.append(prev_btn)
            
        if self.current_page < self.total_pages - 1:
            next_btn = Button(
                lib_start_x + lib_w - 100, nav_y, 100, 40,
                "Next >",
                self._create_button_surface(100, 40, (100, 100, 150)),
                "next",
                self.item_font
            )
            self.buttons.append(next_btn)

        # 3. 完成按鈕 (底部)
        finish_btn = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50,
            "Save & Return",
            self._create_button_surface(200, 50, (100, 200, 100)),
            "skill_chain_menu",
            self.header_font
        )
        self.buttons.append(finish_btn)

    def _create_slot_surface(self, width, height, color, is_marked):
        s = pygame.Surface((width, height))
        s.fill((20, 20, 25))
        
        border_color = color
        if is_marked:
            # 閃爍效果由 draw 階段的額外繪製負責，這裡是靜態
            border_color = (255, 255, 200)
            
        pygame.draw.rect(s, border_color, (0, 0, width, height), 2)
        
        # 連結點裝飾
        pygame.draw.circle(s, border_color, (width, height//2), 3)
        if not is_marked:
             # 微弱的填充
             pass 
        return s

    def _create_button_surface(self, width, height, base_color):
        s = pygame.Surface((width, height))
        r, g, b = base_color
        # 玻璃質感
        s.fill((int(r*0.2), int(g*0.2), int(b*0.2)))
        pygame.draw.line(s, (255, 255, 255), (0, 0), (width, 0)) # 高光
        pygame.draw.rect(s, base_color, (0, 0, width, height), 1)
        return s

    def _init_particles(self):
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'color': (150, 200, 255),
                'speed': random.uniform(0.1, 0.5)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 15, 20))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 連結線效果 (在插槽之間繪製)
        start_x = 100
        start_y = 150
        gap_y = 60
        gap_x = 220
        slot_w = 200
        slot_h = 50
        
        # 垂直連接 (0->1->2->3)
        for i in range(3):
            sx = start_x + slot_w // 2
            sy = start_y + i * gap_y + slot_h
            ex = sx
            ey = start_y + (i+1) * gap_y
            pygame.draw.line(screen, (50, 100, 150), (sx, sy), (ex, ey), 2)
            
        # 第二列垂直連接
        for i in range(3):
            sx = start_x + gap_x + slot_w // 2
            sy = start_y + i * gap_y + slot_h
            ex = sx
            ey = start_y + (i+1) * gap_y
            pygame.draw.line(screen, (50, 100, 150), (sx, sy), (ex, ey), 2)
            
        # 列間連接 (3 -> 4)
        c1 = (start_x + slot_w // 2, start_y + 3 * gap_y + slot_h)
        c2 = (start_x + gap_x + slot_w // 2, start_y)
        # 用曲線或直線連接
        pygame.draw.line(screen, (100, 150, 200), c1, c2, 1)

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
        
        # 面板標題
        slot_header = self.header_font.render("Chain Sequence", True, (150, 200, 255))
        screen.blit(slot_header, (start_x, 100))
        
        lib_header = self.header_font.render(f"Library (Pg {self.current_page+1}/{self.total_pages})", True, (150, 255, 150))
        screen.blit(lib_header, (SCREEN_WIDTH - 350, 100))
        
        # 5. 按鈕
        for button in self.buttons:
            button.draw(screen)
            
            # 如果是選中的插槽，繪製額外的高亮框
            if button.action.startswith("mark_slot_") and self.marked_slot is not None:
                idx = int(button.action.split("_")[2])
                if idx == self.marked_slot:
                    glow_rect = button.rect.inflate(10, 10)
                    pygame.draw.rect(screen, (255, 200, 50), glow_rect, 2)
                    
            # 鼠標懸停選中框
            if button.is_selected:
                 pygame.draw.rect(screen, (255, 255, 255), button.rect, 2)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._save_chain()
            self.game.menu_manager.close_menu(MenuNavigation.SKILL_CHAIN_EDIT_MENU)
            return BasicAction.EXIT_MENU
            
        # 中鍵清除
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:
                for button in self.buttons:
                    if button.rect.collidepoint(event.pos) and button.action.startswith("mark_slot_"):
                        slot_idx = int(button.action.split("_")[2])
                        self.slots[slot_idx] = None
                        self._update_buttons() # 刷新顯示
                        return "clear_slot"
                        
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
                if action.startswith("mark_slot_"):
                    self.marked_slot = int(action.split("_")[2])
                    self._update_buttons() # 更新按鈕外觀(選中狀態)
                    return "mark_slot"
                    
                elif action.startswith("assign_skill_"):
                    skill_idx = int(action.split("_")[2])
                    if self.marked_slot is not None:
                        skill_dict = self.skills[skill_idx]
                        self.slots[self.marked_slot] = create_skill_from_dict(skill_dict)
                        self.marked_slot = None # 分配後取消選中
                        self._update_buttons() # 刷新顯示
                        return "assign_skill"
                        
                elif action in ["previous", "next"]:
                    if action == "previous" and self.current_page > 0:
                        self.current_page -= 1
                    elif action == "next" and self.current_page < self.total_pages - 1:
                        self.current_page += 1
                    self.selected_index = 0
                    self._update_buttons()
                    return action
                    
                elif action == "skill_chain_menu":
                    self._save_chain()
                    self.game.menu_manager.close_menu(MenuNavigation.SKILL_CHAIN_EDIT_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.SKILL_CHAIN_MENU)
                    return BasicAction.EXIT_MENU
                    
        return ""

    def _save_chain(self):
        """保存編輯後的技能鏈"""
        # 去除None並保存
        final_slots = [s for s in self.slots if s is not None]
        player = self.game.entity_manager.get_player_component()
        if player:
            player.skill_chain[self.chain_idx] = final_slots
            player.current_skill_idx = 0
            print(f"Saved chain {self.chain_idx}: {len(final_slots)} skills")

    def update_slots_for_chain(self, chain_idx: int) -> None:
        """更新當前編輯的鏈索引並重載數據"""
        self.chain_idx = chain_idx
        self.title = f"Chain Configuration I" if chain_idx == 0 else f"Chain Configuration II"
        self._load_current_chain()
        self._update_buttons()

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self._update_total_pages() # 確保頁數正確
            self._update_buttons()
            if 0 <= self.selected_index < len(self.buttons):
                self.selected_index = 0
                self.buttons[self.selected_index].is_selected = True
            
            # 重置
            self.marked_slot = None
            self.current_page = 0 
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = 0
                
    def _update_total_pages(self):
        self.skills = self.game.storage_manager.skills_library
        self.total_pages = ceil(len(self.skills) / self.skills_per_page) if self.skills else 1