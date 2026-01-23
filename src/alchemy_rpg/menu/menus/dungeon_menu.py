# src/menu/menus/dungeon_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
import math
import random
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Dict, TYPE_CHECKING, Optional
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
)

if TYPE_CHECKING:
    from src.core.game import Game
    from src.entities.npc.dungeon_portal_npc import DungeonPortalNPC

class DungeonMenu(AbstractMenu):
    """地牢選擇菜單 - 優化版"""
    
    def __init__(self, game: 'Game', dungeons: List[Dict], npc_facade: 'Optional[DungeonPortalNPC]' = None):
        """
        初始化地牢菜單
        :param game: 遊戲實例
        :param dungeons: 可選地牢列表
        :param npc_facade: 開啟此菜單的 DungeonPortalNPC 門面實例
        """
        self.game = game
        self.title = "Dungeon Portal"
        self.dungeons = dungeons if dungeons else []
        self.npc_facade = npc_facade
        self.active = False
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.header_font = pygame.font.SysFont(None, 36)
        self.detail_font = pygame.font.SysFont(None, 24)
        
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
        """初始化按鈕"""
        self.buttons = []
        
        btn_width = 300
        btn_height = 60
        gap = 25
        start_y = 200
        center_x = SCREEN_WIDTH // 2
        
        # 地牢按鈕
        for i, dungeon in enumerate(self.dungeons):
            y = start_y + i * (btn_height + gap)
            
            # 按鈕文本包含名稱和等級
            text = f"{dungeon['name']} (Lv.{dungeon['level']})"
            
            btn = Button(
                center_x - btn_width // 2, y, btn_width, btn_height,
                text,
                self._create_button_surface(btn_width, btn_height, (60, 40, 60)), # 深紫色基調
                f"enter_{dungeon['name']}",
                self.header_font
            )
            self.buttons.append(btn)
            
        # 返回按鈕
        back_y = SCREEN_HEIGHT - 100
        back_btn = Button(
            center_x - btn_width // 2, back_y, btn_width, btn_height,
            "Close Portal",
            self._create_button_surface(btn_width, btn_height, (60, 60, 60)), # 深灰色
            "back",
            self.header_font
        )
        self.buttons.append(back_btn)

    def _create_button_surface(self, width, height, base_color):
        """創建地牢風格按鈕表面"""
        surface = pygame.Surface((width, height))
        r, g, b = base_color
        
        # 粗糙的石頭質感(模擬)
        surface.fill(base_color)
        for _ in range(50):
            noise_color = (
                min(255, max(0, r + random.randint(-10, 10))),
                min(255, max(0, g + random.randint(-10, 10))),
                min(255, max(0, b + random.randint(-10, 10)))
            )
            pygame.draw.circle(surface, noise_color, 
                             (random.randint(0, width), random.randint(0, height)), 
                             random.randint(1, 3))
            
        # 邊框 - 看起來像古老與魔法的結合
        pygame.draw.rect(surface, (
            min(255, int(r*1.5)), min(255, int(g*0.8)), min(255, int(b*1.5))
        ), (0, 0, width, height), 2)
        
        # 角落裝飾
        corner_len = 10
        corner_color = (200, 100, 255)
        # 左上
        pygame.draw.line(surface, corner_color, (0, 0), (corner_len, 0), 2)
        pygame.draw.line(surface, corner_color, (0, 0), (0, corner_len), 2)
        # 右下
        pygame.draw.line(surface, corner_color, (width-2, height-2), (width-corner_len-2, height-2), 2)
        pygame.draw.line(surface, corner_color, (width-2, height-2), (width-2, height-corner_len-2), 2)
        
        return surface

    def _init_particles(self):
        """初始化傳送門粒子"""
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(SCREEN_HEIGHT, SCREEN_HEIGHT + 200),
                'vy': random.uniform(1, 3), # 向上飘
                'size': random.randint(2, 5),
                'color': random.choice([
                    (100, 50, 150), (150, 50, 200), (50, 0, 50), (200, 100, 255)
                ]),
                'alpha': random.randint(50, 200)
            })

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
            
        self.animation_time += 0.05
        
        # 1. 背景 (地牢深色氛圍)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((5, 0, 10))
        overlay.set_alpha(240)
        screen.blit(overlay, (0, 0))
        
        # 2. 粒子效果 (從下往上飄的魔力)
        for p in self.particles:
            alpha = int(p['alpha'] + 50 * math.sin(self.animation_time + p['x']))
            color = (*p['color'], max(0, min(255, alpha)))
            
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']), int(p['y'])))
            
            # 移動
            p['y'] -= p['vy']
            # 螺旋上升
            p['x'] += math.sin(p['y'] * 0.01 + self.animation_time) * 0.5
            
            if p['y'] < -10:
                p['y'] = SCREEN_HEIGHT + random.randint(0, 100)
                p['x'] = random.randint(0, SCREEN_WIDTH)

        # 3. 標題 (帶有漩渦光效)
        title_y = 60
        
        # 旋轉的魔法陣背景 (簡單模擬)
        center_title = (SCREEN_WIDTH // 2, title_y + 10)
        angle = self.animation_time * 20
        radius = 160
        # 畫幾個點代表魔法陣
        for i in range(8):
            rad = math.radians(angle + i * 45)
            x = center_title[0] + math.cos(rad) * radius
            y = center_title[1] + math.sin(rad) * (radius * 0.3) # 壓扁成橢圓
            color = (100, 50, 150, 100)
            pygame.draw.circle(screen, color, (int(x), int(y)), 5)
            
        # 文字
        title_surf = self.title_font.render(self.title, True, (200, 150, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        # 陰影
        shadow_surf = self.title_font.render(self.title, True, (50, 0, 50))
        screen.blit(shadow_surf, (title_rect.x + 3, title_rect.y + 3))
        screen.blit(title_surf, title_rect)
        
        # 4. 按鈕
        for button in self.buttons:
            button.draw(screen)

    def _handle_enter_action(self, dungeon_name: str) -> str:
        """處理進入地牢的邏輯"""
        if self.npc_facade:
            self.npc_facade.enter_dungeon(dungeon_name)
            self.game.menu_manager.close_all_menus()
        else:
            print("DungeonMenu: 錯誤！找不到 DungeonPortalNPC 門面實例。")
        return f"enter_{dungeon_name}"

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active:
            return ""
            
        # 鼠標悬停
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        self.buttons[self.selected_index].is_selected = True
                    break
        
        # 鍵盤導航
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
                
        # 點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._process_action(action)
                
        return ""
        
    def _process_action(self, action: str) -> str:
        if action == "back":
            self.game.menu_manager.close_all_menus()
            return BasicAction.EXIT_MENU
        if action.startswith("enter_"):
            dungeon_name = action.split("_", 1)[1]
            return self._handle_enter_action(dungeon_name)
        return action

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self._init_particles()
        else:
            if 0 <= self.selected_index < len(self.buttons):
                self.buttons[self.selected_index].is_selected = False

    def update_npc_facade(self, npc_facade: 'DungeonPortalNPC') -> None:
        """更新存儲的 DungeonPortalNPC 門面實例"""
        self.npc_facade = npc_facade