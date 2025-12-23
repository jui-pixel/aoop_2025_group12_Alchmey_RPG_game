# src/menu/menus/element_menu.py
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

class ElementMenu(AbstractMenu):
    """元素覺醒菜單 - 八芒星佈局優化版"""
    
    def __init__(self, game: 'Game', options: List[Dict] = None):
        self.game = game
        self.title = "Astral Awakening"
        self.active = False
        
        # 元素配置
        self.awaken_cost = 1
        self.octagram_elements = ["metal", "water", "wood", "fire", "earth", "wind", "thunder", "ice"]
        self.special_elements = ["light", "dark"] # 日月
        
        # 視覺參數
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2 + 30
        self.radius = 220
        self.animation_time = 0
        self.particles = []
        self.message = None
        self.msg_timer = 0
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.label_font = pygame.font.SysFont(None, 24)
        self.msg_font = pygame.font.SysFont(None, 32)
        
        self._init_buttons()
        self._init_star_points()
        self._init_particles()
        
        self.selected_index = 0
        if self.buttons:
            self.buttons[self.selected_index].is_selected = True

    def _init_star_points(self):
        """計算八芒星頂點"""
        self.star_points = []
        for i in range(8):
            angle = math.radians(i * 45 - 90) # -90 使其從頂部開始
            x = self.center_x + math.cos(angle) * self.radius
            y = self.center_y + math.sin(angle) * self.radius
            self.star_points.append((x, y))

    def _init_buttons(self):
        """初始化按鈕"""
        self.buttons = []
        awakened = self.game.storage_manager.awakened_elements
        
        # 1. 八芒星元素按鈕
        btn_size = 60
        for i, elem in enumerate(self.octagram_elements):
            angle = math.radians(i * 45 - 90)
            x = self.center_x + math.cos(angle) * self.radius
            y = self.center_y + math.sin(angle) * self.radius
            
            is_unlocked = elem in awakened
            color = self._get_element_color(elem, is_unlocked)
            
            btn = Button(
                int(x - btn_size//2), int(y - btn_size//2), btn_size, btn_size,
                "", # 圓形按鈕不顯示文字在中間，改為繪製時處理或下方標籤
                self._create_circle_surface(btn_size, color, is_unlocked),
                f"awaken_{elem}",
                self.label_font
            )
            # 存儲額外信息以便繪製標籤
            btn.element_name = elem
            self.buttons.append(btn)
            
        # 2. 日月 (光/暗) - 放置在左上和右上角
        sun_pos = (SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT // 2 - 200)
        moon_pos = (SCREEN_WIDTH // 2 + 350, SCREEN_HEIGHT // 2 - 200)
        
        # Light (Sun)
        is_light_unlocked = "light" in awakened
        sun_btn = Button(
            int(sun_pos[0] - 40), int(sun_pos[1] - 40), 80, 80,
            "",
            self._create_celestial_surface(80, (255, 255, 200), is_light_unlocked, "sun"),
            "awaken_light",
            self.label_font
        )
        sun_btn.element_name = "light"
        self.buttons.append(sun_btn)
        
        # Dark (Moon)
        is_dark_unlocked = "dark" in awakened
        moon_btn = Button(
            int(moon_pos[0] - 40), int(moon_pos[1] - 40), 80, 80,
            "",
            self._create_celestial_surface(80, (100, 50, 150), is_dark_unlocked, "moon"),
            "awaken_dark",
            self.label_font
        )
        moon_btn.element_name = "dark"
        self.buttons.append(moon_btn)
        
        # 3. 返回按鈕
        back_w, back_h = 200, 50
        back_btn = Button(
            SCREEN_WIDTH // 2 - back_w // 2, SCREEN_HEIGHT - 80, back_w, back_h,
            "Return",
            self._create_rect_surface(back_w, back_h, (100, 100, 100)),
            "back",
            self.label_font
        )
        self.buttons.append(back_btn)

    def _get_element_color(self, elem, unlocked):
        base_colors = {
            "metal": (192, 192, 192),
            "wood": (50, 200, 50),
            "water": (50, 100, 255),
            "fire": (255, 50, 50),
            "earth": (139, 69, 19),
            "wind": (150, 255, 200),
            "thunder": (255, 255, 50),
            "ice": (100, 255, 255),
            "light": (255, 255, 200),
            "dark": (100, 0, 100)
        }
        color = base_colors.get(elem, (150, 150, 150))
        if not unlocked:
            # 變暗
            return (color[0]//3, color[1]//3, color[2]//3)
        return color

    def _create_circle_surface(self, size, color, unlocked):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        # 外環
        if unlocked:
            pygame.draw.circle(s, (255, 255, 255), (size//2, size//2), size//2, 2)
            pygame.draw.circle(s, color, (size//2, size//2), size//2 - 4)
        else:
            pygame.draw.circle(s, (100, 100, 100), (size//2, size//2), size//2, 1)
            pygame.draw.circle(s, color, (size//2, size//2), size//2 - 2)
        return s
        
    def _create_celestial_surface(self, size, color, unlocked, type_):
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size//2, size//2)
        if unlocked:
            if type_ == "sun":
                # 光芒
                pygame.draw.circle(s, color, center, size//2 - 5)
                # 簡單光刺
                for i in range(8):
                    ang = i * math.pi / 4
                    ex, ey = center[0] + math.cos(ang)*size/2, center[1] + math.sin(ang)*size/2
                    pygame.draw.line(s, color, center, (ex, ey), 2)
            else: # moon
                pygame.draw.circle(s, color, center, size//2 - 2)
                # 陰影造成月牙效果
                pygame.draw.circle(s, (0, 0, 0, 100), (center[0]+10, center[1]-5), size//2 - 5)
        else:
            pygame.draw.circle(s, (50, 50, 50), center, size//2 - 2, 1)
            pygame.draw.circle(s, (color[0]//4, color[1]//4, color[2]//4), center, size//2 - 4)
            
        return s

    def _create_rect_surface(self, w, h, color):
        s = pygame.Surface((w, h))
        s.fill(color)
        pygame.draw.rect(s, (200, 200, 200), (0, 0, w, h), 2)
        return s

    def _init_particles(self):
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'alpha': random.randint(100, 255),
                'speed': random.uniform(0.1, 0.5)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.02
        
        # 1. 宇宙背景
        screen.fill((5, 5, 10))
        
        # 2. 星星粒子
        for p in self.particles:
            color = (255, 255, 255, p['alpha'])
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            p['x'] -= p['speed']
            if p['x'] < 0: p['x'] = SCREEN_WIDTH
            
        # 3. 繪製魔法陣 (八芒星線條)
        # 兩個正方形交錯
        # Square 1: 0-2-4-6-0
        sq1_indices = [0, 2, 4, 6, 0]
        # Square 2: 1-3-5-7-1
        sq2_indices = [1, 3, 5, 7, 1]
        
        points = self.star_points
        line_color = (100, 100, 150)
        
        # 繪製連線
        pygame.draw.lines(screen, line_color, False, [points[i] for i in sq1_indices], 2)
        pygame.draw.lines(screen, line_color, False, [points[i] for i in sq2_indices], 2)
        # 外圈環
        pygame.draw.circle(screen, (50, 50, 100), (self.center_x, self.center_y), self.radius, 1)
        
        # 4. 標題
        title_surf = self.title_font.render(self.title, True, (200, 200, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title_surf, title_rect)
        
        # 5. 繪製中心信息
        mana = self.game.storage_manager.mana
        mana_text = self.msg_font.render(f"Mana: {mana}", True, (100, 200, 255))
        screen.blit(mana_text, mana_text.get_rect(center=(self.center_x, self.center_y)))
        
        cost_text = self.label_font.render(f"Cost: {self.awaken_cost}", True, (150, 150, 150))
        screen.blit(cost_text, cost_text.get_rect(center=(self.center_x, self.center_y + 30)))
        
        # 6. 按鈕與標籤
        for button in self.buttons:
            button.draw(screen)
            
            # 繪製選中光圈
            if button.is_selected:
                glow_rect = button.rect.inflate(10, 10)
                pygame.draw.ellipse(screen, (255, 255, 255), glow_rect, 2)
            
            # 繪製標籤 (如果是元素按鈕)
            if hasattr(button, 'element_name'):
                name_text = button.element_name.capitalize()
                unlocked = button.element_name in self.game.storage_manager.awakened_elements
                color = (255, 255, 255) if unlocked else (100, 100, 100)
                
                label = self.label_font.render(name_text, True, color)
                # 位置調整：在按鈕下方或上方，視位置而定
                label_rect = label.get_rect(center=(button.rect.centerx, button.rect.bottom + 15))
                screen.blit(label, label_rect)

        # 7. 消息提示
        if self.message:
            self.msg_timer -= 1
            if self.msg_timer > 0:
                msg_surf = self.msg_font.render(self.message, True, (255, 100, 100))
                screen.blit(msg_surf, msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 150)))
            else:
                self.message = None

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        self.buttons[self.selected_index].is_selected = True
                    break
        
        if event.type == pygame.KEYDOWN:
            # 簡單的方向鍵導航可能比較混亂，這裡使用簡單的索引切換
            if event.key in [pygame.K_LEFT, pygame.K_UP]:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key in [pygame.K_RIGHT, pygame.K_DOWN]:
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
        if action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.ELEMENT_MENU)
            self.game.menu_manager.open_menu(MenuNavigation.CRYSTAL_MENU)
            return BasicAction.EXIT_MENU
        elif action.startswith("awaken_"):
            elem = action.split("_")[1]
            success, reason = self._awaken_element(elem)
            if success:
                # 重新初始化按鈕以更新狀態
                self._init_buttons()
                # 恢復選中索引
                if self.selected_index < len(self.buttons):
                    self.buttons[self.selected_index].is_selected = True
                
                self.message = f"Awakened {elem.capitalize()}!"
                self.msg_timer = 100
                print(f"Awakened {elem}")
            else:
                self.message = reason
                self.msg_timer = 100
            return action
        return ""

    def _awaken_element(self, element: str) -> Tuple[bool, str]:
        """覺醒元素"""
        return self.game.storage_manager.awaken_element(element, cost=self.awaken_cost)

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self._init_buttons() # 刷新狀態
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self.message = None