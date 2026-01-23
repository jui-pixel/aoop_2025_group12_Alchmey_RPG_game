# src/menu/menus/amplifier_stat_menu.py
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

class AmplifierStatMenu(AbstractMenu):
    """增幅器詳細屬性/效果查看菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options: Dict = None):
        self.game = game
        self.amplifier_type = 'magic_missile'
        self.title = "Effect Details"
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 40)
        self.text_font = pygame.font.SysFont(None, 28)
        self.desc_font = pygame.font.SysFont(None, 32)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        
        # 數據與緩存
        self.effect_mapping = []
        self.buttons = []
        self.selected_description = None
        
        # 初始化
        if options and 'type' in options:
            self.update_type(options['type'])
        else:
            self.update_type(self.amplifier_type)
            
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _get_effect_mapping(self, amplifier_type: str) -> List[Tuple[str, str, str]]:
        """獲取增幅器效果數據映射"""
        mapping = {
            "magic_missile": [
                ("Damage Boost", "damage_level", "Increases missile damage by 10 per level."),
                ("Pierce", "penetration_level", "Missiles can pierce through additional enemies."),
                ("Elemental Flux", "elebuff_level", "Enhances elemental damage output significantly."),
                ("Explosion", "explosion_level", "Missiles explode on impact, dealing area damage."),
                ("Velocity", "speed_level", "Increases missile travel speed.")
            ],
            "magic_shield": [
                ("Elemental Res.", "element_resistance_level", "Reduces incoming elemental damage."),
                ("Purification", "remove_element_level", "Chance to cleanse elemental status effects."),
                ("Reflection", "counter_element_resistance_level", "Reflects a portion of elemental damage."),
                ("Ward", "remove_counter_level", "Chance to negate enemy counterattacks."),
                ("Duration", "duration_level", "Extends the shield's active duration."),
                ("Fortitude", "shield_level", "Increases the shield's base health points.")
            ],
            "magic_step": [
                ("Agility", "avoid_level", "Reduces the cooldown of the step skill."),
                ("Haste", "speed_level", "Increases movement speed after stepping."),
                ("Dash Range", "duration_level", "Extends the distance covered by the step.")
            ]
        }
        return mapping.get(amplifier_type, [])

    def _init_buttons(self):
        """初始化按鈕列表"""
        self.buttons = []
        
        start_y = 180
        btn_width = 300
        btn_height = 50
        gap = 15
        center_x = SCREEN_WIDTH // 2
        
        # 效果按鈕
        for i, (effect_name, _, description) in enumerate(self.effect_mapping):
            y = start_y + i * (btn_height + gap)
            btn = Button(
                center_x - btn_width // 2, y, btn_width, btn_height,
                effect_name,
                self._create_button_surface(btn_width, btn_height),
                f"view_{effect_name.lower().replace(' ', '_')}", # Action ID
                self.header_font
            )
            # 存儲描述以便快速訪問，避免再次查找
            btn.description = description 
            self.buttons.append(btn)
            
        # 返回按鈕
        back_y = SCREEN_HEIGHT - 80
        back_btn = Button(
            center_x - btn_width // 2, back_y, btn_width, btn_height,
            "Back",
            self._create_button_surface(btn_width, btn_height, (200, 100, 100)),
            "back",
            self.header_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, color=(60, 60, 90)):
        """創建按鈕表面"""
        surface = pygame.Surface((width, height))
        surface.fill(color)
        pygame.draw.rect(surface, (150, 150, 200), (0, 0, width, height), 2)
        return surface

    def update_type(self, amplifier_type: str) -> None:
        """更新顯示的增幅器類型"""
        self.amplifier_type = amplifier_type
        # 格式化標題: magic_missile -> Magic Missile
        display_name = amplifier_type.replace('_', ' ').title()
        self.title = f"{display_name} Stats"
        
        self.effect_mapping = self._get_effect_mapping(amplifier_type)
        self._init_buttons()
        self.selected_index = 0
        self.selected_description = None
        
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True
            # 默認選中第一個並顯示描述
            self._update_description(0)

    def _update_description(self, index):
        """更新當前選中的描述"""
        if 0 <= index < len(self.buttons):
            btn = self.buttons[index]
            if hasattr(btn, 'description'):
                self.selected_description = btn.description
            else:
                self.selected_description = None

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 20, 30))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 標題
        title_surf = self.title_font.render(self.title, True, (200, 200, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title_surf, title_rect)
        
        # 3. 描述區域 (底部)
        desc_box_y = SCREEN_HEIGHT - 200
        desc_box_height = 100
        desc_box_width = 600
        desc_rect = pygame.Rect((SCREEN_WIDTH - desc_box_width)//2, desc_box_y, desc_box_width, desc_box_height)
        
        # 描述框背景
        pygame.draw.rect(screen, (30, 30, 50), desc_rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 150), desc_rect, 2, border_radius=10)
        
        if self.selected_description:
            # 簡單的自動換行（這裡假設描述不長，直接居中顯示）
            desc_surf = self.desc_font.render(self.selected_description, True, (220, 220, 220))
            desc_text_rect = desc_surf.get_rect(center=desc_rect.center)
            screen.blit(desc_surf, desc_text_rect)
        else:
            hint_surf = self.text_font.render("Select an effect to view details", True, (100, 100, 100))
            screen.blit(hint_surf, hint_surf.get_rect(center=desc_rect.center))

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
                        self._update_description(i)
                    break
                    
        # 鍵盤
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                self._update_description(self.selected_index)
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                self._update_description(self.selected_index)
            elif event.key == pygame.K_RETURN:
                return self._process_action(self.buttons[self.selected_index].action)
                
        # 按鈕點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
                
        return ""
        
    def _process_action(self, action: str) -> str:
        if action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.AMPLIFIER_STAT_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.AMPLIFIER_MENU)
            return BasicAction.EXIT_MENU
        elif action.startswith("view_"):
            # 已經通過懸停/選中顯示了描述，這裡只是可以觸發返回或其他邏輯
            # 在當前邏輯中，查看詳情不需要額外操作，因為描述已經實時顯示
            pass
            
        return ""

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
                self._update_description(self.selected_index)
            self.animation_time = 0
            # 每次激活不一定需要重新初始化按鈕，除非類型改變
            # 但這裡保持簡單，假設 update_type 已經在打開前被調用
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False
            self.selected_description = None 