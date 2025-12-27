import pygame
import math
import random
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import BasicAction, MenuNavigation

class TreasureMenu(AbstractMenu):
    """
    幸運轉盤菜單：透過旋轉獲取 Mana 獎勵
    """
    def __init__(self, game, data = None, on_spin_callback=None):
        self.game = game
        self.title = "Wheel of Fortune"
        self.active = False
        self.on_spin_callback = on_spin_callback  # 轉盤轉動後的回調函數
        self.allow_spin = True
        # --- 轉盤配置 ---
        self.segments = [
            {"val": 10,  "color": (200, 200, 200), "label": "10"},
            {"val": 50,  "color": (100, 255, 100), "label": "50"},
            {"val": 0,   "color": (100, 100, 100), "label": "Miss"},
            {"val": 20,  "color": (150, 150, 255), "label": "20"},
            {"val": 100, "color": (255, 215, 0),   "label": "100!"}, # 大獎
            {"val": 10,  "color": (200, 200, 200), "label": "10"},
            {"val": 30,  "color": (100, 200, 255), "label": "30"},
            {"val": 0,   "color": (100, 100, 100), "label": "Miss"},
        ]
        
        # --- 物理與狀態 ---
        self.angle = 0.0          # 當前角度 (0-360)
        self.velocity = 0.0       # 旋轉速度
        self.is_spinning = False
        self.result_timer = 0
        self.message = ""
        
        # --- 視覺參數 ---
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2 - 50
        self.radius = 180
        
        # 預先渲染轉盤表面 (優化效能)
        self.wheel_surface = self._create_wheel_surface()
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.label_font = pygame.font.SysFont(None, 32)
        self.msg_font = pygame.font.SysFont(None, 48)

        self._init_buttons()
        self.selected_index = 0

    def _create_wheel_surface(self) -> pygame.Surface:
        """預先繪製轉盤的靜態圖像"""
        size = self.radius * 2
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (self.radius, self.radius)
        
        num_seg = len(self.segments)
        arc_step = 360 / num_seg
        
        font = pygame.font.SysFont(None, 28)
        
        for i, seg in enumerate(self.segments):
            start_angle = i * arc_step
            end_angle = (i + 1) * arc_step
            
            # 1. 繪製扇形 (使用多邊形模擬)
            # 注意：Pygame 的 math 是弧度制
            points = [center]
            # 增加細分讓邊緣更圓滑
            for a in range(int(start_angle), int(end_angle) + 1, 2):
                rad = math.radians(a)
                x = self.radius + self.radius * math.cos(rad)
                y = self.radius + self.radius * math.sin(rad)
                points.append((x, y))
            
            pygame.draw.polygon(surface, seg['color'], points)
            pygame.draw.polygon(surface, (50, 50, 50), points, 2) # 邊框
            
            # 2. 繪製文字 (位於扇形中心)
            mid_angle = math.radians(start_angle + arc_step / 2)
            # 文字位置：半徑的 0.7 處
            text_r = self.radius * 0.7
            text_x = self.radius + text_r * math.cos(mid_angle)
            text_y = self.radius + text_r * math.sin(mid_angle)
            
            text_surf = font.render(seg['label'], True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=(text_x, text_y))
            
            # 可選：旋轉文字以對齊中心 (這裡簡化處理，直接顯示)
            surface.blit(text_surf, text_rect)
            
        return surface

    def _init_buttons(self):
        # ... (保留座標計算) ...
        btn_w, btn_h = 200, 60
        y_pos = SCREEN_HEIGHT - 120
        
        # 根據是否允許旋轉，改變按鈕顏色
        spin_color = (100, 200, 100) if self.allow_spin else (100, 100, 100)
        spin_text = "SPIN!" if self.allow_spin else "Claimed"

        self.spin_btn = Button(
            self.center_x - btn_w - 20, y_pos, btn_w, btn_h,
            spin_text, 
            self._create_btn_surf(btn_w, btn_h, spin_color),
            "spin", self.label_font
        )
        
        self.back_btn = Button(
            self.center_x + 20, y_pos, btn_w, btn_h,
            "Leave",
            self._create_btn_surf(btn_w, btn_h, (200, 100, 100)),
            "back", self.label_font
        )
        
        self.buttons = [self.spin_btn, self.back_btn]
        self.buttons[0].is_selected = True

    def _create_btn_surf(self, w, h, color):
        s = pygame.Surface((w, h))
        s.fill(color)
        pygame.draw.rect(s, (255, 255, 255), (0, 0, w, h), 3)
        return s

    def update(self, dt: float) -> None:
        if not self.active: return
        
        if self.is_spinning:
            # 物理模擬
            self.angle += self.velocity * dt * 60 # dt * 60 為了標準化幀率
            self.angle %= 360
            
            # 摩擦力 (減速)
            self.velocity *= 0.985 
            
            # 停止條件
            if self.velocity < 0.1:
                self.velocity = 0
                self.is_spinning = False
                self._calculate_result()
                
        # 簡單的按鈕選中動畫
        if not self.is_spinning and self.buttons[0].is_selected:
             # 可以加個閃爍效果
             pass

    def _calculate_result(self):
        """計算指針指向的獎勵"""
        # 1. 計算每個扇形的角度大小
        num_segments = len(self.segments)
        step = 360 / num_segments
        
        # 2. 核心修正：
        # Pygame 繪圖是順時針 (0->90 是右->下)，rotate 是逆時針。
        # 當轉盤逆時針轉動 Angle 度，原本位於 Angle 度的像素就會轉到 0 度(指針位置)。
        # 因此，指針指到的「原始扇形角度」就是當前的 self.angle。
        
        # 確保角度在 0-360 之間
        hit_angle = self.angle % 360
        
        # 3. 計算索引
        index = int(hit_angle // step)
        
        # 防呆：確保索引不超出範圍 (雖然理論上 % 360 不會超)
        index = index % num_segments
        
        result = self.segments[index]
        
        # 4. 結算
        reward = result['val']
        self.message = f"Result: {result['label']}"
        
        if reward > 0:
            self.game.storage_manager.mana += reward
            self.message += f" (+{reward} Mana)"
        else:
            self.message = "Bad Luck..."

        # [新增] 鎖定轉盤並觸發回調
        self.allow_spin = False
        self._update_spin_button_visuals() # 更新按鈕外觀
        
        if self.on_spin_callback:
            self.on_spin_callback() # 通知 NPC 已經轉過了

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active: return
        
        # 1. 背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((20, 10, 10))
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))
        
        # 2. 標題
        title_surf = self.title_font.render(self.title, True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(self.center_x, 60))
        screen.blit(title_surf, title_rect)
        
        # 3. 繪製轉盤 (旋轉)
        # 注意：pygame.transform.rotate 是逆時針旋轉
        # 我們需要負號來模擬順時針/逆時針，這裡直接用 self.angle
        rotated_wheel = pygame.transform.rotate(self.wheel_surface, self.angle)
        wheel_rect = rotated_wheel.get_rect(center=(self.center_x, self.center_y))
        screen.blit(rotated_wheel, wheel_rect)
        
        # 4. 繪製指針 (固定在右側)
        # 三角形指向左邊 (指向轉盤中心)
        pointer_color = (255, 50, 50)
        # 指針尖端位置
        tip_x = self.center_x + self.radius - 10 
        tip_y = self.center_y
        
        pygame.draw.polygon(screen, pointer_color, [
            (tip_x, tip_y),           # 尖端
            (tip_x + 30, tip_y - 15), # 右上
            (tip_x + 30, tip_y + 15)  # 右下
        ])
        
        # 5. 結果訊息
        if self.message:
            msg_surf = self.msg_font.render(self.message, True, (255, 255, 255))
            msg_rect = msg_surf.get_rect(center=(self.center_x, self.center_y + self.radius + 60))
            pygame.draw.rect(screen, (0,0,0), msg_rect.inflate(20, 10)) # 背景黑框
            screen.blit(msg_surf, msg_rect)
            
        # 6. 按鈕
        # 轉動時隱藏按鈕，或禁用
        if not self.is_spinning:
            for btn in self.buttons:
                btn.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active or self.is_spinning:
            return ""

        # 鍵盤
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.menu_manager.close_menu(MenuNavigation.TREASURE_MENU)
                return BasicAction.EXIT_MENU
                
            elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self._process_action(self.buttons[self.selected_index].action)

        # 滑鼠
        if event.type == pygame.MOUSEMOTION:
            for i, btn in enumerate(self.buttons):
                if btn.rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        btn.is_selected = True

        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.buttons:
                if btn.rect.collidepoint(event.pos):
                    return self._process_action(btn.action)

        return ""

    def _process_action(self, action: str) -> str:
        if action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.TREASURE_MENU)
            return BasicAction.EXIT_MENU
            
        elif action == "spin":
            self._start_spin()
            return "spin"
            
        return ""

    def _start_spin(self):
        """開始旋轉"""
        self.is_spinning = True
        self.message = ""
        # 初始速度：隨機值，保證結果隨機
        # 速度範圍：20.0 到 40.0 (每幀角度變化)
        self.velocity = random.uniform(20.0, 45.0)

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self.message = ""
            self.angle = 0
            self.is_spinning = False
            self.velocity = 0
    
    def reset(self) -> None:
        self.activate(False)
        self.message = ""
        self.angle = 0
        self.is_spinning = False
        self.velocity = 0
    
    def is_active(self) -> bool:
        return self.active
    
    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""
    
    def _update_spin_button_visuals(self):
        """更新按鈕狀態為已領取"""
        btn_w, btn_h = 200, 60
        # 變灰
        self.spin_btn.surface = self._create_btn_surf(btn_w, btn_h, (100, 100, 100))
        self.spin_btn.text = "Claimed"
    
    def _process_action(self, action: str) -> str:
        if action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.TREASURE_MENU)
            return BasicAction.EXIT_MENU
            
        elif action == "spin":
            # [新增] 檢查是否允許旋轉
            if self.allow_spin:
                self._start_spin()
                return "spin"
            else:
                # 播放一個禁止的音效或提示
                pass
            
        return ""