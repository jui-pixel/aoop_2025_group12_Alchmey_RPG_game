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
    """元素覺醒菜單 - 八芒星佈局優化版 (含特效)"""
    
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
        self.awakening_effects = [] # 覺醒特效列表
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
            btn.base_color = color # 儲存基礎顏色用於特效
            self.buttons.append(btn)
            
        # 2. 日月 (光/暗) - 放置在左上和右上角
        sun_pos = (SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT // 2 - 200)
        moon_pos = (SCREEN_WIDTH // 2 + 350, SCREEN_HEIGHT // 2 - 200)
        
        # Light (Sun)
        is_light_unlocked = "light" in awakened
        light_color = (255, 255, 200)
        sun_btn = Button(
            int(sun_pos[0] - 40), int(sun_pos[1] - 40), 80, 80,
            "",
            self._create_celestial_surface(80, light_color, is_light_unlocked, "sun"),
            "awaken_light",
            self.label_font
        )
        sun_btn.element_name = "light"
        sun_btn.base_color = light_color
        self.buttons.append(sun_btn)
        
        # Dark (Moon)
        is_dark_unlocked = "dark" in awakened
        dark_color = (150, 50, 200)
        moon_btn = Button(
            int(moon_pos[0] - 40), int(moon_pos[1] - 40), 80, 80,
            "",
            self._create_celestial_surface(80, dark_color, is_dark_unlocked, "moon"),
            "awaken_dark",
            self.label_font
        )
        moon_btn.element_name = "dark"
        moon_btn.base_color = dark_color
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
            "metal": (200, 200, 210),
            "wood": (50, 255, 50),
            "water": (50, 150, 255),
            "fire": (255, 80, 50),
            "earth": (160, 100, 50),
            "wind": (150, 255, 200),
            "thunder": (255, 255, 50),
            "ice": (100, 255, 255),
            "light": (255, 255, 200),
            "dark": (120, 0, 150)
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
            # 內部高光
            pygame.draw.circle(s, (min(255, color[0]+50), min(255, color[1]+50), min(255, color[2]+50), 100), 
                             (size//2 - 5, size//2 - 5), size//4)
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
                    pygame.draw.line(s, color, center, (ex, ey), 3)
            else: # moon
                pygame.draw.circle(s, color, center, size//2 - 2)
                # 陰影造成月牙效果
                pygame.draw.circle(s, (0, 0, 0, 150), (center[0]+12, center[1]-6), size//2 - 6)
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

    def _trigger_awakening_effect(self, x, y, color):
        """觸發覺醒特效"""
        # 1. 爆發粒子
        for _ in range(40):
            vx = random.uniform(-4, 4)
            vy = random.uniform(-4, 4)
            self.awakening_effects.append({
                'type': 'spark',
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'life': 60,
                'max_life': 60,
                'color': (min(255, color[0]+100), min(255, color[1]+100), min(255, color[2]+100)),
                'size': random.randint(2, 6)
            })
        
        # 2. 擴散光環
        self.awakening_effects.append({
            'type': 'shockwave',
            'x': x, 'y': y,
            'radius': 10,
            'max_radius': 150,
            'width': 5,
            'color': color,
            'life': 40,
            'max_life': 40
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
        sq1_indices = [0, 2, 4, 6, 0]
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
        
        # 6. 按鈕、標籤與已覺醒特效
        for button in self.buttons:
            # 繪製已覺醒的特殊表現 (光環/魔法陣)
            if hasattr(button, 'element_name') and button.element_name in self.game.storage_manager.awakened_elements:
                self._draw_awakened_aura(screen, button)
                
            button.draw(screen)
            
            # 繪製選中光圈
            if button.is_selected:
                glow_rect = button.rect.inflate(14, 14)
                pygame.draw.ellipse(screen, (255, 255, 255), glow_rect, 2)
                # 額外光暈
                s = pygame.Surface((glow_rect.width+20, glow_rect.height+20), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (255, 255, 255, 50), (10, 10, glow_rect.width, glow_rect.height), 4)
                screen.blit(s, (glow_rect.x-10, glow_rect.y-10))
            
            # 繪製標籤
            if hasattr(button, 'element_name'):
                name_text = button.element_name.capitalize()
                unlocked = button.element_name in self.game.storage_manager.awakened_elements
                color = (255, 255, 255) if unlocked else (100, 100, 100)
                
                label = self.label_font.render(name_text, True, color)
                label_rect = label.get_rect(center=(button.rect.centerx, button.rect.bottom + 20))
                screen.blit(label, label_rect)

        # 7. 繪製覺醒特效
        self._update_and_draw_effects(screen)

        # 8. 消息提示
        if self.message:
            self.msg_timer -= 1
            if self.msg_timer > 0:
                # 浮動效果
                y_offset = math.sin(self.animation_time * 5) * 5
                msg_surf = self.msg_font.render(self.message, True, (255, 200, 100))
                screen.blit(msg_surf, msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 130 + y_offset)))
            else:
                self.message = None
                
    def _draw_awakened_aura(self, screen, button):
        """繪製已覺醒元素的周圍光環"""
        center = button.rect.center
        radius = button.rect.width // 2 + 5
        color = button.base_color if hasattr(button, 'base_color') else (255, 255, 255)
        
        # 1. 旋轉的魔法圈 (虛線)
        angle_offset = self.animation_time * 2
        num_segments = 8
        for i in range(num_segments):
            start_angle = angle_offset + i * (math.pi * 2 / num_segments)
            end_angle = start_angle + (math.pi / num_segments)
            
            start_pos = (center[0] + math.cos(start_angle) * (radius + 5), 
                         center[1] + math.sin(start_angle) * (radius + 5))
            end_pos = (center[0] + math.cos(end_angle) * (radius + 5), 
                       center[1] + math.sin(end_angle) * (radius + 5))
            
            # 顏色帶透明度
            line_color = (*color, 150)
            pygame.draw.line(screen, line_color, start_pos, end_pos, 2)

        # 2. 呼吸光暈
        pulse = (math.sin(self.animation_time * 3) + 1) * 0.5 # 0 to 1
        glow_radius = radius + 2 + pulse * 5
        
        s = pygame.Surface((glow_radius*2.5, glow_radius*2.5), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, int(50 + pulse * 50)), (glow_radius*1.25, glow_radius*1.25), glow_radius)
        screen.blit(s, (center[0] - glow_radius*1.25, center[1] - glow_radius*1.25))

    def _update_and_draw_effects(self, screen):
        """更新並繪製所有覺醒特效"""
        alive_effects = []
        for p in self.awakening_effects:
            p['life'] -= 1
            if p['life'] <= 0:
                continue
                
            alive_effects.append(p)
            progress = 1 - (p['life'] / p.get('max_life', 60))
            
            if p['type'] == 'spark':
                # 移動
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vy'] += 0.1 # 重力
                
                # 繪製
                alpha = int(255 * (1 - progress))
                color = (*p['color'], alpha)
                s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
                screen.blit(s, (int(p['x']), int(p['y'])))
                
            elif p['type'] == 'shockwave':
                # 擴散
                current_radius = p['radius'] + (p['max_radius'] - p['radius']) * progress
                width = max(1, int(p['width'] * (1 - progress)))
                alpha = int(255 * (1 - progress))
                
                s = pygame.Surface((current_radius*2.2, current_radius*2.2), pygame.SRCALPHA)
                center_s = (current_radius*1.1, current_radius*1.1)
                pygame.draw.circle(s, (*p['color'], alpha), center_s, int(current_radius), width)
                screen.blit(s, (p['x'] - current_radius*1.1, p['y'] - current_radius*1.1))
                
        self.awakening_effects = alive_effects

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
                # 播放音效或特效
                btn_index = self.selected_index # 假設當前選中的就是這個
                for btn in self.buttons:
                    if btn.action == action:
                        self._trigger_awakening_effect(
                            btn.rect.centerx, btn.rect.centery, 
                            btn.base_color if hasattr(btn, 'base_color') else (255, 255, 255)
                        )
                        break
                        
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
        return self.game.storage_manager.awaken_element(element, cost=self.awaken_cost)

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self._init_buttons()
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self.message = None
            self.awakening_effects = []