# src/menu/menus/death_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
    MenuResult,
    create_menu_result,
    get_menu_config,
    DeathMenuAction
)
import pygame
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import Optional
import random
import math


class DeathMenu(AbstractMenu):
    """死亡菜單 - 顯示死亡信息和返回大廳按鈕"""
    
    def __init__(self, game: 'Game', data: Optional[dict] = None):
        """
        初始化死亡菜單
        
        Args:
            game: 遊戲實例
            data: 可選數據，可包含：
                - 'dungeon_name': 副本名稱
                - 'reason': 死亡原因
                - 'time': 存活時間
                - 'score': 分數
        """
        self.config = get_menu_config('death_menu')
        self.game = game
        self.title = "GAME OVER"
        self.active = False
        
        # 解析數據
        self.data = data or {}
        self.dungeon_name = self.data.get('dungeon_name', 'Unknown Dungeon')
        self.reason = self.data.get('reason', 'You died.')
        self.time = self.data.get('time', 0)
        self.score = self.data.get('score', 0)
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 84)
        self.subtitle_font = pygame.font.SysFont(None, 48)
        self.text_font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 28)
        
        # 按鈕
        button_width = 300
        button_height = 50
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        button_y = SCREEN_HEIGHT - 150
        
        self.buttons = [
            Button(
                button_x, button_y, button_width, button_height,
                "Return to Lobby",
                pygame.Surface((button_width, button_height)),
                DeathMenuAction.RETURN_TO_LOBBY,
                pygame.font.SysFont(None, 40)
            )
        ]
        
        self.selected_index = 0
        self.buttons[self.selected_index].is_selected = True
        
        # 動畫效果
        self.animation_time = 0
        self.particles = []
        self._init_particles()
    
    def _init_particles(self):
        """初始化灰燼/血色粒子效果"""
        for _ in range(60):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(2, 5),
                'speed': random.uniform(0.2, 1.5),
                'alpha': random.randint(50, 200),
                'color': random.choice([(150, 150, 150), (100, 0, 0), (50, 50, 50)]) # 灰, 暗紅, 深灰
            })
    
    def draw(self, screen: pygame.Surface) -> None:
        """繪製死亡菜單"""
        if not self.active:
            return
        
        # 繪製半透明紅色/黑色背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(240)
        overlay.fill((20, 0, 0)) # 深紅色背景
        screen.blit(overlay, (0, 0))
        
        # 繪製粒子
        for particle in self.particles:
            color = (*particle['color'], particle['alpha'])
            s = pygame.Surface((particle['size']*2, particle['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (particle['size'], particle['size']), particle['size'])
            screen.blit(s, (int(particle['x']), int(particle['y'])))
        
        # 繪製標題 (帶脈動效果)
        title_color = self._get_animated_color()
        title_surface = self.title_font.render(self.title, True, title_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(title_surface, title_rect)
        
        # 繪製副本名稱/地點
        dungeon_text = f"Fallen in: {self.dungeon_name}"
        dungeon_surface = self.subtitle_font.render(dungeon_text, True, (180, 180, 180))
        dungeon_rect = dungeon_surface.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(dungeon_surface, dungeon_rect)
        
        # 繪製統計信息
        y_offset = 280
        
        # 死亡原因
        reason_text = f"{self.reason}"
        reason_surface = self.text_font.render(reason_text, True, (255, 100, 100))
        reason_rect = reason_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        screen.blit(reason_surface, reason_rect)
        y_offset += 60
        
        # 時間
        if self.time > 0:
            time_text = f"Survival Time: {self._format_time(self.time)}"
            time_surface = self.text_font.render(time_text, True, (200, 200, 200))
            time_rect = time_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(time_surface, time_rect)
            y_offset += 40
        
        # 分數
        if self.score > 0:
            score_text = f"Score: {self.score}"
            score_surface = self.text_font.render(score_text, True, (200, 200, 200))
            score_rect = score_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(score_surface, score_rect)
            y_offset += 40
        
        # 繪製按鈕
        for button in self.buttons:
            button.draw(screen)
    
    def handle_event(self, event: pygame.event.Event) -> MenuResult:
        """處理事件"""
        if not self.active:
            return MenuResult(action="", success=False)
        
        # 處理鼠標移動
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.buttons[self.selected_index].is_selected = False
                    self.selected_index = i
                    self.buttons[self.selected_index].is_selected = True
                    break
        
        # 處理鍵盤輸入
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self._handle_action(self.buttons[self.selected_index].action)
            elif event.key == pygame.K_ESCAPE:
                return self._handle_action(DeathMenuAction.RETURN_TO_LOBBY)
        
        # 處理鼠標點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._handle_action(action)
        
        return MenuResult(action="", success=False)
    
    def _handle_action(self, action: str) -> MenuResult:
        """處理動作"""
        if action == DeathMenuAction.RETURN_TO_LOBBY:
            # 關閉死亡菜單並返回大廳
            self.game.menu_manager.close_menu(MenuNavigation.DEATH_MENU)
            self.game.start_game() # 這裏假設 start_game 可以重置到大廳，或者需要 game 提供特定方法
            return create_menu_result(
                action=DeathMenuAction.RETURN_TO_LOBBY,
                success=True,
                message="Returning to lobby...",
                close_current=True,
                data={'target_state': 'lobby'}
            )
        
        return MenuResult(action="", success=False)
    
    def get_selected_action(self) -> str:
        """獲取當前選中的動作"""
        return self.buttons[self.selected_index].action if self.active else ""
    
    def activate(self, active: bool) -> None:
        """激活/禁用菜單"""
        self.active = active
        if active:
            self.buttons[self.selected_index].is_selected = True
            self.animation_time = 0
            self._init_particles()
        else:
            self.buttons[self.selected_index].is_selected = False
    
    def update(self, dt: float) -> None:
        """更新動畫"""
        if not self.active:
            return
        
        self.animation_time += dt
        
        # 更新粒子
        for particle in self.particles:
            particle['y'] -= particle['speed'] # 向上飄
            if particle['y'] < 0:
                particle['y'] = SCREEN_HEIGHT
                particle['x'] = random.randint(0, SCREEN_WIDTH)
            
            # 稍微左右擺動
            particle['x'] += math.sin(self.animation_time + particle['y'] * 0.01) * 0.5
    
    def _get_animated_color(self) -> tuple:
        """獲取動畫顏色（血色脈動）"""
        # 紅色脈動
        intensity = int(180 + 75 * math.sin(self.animation_time * 2))
        return (intensity, 0, 0)
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間顯示"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
