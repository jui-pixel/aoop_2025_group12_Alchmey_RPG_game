# src/menu_manager.py
from src.menu.abstract_menu import AbstractMenu
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Optional # 引入 List 和 Optional 類型提示

class MenuManager:
    def __init__(self, game):
        """初始化菜單管理器，負責管理遊戲中的各個菜單。

        Args:
            screen: Pygame 的顯示表面，用於渲染菜單。
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.screen = game.screen  # 保存 Pygame 顯示表面
        self.game = game  # 保存遊戲實例引用
        self.menus = {}  # 用於儲存所有菜單的字典，鍵為菜單名稱，值為菜單實例
        self.menu_stack: List[AbstractMenu] = []  # <--- 使用菜單堆棧來支援菜單疊加
        self.current_menu: Optional[AbstractMenu] = self.get_current_menu()  # 當前活動菜單
        self.font = pygame.font.SysFont(None, 48)  # 初始化字體，字體大小為 48

    def register_menu(self, name, menu: AbstractMenu = None):
        """註冊一個菜單。

        Args:
            name: 菜單的名稱。
            menu: 菜單實例（AbstractMenu 的子類），可以為 None（延遲初始化）。

        將菜單加入到 menus 字典中，並設置其初始激活狀態為 False。
        """
        if name in self.menus and self.menus[name] is not None:
            print(f"MenuManager: 菜單 {name} 已存在，無法重複註冊")
            return
        self.menus[name] = menu
        if menu is not None:
            menu.activate(False)  # 設置菜單為非激活狀態
        print(f"MenuManager: 已註冊菜單 {name}，實例：{menu.__class__.__name__ if menu else 'None'}")

    # =====================================================================
    #  核心疊加邏輯：push_menu, pop_menu, get_current_menu (取代 set_menu)
    # =====================================================================

    def push_menu(self, menu_name: str) -> None:
        """
        將指定菜單推入堆棧頂部，並將其激活。
        如果堆棧非空，舊的頂層菜單將被禁用（不處理輸入）。
        """
        if menu_name not in self.menus or self.menus[menu_name] is None:
            print(f"MenuManager: 菜單 {menu_name} 尚未註冊或未實例化。")
            return

        new_menu = self.menus[menu_name]

        # 1. 如果堆棧不為空，將當前頂層菜單設為禁用 (阻止其處理輸入)
        current_top = self.get_current_menu()
        if current_top:
            current_top.activate(False) 

        # 2. 推入新菜單
        self.menu_stack.append(new_menu)

        # 3. 激活新菜單 (允許其處理輸入)
        new_menu.activate(True)
        print(f"MenuManager: Pushed {menu_name}. Stack size: {len(self.menu_stack)}")

    def pop_menu(self) -> Optional[AbstractMenu]:
        """
        彈出堆棧頂部的菜單（關閉當前活動菜單）。
        如果堆棧中仍有其他菜單，則激活新的頂層菜單。
        """
        if not self.menu_stack:
            return None

        # 1. 彈出並禁用頂部菜單
        popped_menu = self.menu_stack.pop()
        popped_menu.activate(False)
        
        # 2. 激活新的頂層菜單（如果存在）
        new_top = self.get_current_menu()
        if new_top:
            new_top.activate(True)
            print(f"MenuManager: Popped {popped_menu.__class__.__name__}. New top: {new_top.__class__.__name__}. Stack size: {len(self.menu_stack)}")
        else:
            print(f"MenuManager: Popped {popped_menu.__class__.__name__}. Stack is empty.")
            
        return popped_menu

    def get_current_menu(self) -> Optional[AbstractMenu]:
        """獲取當前堆棧頂部的菜單 (即唯一能處理輸入的菜單)。"""
        return self.menu_stack[-1] if self.menu_stack else None

    # 為了兼容舊代碼，保留 set_menu，但將其重定向到 push/pop
    def set_menu(self, menu_name):
        """兼容舊接口：設置當前顯示的菜單。
        
        注意：由於採用了堆棧邏輯，此方法不再直接替換菜單，
        而是先清空堆棧，然後推入新菜單。
        """
        # 先清空堆棧
        while self.menu_stack:
            self.pop_menu() # 這裡的 pop_menu 會在內部輸出 log
        
        # 然後推入新菜單
        if menu_name:
            self.push_menu(menu_name)
        else:
            print("MenuManager: 設置菜單為 None (堆棧已清空)")

    def draw(self):
        """
        繪製菜單堆棧中的所有菜單，從底部到頂部。
        這允許菜單疊加顯示。
        """
        if self.menu_stack:
            for menu in self.menu_stack:
                menu.draw(self.screen)  # 繪製所有菜單
            pygame.display.flip()  # 更新螢幕顯示

    def handle_event(self, event):
        """
        處理菜單相關的事件。

        只將事件傳遞給堆棧頂部的菜單處理。
        """
        current_menu = self.get_current_menu()
        
        if current_menu:
            result = current_menu.handle_event(event)  # 將事件傳遞給堆棧頂部菜單
            print(f"MenuManager: 處理事件 {current_menu.__class__.__name__}，結果：{result}")

            # 根據菜單返回的標準動作進行操作
            if result == 'EXIT_MENU' or result == 'BACK' or result == 'CONFIRM_CLOSE':
                self.pop_menu()
                # 檢查 pop_menu 後是否回到主遊戲狀態
                if not self.get_current_menu() and self.game.event_manager.state == 'menu':
                    # 如果堆棧為空且狀態仍為菜單，則通知遊戲返回上一狀態
                    # 假設返回 'GAME_STATE_CHANGE' 讓 EventManager 處理
                    return 'RETURN_TO_GAME_STATE' 
                return 'MENU_CLOSED' # 通知上層迴圈菜單已關閉

            # 原有的特定菜單邏輯（建議在菜單類本身或 Game 類中處理）
            if current_menu.__class__.__name__ == "SettingsMenu" and result in ["toggle_sound", "back"]:
                if result == "toggle_sound":
                    print("MenuManager: 正在切換音效（尚未實現）")
                elif result == "back":
                    self.pop_menu() # 只需要彈出菜單，不再需要 game.hide_menu
                return ""
                
            return result
        return ""
    
    def update_current_menus(self, delta_time: float) -> None:
        """更新當前堆棧中的所有菜單（如果需要）。"""
        for menu in self.menu_stack:
            menu.update(delta_time)