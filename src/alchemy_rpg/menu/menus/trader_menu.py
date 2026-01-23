import pygame
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.menu.menu_config import BasicAction, MenuNavigation
from src.ecs.components import Health

class TraderMenu(AbstractMenu):
    """
    商人菜單：Mana -> HP 轉換
    """
    def __init__(self, game):
        self.game = game
        self.title = "Life Trader"
        self.active = False
        
        # 交易匯率配置
        self.trade_options = [
            {"cost": 5, "heal": 50, "desc": "Small Heal"},
            {"cost": 10, "heal": 120, "desc": "Medium Heal"},
            {"cost": 25, "heal": 9999, "desc": "Full Restore"},
        ]
        
        # 字體
        self.title_font = pygame.font.SysFont(None, 64)
        self.info_font = pygame.font.SysFont(None, 36)
        self.btn_font = pygame.font.SysFont(None, 32)
        
        # 狀態訊息
        self.message = ""
        self.msg_timer = 0
        
        # UI 佈局
        self.panel_width = 500
        self.panel_height = 400
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2
        self.panel_rect = pygame.Rect(
            self.center_x - self.panel_width // 2,
            self.center_y - self.panel_height // 2,
            self.panel_width,
            self.panel_height
        )

        self._init_buttons()
        self.selected_index = 0
        if self.buttons:
            self.buttons[0].is_selected = True

    def _init_buttons(self):
        self.buttons = []
        btn_w, btn_h = 300, 50
        start_y = self.panel_rect.top + 120
        gap = 15
        
        # 生成交易按鈕
        for i, opt in enumerate(self.trade_options):
            text = f"{opt['desc']} ({opt['cost']} Mana)"
            y_pos = start_y + i * (btn_h + gap)
            
            btn = Button(
                self.center_x - btn_w // 2,
                y_pos,
                btn_w, btn_h,
                text,
                self._create_surface(btn_w, btn_h, (60, 60, 80)),
                f"trade_{i}", # Action ID
                self.btn_font
            )
            self.buttons.append(btn)
            
        # 退出按鈕
        exit_y = start_y + len(self.trade_options) * (btn_h + gap) + 20
        exit_btn = Button(
            self.center_x - btn_w // 2,
            exit_y,
            btn_w, btn_h,
            "Leave Shop",
            self._create_surface(btn_w, btn_h, (100, 60, 60)),
            "back",
            self.btn_font
        )
        self.buttons.append(exit_btn)

    def _create_surface(self, w, h, color):
        s = pygame.Surface((w, h))
        s.fill(color)
        pygame.draw.rect(s, (200, 200, 200), (0, 0, w, h), 2)
        return s

    def _get_player_health(self) -> Health:
        """獲取玩家的 Health 組件"""
        return self.game.entity_manager.player._get_health_comp()

    def update(self, dt: float) -> None:
        if self.msg_timer > 0:
            self.msg_timer -= dt
            if self.msg_timer <= 0:
                self.message = ""

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active: return

        # 1. 背景遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))

        # 2. 主面板
        pygame.draw.rect(screen, (40, 40, 50), self.panel_rect)
        pygame.draw.rect(screen, (100, 200, 255), self.panel_rect, 3) # 藍色邊框

        # 3. 標題
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.center_x, self.panel_rect.top + 40))
        screen.blit(title_surf, title_rect)

        # 4. 玩家當前狀態 (Mana & HP)
        player_hp = self._get_player_health()
        current_hp = player_hp.current_hp if player_hp else 0
        max_hp = player_hp.max_hp if player_hp else 0
        current_mana = self.game.storage_manager.mana

        status_text = f"HP: {int(current_hp)}/{int(max_hp)}   |   Mana: {int(current_mana)}"
        status_surf = self.info_font.render(status_text, True, (100, 255, 100))
        status_rect = status_surf.get_rect(center=(self.center_x, self.panel_rect.top + 80))
        screen.blit(status_surf, status_rect)

        # 5. 按鈕
        for btn in self.buttons:
            btn.draw(screen)

        # 6. 回饋訊息
        if self.message:
            msg_color = (255, 100, 100) if "Short" in self.message or "Full" in self.message else (100, 255, 100)
            msg_surf = self.info_font.render(self.message, True, msg_color)
            msg_rect = msg_surf.get_rect(center=(self.center_x, self.panel_rect.bottom - 30))
            screen.blit(msg_surf, msg_rect)

    def handle_event(self, event: pygame.event.Event) -> str:
        if not self.active: return ""

        # 鍵盤導航
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.menu_manager.close_menu(MenuNavigation.TRADER_MENU)
                return BasicAction.EXIT_MENU
            
            elif event.key == pygame.K_UP:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_DOWN:
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
                
            elif event.key == pygame.K_RETURN:
                return self._process_action(self.buttons[self.selected_index].action)

        # 滑鼠交互
        if event.type == pygame.MOUSEMOTION:
            for i, btn in enumerate(self.buttons):
                if btn.rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.buttons[self.selected_index].is_selected = False
                        self.selected_index = i
                        btn.is_selected = True
                    break

        # 按鈕點擊
        for btn in self.buttons:
            active, action = btn.handle_event(event)
            if active:
                return self._process_action(action)

        return ""

    def _process_action(self, action: str) -> str:
        if action == "back":
            self.game.menu_manager.close_menu(MenuNavigation.TRADER_MENU)
            return BasicAction.EXIT_MENU
        
        elif action.startswith("trade_"):
            idx = int(action.split("_")[1])
            self._perform_trade(self.trade_options[idx])
            return "trade"
            
        return ""

    def _perform_trade(self, option: dict):
        player_hp_comp = self._get_player_health()
        if not player_hp_comp:
            return

        cost = option['cost']
        heal_amt = option['heal']

        # 1. 檢查血量是否已滿
        if player_hp_comp.current_hp >= player_hp_comp.max_hp:
            self.message = "Health is already Full!"
            self.msg_timer = 2.0
            return

        # 2. 檢查 Mana 是否足夠
        if self.game.storage_manager.mana < cost:
            self.message = "Mana Shortage!"
            self.msg_timer = 2.0
            return

        # 3. 執行交易
        self.game.storage_manager.mana -= cost
        
        # 回血邏輯 (不超過上限)
        old_hp = player_hp_comp.current_hp
        player_hp_comp.current_hp = min(player_hp_comp.max_hp, player_hp_comp.current_hp + heal_amt)
        actual_healed = int(player_hp_comp.current_hp - old_hp)

        self.message = f"Recovered {actual_healed} HP!"
        self.msg_timer = 2.0

    def activate(self, active: bool) -> None:
        self.active = active
        self.message = ""
        # 每次打開時重置選擇
        if active:
            self.selected_index = 0
            for btn in self.buttons: btn.is_selected = False
            if self.buttons: self.buttons[0].is_selected = True
    
    def is_active(self) -> bool:
        return self.active
    
    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""