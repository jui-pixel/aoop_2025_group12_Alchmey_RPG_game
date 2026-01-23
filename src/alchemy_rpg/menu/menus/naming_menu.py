# src/menu/menus/naming_menu.py
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

class NamingMenu(AbstractMenu):
    """技能命名菜單 - 優化版"""
    
    def __init__(self, game: 'Game', options=None):
        self.game = game
        self.title = "Forging New Spell"
        self.active = False
        
        self.skill_name = ""
        self.message = "Enter the name of your creation"
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.input_font = pygame.font.SysFont(None, 48)
        self.msg_font = pygame.font.SysFont(None, 32)
        self.btn_font = pygame.font.SysFont(None, 36)
        
        # 視覺效果
        self.animation_time = 0
        self.particles = []
        self.cursor_blink = 0
        
        # 初始化按鈕
        self._init_buttons()
        self._init_particles()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _init_buttons(self):
        """初始化按鈕"""
        self.buttons = []
        
        btn_width = 240
        btn_height = 50
        gap = 40
        center_x = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 120
        
        # Confirm Button (Finalize)
        confirm_btn = Button(
            center_x + gap // 2, y, btn_width, btn_height,
            "Finalize Spell",
            self._create_button_surface(btn_width, btn_height, (100, 255, 100)),
            "back_to_lobby",
            self.btn_font
        )
        self.buttons.append(confirm_btn)
        
        # Cancel Button (Back to Alchemy)
        cancel_btn = Button(
            center_x - btn_width - gap // 2, y, btn_width, btn_height,
            "Return to Alchemy",
            self._create_button_surface(btn_width, btn_height, (200, 100, 100)),
            "back_to_alchemy",
            self.btn_font
        )
        self.buttons.append(cancel_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建按鈕表面"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 漸層
        for i in range(height):
            c = (
                max(0, int(r * (1 - i/height * 0.3))),
                max(0, int(g * (1 - i/height * 0.3))),
                max(0, int(b * (1 - i/height * 0.3)))
            )
            pygame.draw.line(surface, c, (0, i), (width, i))
            
        pygame.draw.rect(surface, (200, 200, 200), (0, 0, width, height), 2)
        return surface

    def _init_particles(self):
        """初始化魔法粒子"""
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 4),
                'color': random.choice([(100, 200, 255), (255, 200, 100), (200, 100, 255)]),
                'speed': random.uniform(0.2, 1.0),
                'vy': random.uniform(-0.5, -1.5) # 向上飄
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        self.cursor_blink += 1
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 5, 15))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子
        for p in self.particles:
            color = (*p['color'], 150)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
            p['y'] += p['vy']
            p['x'] += math.sin(self.animation_time + p['y']*0.01) * 0.5
            
            if p['y'] < 0:
                p['y'] = SCREEN_HEIGHT
                p['x'] = random.randint(0, SCREEN_WIDTH)

        # 3. 標題
        title_y = 60
        title_surf = self.title_font.render(self.title, True, (200, 220, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        # 光暈
        glow_surf = self.title_font.render(self.title, True, (100, 100, 255))
        screen.blit(glow_surf, (title_rect.x + 2, title_rect.y + 2))
        screen.blit(title_surf, title_rect)
        
        # 4. 輸入框區域
        center_y = SCREEN_HEIGHT // 2 - 20
        input_width = 500
        input_height = 60
        input_rect = pygame.Rect(
            (SCREEN_WIDTH - input_width) // 2,
            center_y - input_height // 2,
            input_width,
            input_height
        )
        
        # 輸入框背景
        pygame.draw.rect(screen, (30, 30, 50), input_rect)
        pygame.draw.rect(screen, (100, 150, 255), input_rect, 2)
        
        # 輸入文字渲染
        txt_surf = self.input_font.render(self.skill_name, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=input_rect.center)
        screen.blit(txt_surf, txt_rect)
        
        # 光標
        if (self.cursor_blink // 30) % 2 == 0:
            cursor_x = txt_rect.right + 2
            pygame.draw.line(screen, (255, 255, 255), 
                           (cursor_x, txt_rect.top + 5), 
                           (cursor_x, txt_rect.bottom - 5), 2)
                           
        # 提示信息
        msg_color = (255, 100, 100) if "Invalid" in self.message or "Please" in self.message else (150, 200, 255)
        msg_surf = self.msg_font.render(self.message, True, msg_color)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, center_y + 60))
        screen.blit(msg_surf, msg_rect)
        
        # 5. 按鈕
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
            if event.key == pygame.K_ESCAPE:
                self.game.menu_manager.close_menu(MenuNavigation.NAMING_MENU)
                self.game.menu_manager.open_menu(MenuNavigation.ALCHEMY_MENU)
                return BasicAction.EXIT_MENU
                
            elif event.key == pygame.K_RETURN:
                if self.skill_name:
                    return self._try_create_skill()
                else:
                    self.message = "Please enter a skill name"
                    
            elif event.key == pygame.K_BACKSPACE:
                self.skill_name = self.skill_name[:-1]
                
            else:
                # 限制長度
                if len(self.skill_name) < 20:
                    char = event.unicode
                    # 允許字母、數字、空格、下劃線
                    if char.isalnum() or char in ['_', ' ']:
                        self.skill_name += char
                        
        # 按鈕點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action == "back_to_alchemy":
                    self.game.menu_manager.close_menu(MenuNavigation.NAMING_MENU)
                    self.game.menu_manager.open_menu(MenuNavigation.ALCHEMY_MENU)
                    return BasicAction.EXIT_MENU
                elif action == "back_to_lobby":
                    if self.skill_name:
                        return self._try_create_skill()
                    else:
                        self.message = "Please enter a skill name"
                        
        return ""

    def _try_create_skill(self) -> str:
        """嘗試創建技能"""
        alchemy_menu = self.game.menu_manager.menus.get(MenuNavigation.ALCHEMY_MENU)
        if alchemy_menu:
            skill_dict = alchemy_menu.create_skill_dict(self.skill_name)
            if skill_dict:
                self.game.storage_manager.add_skill_to_library(skill_dict)
                self.game.storage_manager.apply_skills_to_player()
                self.game.menu_manager.close_menu(MenuNavigation.NAMING_MENU)
                alchemy_menu.reset()
                self.game.menu_manager.close_all_menus()
                
                print(f"Skill Created: {self.skill_name}")
                return BasicAction.EXIT_MENU
            else:
                self.message = "Invalid skill parameters"
        else:
            self.message = "Alchemy system error (Menu not found)"
        return ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.skill_name = ""
            self.message = "Enter the name of your creation"
            self.animation_time = 0
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""