# src/menu_manager.py
from src.menu.abstract_menu import AbstractMenu
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from typing import List, Optional, Union
from src.menu.menu_config import (
    BasicAction,
)
from src.menu.menus.alchemy_menu import AlchemyMenu
from src.menu.menus.amplifier_menu import AmplifierMenu
from src.menu.menus.amplifier_stat_menu import AmplifierStatMenu
from src.menu.menus.crystal_menu import CrystalMenu
from src.menu.menus.dungeon_menu import DungeonMenu
from src.menu.menus.element_menu import ElementMenu
from src.menu.menus.main_menu import MainMenu
from src.menu.menus.main_material_menu import MainMaterialMenu
from src.menu.menus.element_choose_menu import ElementChooseMenu
from src.menu.menus.stat_menu import StatMenu
from src.menu.menus.amplifier_choose_menu import AmplifierChooseMenu
from src.menu.menus.naming_menu import NamingMenu
from src.menu.menus.skill_library_menu import SkillLibraryMenu
from src.menu.menus.skill_chain_edit_menu import SkillChainEditMenu
from src.menu.menus.skill_chain_menu import SkillChainMenu
from src.menu.menus.setting_menu import SettingsMenu

class MenuManager:
    def __init__(self, game):
        """初始化菜單管理器，負責管理遊戲中的各個菜單。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.screen = game.screen  # 保存 Pygame 顯示表面
        self.game = game  # 保存遊戲實例引用
        self.menus = {}  # 用於儲存所有菜單的字典，鍵為菜單名稱，值為菜單實例
        self.active_menus: List[AbstractMenu] = []  # 當前激活的菜單列表（同時顯示）
        self.font = pygame.font.SysFont(None, 48)  # 初始化字體，字體大小為 48

    def register_menu(self, menu_name: str, menu: AbstractMenu = None, update = False) -> None:
        """註冊一個菜單。

        Args:
            menu_name: 菜單的名稱。
            menu: 菜單實例（AbstractMenu 的子類），可以為 None（延遲初始化）。
            update: 如果菜單已存在，是否更新其實例。
        """
        if menu_name in self.menus and self.menus[menu_name] is not None:
            if update:
                print(f"MenuManager: 菜單 {menu_name} 已存在，正在更新實例。")
                self.menus[menu_name] = menu
            else:
                print(f"MenuManager: 菜單 {menu_name} 已存在，且未強制更新 ，因此無法重複註冊")
            return
        self.menus[menu_name] = menu
        if menu is not None:
            menu.activate(False)  # 設置菜單為非激活狀態
        print(f"MenuManager: 已註冊菜單 {menu_name}，實例：{menu.__class__.__name__ if menu else 'None'}")

    # =====================================================================
    #  核心列表邏輯：open_menu, close_menu, close_all_menus
    # =====================================================================

    def open_menu(self, menu_name: str, data = None) -> None:
        """
        打開指定菜單並添加到激活列表。
        如果菜單已經在列表中，則不重複添加。
        
        Args:
            menu_name: 要打開的菜單名稱
        """
        if menu_name not in self.menus or self.menus[menu_name] is None:
            print(f"MenuManager: 菜單 {menu_name} 尚未註冊或未實例化。")
            if menu_name == "alchemy_menu":
                self.register_menu(menu_name, AlchemyMenu(self.game, data))
            elif menu_name == "amplifier_menu":
                self.register_menu(menu_name, AmplifierMenu(self.game, data))
            elif menu_name == 'amplifier_stat_menu':
                self.register_menu(menu_name, AmplifierStatMenu(self.game, data))
            elif menu_name == 'crystal_menu':
                self.register_menu(menu_name, CrystalMenu(self.game, data))
            elif menu_name == 'element_menu':
                self.register_menu(menu_name, ElementMenu(self.game, data))
            elif menu_name == 'main_material_menu':
                self.register_menu(menu_name, MainMaterialMenu(self.game, data))
            elif menu_name == 'element_choose_menu':
                self.register_menu(menu_name, ElementChooseMenu(self.game, data))
            elif menu_name == 'stat_menu':
                self.register_menu(menu_name, StatMenu(self.game, data))
            elif menu_name == 'amplifier_choose_menu':
                self.register_menu(menu_name, AmplifierChooseMenu(self.game, data))
            elif menu_name == 'naming_menu':
                self.register_menu(menu_name, NamingMenu(self.game, data))
            elif menu_name == 'skill_library_menu':
                self.register_menu(menu_name, SkillLibraryMenu(self.game, data))
            elif menu_name == 'settings_menu':
                self.register_menu(menu_name, SettingsMenu(self.game, data))
            elif menu_name == 'skill_chain_menu':
                self.register_menu(menu_name, SkillChainMenu(self.game, data))
            elif menu_name == 'skill_chain_edit_menu':
                self.register_menu(menu_name, SkillChainEditMenu(self.game, data))
            elif menu_name == 'dungeon_menu':
                    # 【修正點】解包 data 並將其傳遞給 DungeonMenu
                    dungeons = data.get('dungeons', []) if isinstance(data, dict) else data 
                    npc_facade = data.get('npc_facade') if isinstance(data, dict) else None
                    
                    if not isinstance(dungeons, list):
                        dungeons = data 
                        npc_facade = None 

                    self.register_menu(menu_name, DungeonMenu(self.game, dungeons, npc_facade))
            self.active_menus.append(self.menus[menu_name])
            self.menus[menu_name].activate(True)
            return

        menu = self.menus[menu_name]
        
        # 檢查菜單是否已經在激活列表中
        if menu in self.active_menus:
            print(f"MenuManager: 菜單 {menu_name} 已經打開，不重複添加。")
            return

        # 添加到激活列表並激活
        self.active_menus.append(menu)
        menu.activate(True)
        print(f"MenuManager: 打開菜單 {menu_name}. 當前激活菜單數: {len(self.active_menus)}")

    def close_menu(self, menu_identifier: Union[str, AbstractMenu]) -> bool:
        """
        關閉指定的菜單（通過名稱或實例）。
        可以獨立關閉任何一個菜單，不需要按順序。
        
        Args:
            menu_identifier: 菜單名稱（字符串）或菜單實例
            
        Returns:
            bool: 如果成功關閉返回 True，否則返回 False
        """
        menu_to_close = None
        
        # 根據標識符類型找到要關閉的菜單
        if isinstance(menu_identifier, str):
            # 通過名稱查找
            if menu_identifier in self.menus:
                menu_to_close = self.menus[menu_identifier]
        else:
            # 直接使用菜單實例
            menu_to_close = menu_identifier
        
        # 檢查菜單是否在激活列表中
        if menu_to_close and menu_to_close in self.active_menus:
            self.active_menus.remove(menu_to_close)
            menu_to_close.activate(False)
            menu_name = self._get_menu_name(menu_to_close)
            print(f"MenuManager: 關閉菜單 {menu_name}. 當前激活菜單數: {len(self.active_menus)}")
            return True
        else:
            print(f"MenuManager: 菜單 {menu_identifier} 未在激活列表中。")
            return False

    def close_all_menus(self) -> None:
        """關閉所有激活的菜單。"""
        for menu in self.active_menus[:]:  # 使用切片創建副本以避免迭代時修改列表
            menu.activate(False)
        self.active_menus.clear()
        print("MenuManager: 已關閉所有菜單。")

    def is_menu_open(self, menu_name: str) -> bool:
        """
        檢查指定菜單是否已打開。
        
        Args:
            menu_name: 菜單名稱
            
        Returns:
            bool: 如果菜單已打開返回 True，否則返回 False
        """
        if menu_name not in self.menus:
            return False
        menu = self.menus[menu_name]
        return menu in self.active_menus

    def get_active_menus(self) -> List[AbstractMenu]:
        """獲取所有激活的菜單列表。"""
        return self.active_menus.copy()

    # =====================================================================
    #  兼容性方法：保留舊接口以支持現有代碼
    # =====================================================================

    def push_menu(self, menu_name: str) -> None:
        """
        兼容性方法：推入菜單（等同於 open_menu）。
        保留此方法以支持現有代碼。
        """
        self.open_menu(menu_name)

    def pop_menu(self) -> Optional[AbstractMenu]:
        """
        兼容性方法：彈出最後打開的菜單。
        保留此方法以支持現有代碼。
        
        Returns:
            被關閉的菜單實例，如果沒有菜單則返回 None
        """
        if not self.active_menus:
            return None
        
        # 關閉最後一個菜單
        last_menu = self.active_menus[-1]
        self.close_menu(last_menu)
        return last_menu

    def get_current_menu(self) -> Optional[AbstractMenu]:
        """
        兼容性方法：獲取最後打開的菜單。
        保留此方法以支持現有代碼。
        """
        return self.active_menus[-1] if self.active_menus else None

    def set_menu(self, menu_name: Optional[str]) -> None:
        """
        兼容性方法：設置當前顯示的菜單。
        先關閉所有菜單，然後打開指定菜單。
        """
        self.close_all_menus()
        
        if menu_name:
            self.open_menu(menu_name)
        else:
            print("MenuManager: 設置菜單為 None (已關閉所有菜單)")

    # =====================================================================
    #  繪製與事件處理
    # =====================================================================

    def draw(self) -> None:
        """
        繪製所有激活的菜單，從第一個到最後一個。
        這允許多個菜單同時顯示。
        """
        if self.active_menus:
            for menu in self.active_menus:
                menu.draw(self.screen)  # 繪製所有激活的菜單
            pygame.display.flip()  # 更新螢幕顯示

    def handle_event(self, event: pygame.event.Event) -> str:
        """
        處理菜單相關的事件。
        
        事件處理順序：從最後打開的菜單開始（反向遍歷），
        這樣最上層的菜單優先處理事件。
        
        Args:
            event: Pygame 事件對象
            
        Returns:
            str: 菜單處理結果
        """
        if not self.active_menus:
            return ""
        
        # 從後往前遍歷（最後打開的菜單優先處理）
        for menu in reversed(self.active_menus):
            result = menu.handle_event(event)
            
            if result:  # 如果菜單處理了事件
                print(f"MenuManager: 處理事件 {menu.__class__.__name__}，結果：{result}")
                
                # 根據菜單返回的標準動作進行操作
                if result == BasicAction.EXIT_MENU:
                    self.close_menu(menu)
                    
                    # 檢查是否所有菜單都已關閉
                    if not self.active_menus and hasattr(self.game, 'event_manager') and self.game.event_manager.state == 'menu':
                        return 'RETURN_TO_GAME_STATE'
                    return 'MENU_CLOSED'

                # 特定菜單邏輯（建議在菜單類本身處理）
                if menu.__class__.__name__ == "SettingsMenu" and result in ["toggle_sound", "back"]:
                    if result == "toggle_sound":
                        print("MenuManager: 正在切換音效（尚未實現）")
                    elif result == "back":
                        self.close_menu(menu)
                    return ""
                
                # 事件已被處理，不再傳遞給下層菜單
                return result
        
        return ""
    
    def update_current_menus(self, delta_time: float) -> None:
        """更新所有激活的菜單。"""
        for menu in self.active_menus:
            menu.update(delta_time)

    # =====================================================================
    #  輔助方法
    # =====================================================================

    def _get_menu_name(self, menu: AbstractMenu) -> str:
        """
        根據菜單實例獲取菜單名稱。
        
        Args:
            menu: 菜單實例
            
        Returns:
            菜單名稱，如果找不到則返回類名
        """
        for name, registered_menu in self.menus.items():
            if registered_menu is menu:
                return name
        return menu.__class__.__name__