# src/menu/menus/win_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
from src.menu.menu_config import (
    BasicAction,
    MenuNavigation,
    MenuResult,
    create_menu_result,
    get_menu_config
)
import pygame
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import Optional


class WinMenu(AbstractMenu):
    """勝利菜單 - 顯示勝利信息和返回大廳按鈕"""
    
    def __init__(self, game: 'Game', data: Optional[dict] = None):
        """
        初始化勝利菜單
        
        Args:
            game: 遊戲實例
            data: 可選數據，可包含：
                - 'dungeon_name': 副本名稱
                - 'rewards': 獎勵信息
                - 'time': 通關時間
                - 'score': 分數
        """
        self.config = get_menu_config('win_menu')
        self.game = game
        self.title = "🎉 VICTORY! 🎉"
        self.active = False
        
        # 解析數據
        self.data = data or {}
        self.dungeon_name = self.data.get('dungeon_name', 'Unknown Dungeon')
        self.rewards = self.data.get('rewards', {})
        self.time = self.data.get('time', 0)
        self.score = self.data.get('score', 0)
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 72)
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
                "return_to_lobby",
                pygame.font.SysFont(None, 40)
            )
        ]
        
        self.selected_index = 0
        self.buttons[self.selected_index].is_selected = True
        
        # 動畫效果
        self.animation_time = 0
        self.star_particles = []
        self._init_particles()
    
    def _init_particles(self):
        """初始化星星粒子效果"""
        import random
        for _ in range(50):
            self.star_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(2, 6),
                'speed': random.uniform(0.5, 2.0),
                'alpha': random.randint(100, 255)
            })
    
    def draw(self, screen: pygame.Surface) -> None:
        """繪製勝利菜單"""
        if not self.active:
            return
        
        # 繪製半透明黑色背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # 繪製星星粒子
        for particle in self.star_particles:
            color = (255, 255, 200, particle['alpha'])
            pygame.draw.circle(
                screen, 
                color[:3], 
                (int(particle['x']), int(particle['y'])), 
                particle['size']
            )
        
        # 繪製標題 (帶動畫效果)
        title_color = self._get_animated_color()
        title_surface = self.title_font.render(self.title, True, title_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)
        
        # 繪製副本名稱
        dungeon_text = f"Completed: {self.dungeon_name}"
        dungeon_surface = self.subtitle_font.render(dungeon_text, True, (200, 200, 200))
        dungeon_rect = dungeon_surface.get_rect(center=(SCREEN_WIDTH // 2, 180))
        screen.blit(dungeon_surface, dungeon_rect)
        
        # 繪製統計信息
        y_offset = 250
        
        # 時間
        if self.time > 0:
            time_text = f"Time: {self._format_time(self.time)}"
            time_surface = self.text_font.render(time_text, True, (150, 255, 150))
            time_rect = time_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(time_surface, time_rect)
            y_offset += 50
        
        # 分數
        if self.score > 0:
            score_text = f"Score: {self.score}"
            score_surface = self.text_font.render(score_text, True, (255, 215, 0))
            score_rect = score_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(score_surface, score_rect)
            y_offset += 50
        
        # 獎勵
        if self.rewards:
            y_offset += 20
            rewards_title = self.text_font.render("Rewards:", True, (255, 255, 100))
            rewards_rect = rewards_title.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(rewards_title, rewards_rect)
            y_offset += 40
            
            for reward_name, reward_value in self.rewards.items():
                reward_text = f"  + {reward_name}: {reward_value}"
                reward_surface = self.small_font.render(reward_text, True, (200, 200, 255))
                reward_rect = reward_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                screen.blit(reward_surface, reward_rect)
                y_offset += 35
        
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
                # ESC 也可以返回大廳
                return self._handle_action("return_to_lobby")
        
        # 處理鼠標點擊
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                return self._handle_action(action)
        
        return MenuResult(action="", success=False)
    
    def _handle_action(self, action: str) -> MenuResult:
        """處理動作"""
        if action == "return_to_lobby":
            # 關閉勝利菜單並返回大廳
            self.game.menu_manager.close_menu(MenuNavigation.WIN_MENU)
            self.game.start_game()
            return create_menu_result(
                action="return_to_lobby",
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
            self._init_particles()  # 重新初始化粒子
        else:
            self.buttons[self.selected_index].is_selected = False
    
    def update(self, dt: float) -> None:
        """更新動畫"""
        if not self.active:
            return
        
        self.animation_time += dt
        
        # 更新星星粒子
        for particle in self.star_particles:
            particle['y'] += particle['speed']
            if particle['y'] > SCREEN_HEIGHT:
                particle['y'] = 0
                import random
                particle['x'] = random.randint(0, SCREEN_WIDTH)
    
    def _get_animated_color(self) -> tuple:
        """獲取動畫顏色（閃爍效果）"""
        import math
        # 使用正弦波創建閃爍效果
        intensity = int(200 + 55 * math.sin(self.animation_time * 3))
        return (255, intensity, 0)  # 金色閃爍
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間顯示"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
