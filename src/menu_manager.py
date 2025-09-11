from src.menu.abstract_menu import AbstractMenu
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class MenuManager:
    def __init__(self, screen, game):
        """初始化菜單管理器，負責管理遊戲中的各個菜單。

        Args:
            screen: Pygame 的顯示表面，用於渲染菜單。
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.screen = screen  # 保存 Pygame 顯示表面
        self.game = game  # 保存遊戲實例引用
        self.menus = {}  # 用於儲存所有菜單的字典，鍵為菜單名稱，值為菜單實例
        self.current_menu = None  # 當前顯示的菜單，初始為空
        self.font = pygame.font.SysFont(None, 48)  # 初始化字體，字體大小為 48

    def register_menu(self, name, menu: AbstractMenu = None):
        """註冊一個菜單。

        Args:
            name: 菜單的名稱。
            menu: 菜單實例（AbstractMenu 的子類），可以為 None（延遲初始化）。

        將菜單加入到 menus 字典中，並設置其初始激活狀態為 False。
        """
        self.menus[name] = menu
        if menu is not None:
            menu.activate(False)  # 設置菜單為非激活狀態
        print(f"MenuManager: 已註冊菜單 {name}，實例：{menu.__class__.__name__ if menu else 'None'}")

    def set_menu(self, menu_name):
        """設置當前顯示的菜單。

        Args:
            menu_name: 要顯示的菜單名稱。

        如果當前有活動菜單，則先停用它，然後切換到新菜單並激活。
        """
        if self.current_menu:
            self.current_menu.activate(False)  # 停用當前菜單
        if menu_name in self.menus:
            self.current_menu = self.menus[menu_name]  # 設置新菜單
            if self.current_menu:
                self.current_menu.activate(True)  # 激活新菜單
        else:
            self.current_menu = None  # 如果菜單不存在，設置為 None
        print(f"MenuManager: 設置菜單為 {menu_name}，當前菜單：{self.current_menu.__class__.__name__ if self.current_menu else 'None'}")

    def draw(self):
        """繪製當前菜單。

        如果有活動菜單，則調用其 draw 方法進行渲染，並刷新顯示。
        """
        if self.current_menu:
            self.current_menu.draw(self.screen)  # 繪製當前菜單
            pygame.display.flip()  # 更新螢幕顯示

    def handle_event(self, event):
        """處理菜單相關的事件。

        Args:
            event: Pygame 事件對象。

        Returns:
            str: 事件的處理結果（例如菜單選項的動作）。

        如果有活動菜單，則將事件傳遞給當前菜單處理，並根據結果執行相應操作。
        """
        if self.current_menu:
            result = self.current_menu.handle_event(event)  # 將事件傳遞給當前菜單
            print(f"MenuManager: 處理事件 {self.current_menu.__class__.__name__}，結果：{result}")
            if self.current_menu.__class__.__name__ == "SettingsMenu" and result in ["toggle_sound", "back"]:
                if result == "toggle_sound":
                    print("MenuManager: 正在切換音效（尚未實現）")
                    # TODO: 實現音效開關邏輯
                elif result == "back":
                    self.game.hide_menu('settings_menu')  # 返回主菜單
                return ""
            return result
        return ""