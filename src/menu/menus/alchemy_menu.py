# src/menu/menus/alchemy_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import random
import math
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)
from typing import List, Dict, Optional

class AlchemyMenu(AbstractMenu):
    """煉金（技能合成）菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options = None):
        self.game = game
        self.title = "Arcane Synthesis" # 更具魔法感的標題
        
        # 核心數據
        self.main_material = "missile"
        self.element = "untyped"
        self.amplifier_levels = {}
        self.success_rate = 0
        self.message = ""
        
        # 視覺相關
        self.active = False
        self.animation_time = 0
        self.particles = []
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.text_font = pygame.font.SysFont(None, 32)
        self.small_font = pygame.font.SysFont(None, 24)
        
        # 佈局配置
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2
        
        # 初始化按鈕
        self._init_buttons()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True
            
        self._register_menus()
        self._init_particles()

    def _init_buttons(self):
        """初始化按鈕位置與樣式"""
        btn_width = 220
        btn_height = 50
        margin = 20
        
        # 左側面板按鈕 (材料選擇)
        left_x = 100
        left_start_y = 200
        
        # 右側面板按鈕 (增幅器)
        right_x = SCREEN_WIDTH - 100 - btn_width
        right_start_y = 200
        
        # 底部按鈕
        bottom_y = SCREEN_HEIGHT - 100
        
        self.buttons = [
            # 左側：主要材料與元素
            Button(left_x, left_start_y, btn_width, btn_height, "Select Material", 
                   self._create_button_surface(btn_width, btn_height), "choose_main", self.text_font),
            
            Button(left_x, left_start_y + btn_height + margin, btn_width, btn_height, "Select Element", 
                   self._create_button_surface(btn_width, btn_height), "choose_element", self.text_font),
            
            # 右側：增幅器
            Button(right_x, right_start_y, btn_width, btn_height, "Add Amplifiers", 
                   self._create_button_surface(btn_width, btn_height), "choose_amplifier", self.text_font),
            
            # 底部：合成與返回
            Button(self.center_x - btn_width - 10, bottom_y, btn_width, btn_height, "Synthesize", 
                   self._create_button_surface(btn_width, btn_height, color=(100, 200, 100)), "synthesize", self.text_font),
                   
            Button(self.center_x + 10, bottom_y, btn_width, btn_height, "Back", 
                   self._create_button_surface(btn_width, btn_height, color=(200, 100, 100)), "back", self.text_font)
        ]

    def _create_button_surface(self, width, height, color=(50, 50, 80)):
        """創建按鈕表面"""
        surface = pygame.Surface((width, height))
        surface.fill(color)
        # 繪製邊框
        pygame.draw.rect(surface, (200, 200, 255), (0, 0, width, height), 2)
        return surface

    def _init_particles(self):
        """初始化魔法粒子"""
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': self.center_x + random.randint(-100, 100),
                'y': self.center_y + random.randint(-100, 100),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'size': random.randint(2, 5),
                'color': (random.randint(100, 255), random.randint(100, 255), 255),
                'life': random.randint(50, 200)
            })

    def _register_menus(self):
        """註冊依賴的子菜單"""
        mm = self.game.menu_manager
        if not mm.menus.get(MenuNavigation.MAIN_MATERIAL_MENU):
            from src.menu.menus.main_material_menu import MainMaterialMenu
            mm.register_menu(MenuNavigation.MAIN_MATERIAL_MENU, MainMaterialMenu(self.game, None))
        if not mm.menus.get(MenuNavigation.ELEMENT_CHOOSE_MENU):
            from src.menu.menus.element_choose_menu import ElementChooseMenu
            mm.register_menu(MenuNavigation.ELEMENT_CHOOSE_MENU, ElementChooseMenu(self.game, None))
        if not mm.menus.get(MenuNavigation.AMPLIFIER_CHOOSE_MENU):
            from src.menu.menus.amplifier_choose_menu import AmplifierChooseMenu
            mm.register_menu(MenuNavigation.AMPLIFIER_CHOOSE_MENU, AmplifierChooseMenu(self.game, None))
        if not mm.menus.get(MenuNavigation.NAMING_MENU):
            from src.menu.menus.naming_menu import NamingMenu
            mm.register_menu(MenuNavigation.NAMING_MENU, NamingMenu(self.game, None))

    def calculate_success_rate(self):
        """計算合成成功率 - 保持原有邏輯"""
        num_elements = 1 if self.element != "untyped" else 0
        
        if num_elements > 1:
            self.success_rate = 0
            return
            
        stat_level = 0
        if self.main_material == "missile":
            stat_level = self.game.storage_manager.attack_level
        elif self.main_material == "shield":
            stat_level = self.game.storage_manager.defense_level
        elif self.main_material == "step":
            stat_level = self.game.storage_manager.movement_level
            
        max_cost = stat_level ** 2
        used_cost = sum(self.amplifier_levels.values())
        
        # 基礎成功率公式
        base_rate = (max_cost - used_cost) * 10 + 10
        self.success_rate = max(0, min(100, base_rate))

    def create_skill_dict(self, name):
        """創建技能字典 - 保持原有邏輯"""
        skill_type = None
        sub_type = None
        
        if self.main_material == "missile":
            skill_type = "shooting"
        elif self.main_material == "shield":
            skill_type = "buff"
            sub_type = "shield"
        elif self.main_material == "step":
            skill_type = "buff"
            sub_type = "step"
        else:
            return None
            
        params = {k.replace('_level', ''): v for k, v in self.amplifier_levels.items()}
        
        return {
            'name': name,
            'type': skill_type,
            'sub_type': sub_type,
            'element': self.element,
            'params': params
        }

    def update(self, dt: float) -> None:
        """更新動畫效果"""
        if not self.active:
            return
            
        self.animation_time += dt
        
        # 更新粒子
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            
            # 圍繞中心旋轉
            dx = p['x'] - self.center_x
            dy = p['y'] - self.center_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                # 向心力 + 旋轉力
                p['vx'] += (-dx * 0.005) - (dy * 0.01)
                p['vy'] += (-dy * 0.005) + (dx * 0.01)
            
            if p['life'] <= 0:
                p['x'] = self.center_x + random.uniform(-20, 20)
                p['y'] = self.center_y + random.uniform(-20, 20)
                p['vx'] = random.uniform(-1, 1)
                p['vy'] = random.uniform(-1, 1)
                p['life'] = random.randint(50, 200)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.calculate_success_rate()
        
        # 1. 繪製背景 (深色魔法風格)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 10, 25)) # 深藍黑色
        overlay.set_alpha(230)
        screen.blit(overlay, (0, 0))
        
        # 2. 繪製中心魔法陣/合成區
        # 脈動圓環
        pulse = math.sin(self.animation_time * 2) * 5
        pygame.draw.circle(screen, (50, 50, 100), (self.center_x, self.center_y), 150 + pulse, 2)
        pygame.draw.circle(screen, (30, 30, 80), (self.center_x, self.center_y), 130 - pulse, 1)
        
        # 繪製粒子
        for p in self.particles:
            alpha = min(255, p['life'] * 2)
            color = (*p['color'], alpha)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
        # 3. 繪製標題
        title_surf = self.title_font.render(self.title, True, (200, 200, 255))
        title_rect = title_surf.get_rect(center=(self.center_x, 60))
        screen.blit(title_surf, title_rect)
        
        # 4. 繪製左側信息 (當前選擇)
        left_label_x = 100
        left_val_x = 100
        base_y = 320
        
        # Main Material
        main_label = self.small_font.render("Main Material:", True, (150, 150, 150))
        screen.blit(main_label, (left_label_x, base_y))
        main_val = self.header_font.render(self.main_material.capitalize(), True, (255, 255, 200))
        screen.blit(main_val, (left_val_x, base_y + 25))
        
        # Element
        elem_label = self.small_font.render("Element:", True, (150, 150, 150))
        screen.blit(elem_label, (left_label_x, base_y + 80))
        
        # 根據元素類型改變顏色
        elem_colors = {
            'fire': (255, 100, 100), 'water': (100, 200, 255), 
            'earth': (150, 100, 50), 'wind': (150, 255, 150),
            'light': (255, 255, 200), 'dark': (100, 0, 100),
            'untyped': (200, 200, 200)
        }
        elem_color = elem_colors.get(self.element, (200, 200, 200))
        elem_val = self.header_font.render(self.element.capitalize(), True, elem_color)
        screen.blit(elem_val, (left_val_x, base_y + 105))

        # 5. 繪製右側信息 (增幅器列表)
        right_x = SCREEN_WIDTH - 300
        list_y = 320
        
        amp_title = self.small_font.render("Active Amplifiers:", True, (150, 150, 150))
        screen.blit(amp_title, (right_x, list_y))
        list_y += 30
        
        if not self.amplifier_levels:
            no_amp = self.text_font.render("None", True, (100, 100, 100))
            screen.blit(no_amp, (right_x, list_y))
        else:
            for name, level in self.amplifier_levels.items():
                name_text = name.replace('_level', '').capitalize()
                amp_entry = self.text_font.render(f"- {name_text}: Lv.{level}", True, (200, 255, 255))
                screen.blit(amp_entry, (right_x, list_y))
                list_y += 30
        
        # 6. 中央信息 (成功率與消耗)
        rate_color = (100, 255, 100) if self.success_rate > 50 else (255, 100, 100)
        rate_text = self.header_font.render(f"{int(self.success_rate)}%", True, rate_color)
        rate_label = self.small_font.render("Success Rate", True, (200, 200, 200))
        
        # 居中顯示
        screen.blit(rate_text, rate_text.get_rect(center=(self.center_x, self.center_y)))
        screen.blit(rate_label, rate_label.get_rect(center=(self.center_x, self.center_y + 30)))
        
        # 消耗
        cost_text = self.text_font.render("Cost: 1 Mana", True, (100, 200, 255))
        screen.blit(cost_text, cost_text.get_rect(center=(self.center_x, self.center_y + 70)))

        # 7. 訊息提示 (底部)
        if self.message:
            msg_color = (100, 255, 100) if "Success" in self.message else (255, 100, 100)
            msg_surf = self.text_font.render(self.message, True, msg_color)
            screen.blit(msg_surf, msg_surf.get_rect(center=(self.center_x, SCREEN_HEIGHT - 160)))

        # 8. 繪製按鈕
        for button in self.buttons:
            button.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        # 處理鼠標移動
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    # 只有當選擇改變時才更新，避免不必要的重繪標記
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        self.buttons[self.selected_index].is_selected = True
                    break
        
        # 處理鍵盤導航
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.menu_manager.close_menu(MenuNavigation.ALCHEMY_MENU)
                return BasicAction.EXIT_MENU
                
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
        
        # 處理按鈕點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
                
        return ""

    def _process_action(self, action: str) -> str:
        """統一處理由按鈕或鍵盤觸發的動作"""
        mm = self.game.menu_manager
        
        if action == "back":
            mm.close_menu(MenuNavigation.ALCHEMY_MENU)
            return BasicAction.EXIT_MENU
            
        elif action == "choose_main":
            mm.open_menu(MenuNavigation.MAIN_MATERIAL_MENU)
            return "choose_main"
            
        elif action == "choose_element":
            mm.open_menu(MenuNavigation.ELEMENT_CHOOSE_MENU)
            return "choose_element"
            
        elif action == "choose_amplifier":
            amp_menu = mm.menus.get(MenuNavigation.AMPLIFIER_CHOOSE_MENU)
            if not amp_menu:
                # 應該已經註冊，但為了安全起見
                from src.menu.menus.amplifier_choose_menu import AmplifierChooseMenu
                amp_menu = AmplifierChooseMenu(self.game, None)
                mm.register_menu(MenuNavigation.AMPLIFIER_CHOOSE_MENU, amp_menu)
                
            amp_menu.update_amplifiers()
            mm.open_menu(MenuNavigation.AMPLIFIER_CHOOSE_MENU)
            return "choose_amplifier"
            
        elif action == "synthesize":
            if self.game.storage_manager.mana < 1:
                self.message = "Not enough Mana!"
                return ""
                
            self.game.storage_manager.mana -= 1
            if random.random() * 100 < self.success_rate:
                self.message = "Synthesis Successful!"
                # 簡單的閃光效果或是直接跳轉
                mm.open_menu(MenuNavigation.NAMING_MENU)
            else:
                self.message = "Synthesis Failed..."
                # 可以添加失敗音效或震動效果
            return "synthesize"
            
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            # 重置動畫狀態
            self.animation_time = 0
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False
            
    def reset(self):
        self.main_material = "missile"
        self.element = "untyped"
        self.amplifier_levels = {}
        self.success_rate = 0
        self.message = ""
        
    def set_main_material(self, material: str) -> None:
        self.reset()
        self.main_material = material