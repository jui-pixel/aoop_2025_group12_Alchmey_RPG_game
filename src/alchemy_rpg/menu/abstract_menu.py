# src/menu/abstract_menu.py
from abc import ABC, abstractmethod

class AbstractMenu(ABC):
    @abstractmethod
    def draw(self, screen): pass  # 繪製選單
    @abstractmethod
    def handle_event(self, event): pass  # 處理輸入事件
    @abstractmethod
    def get_selected_action(self): pass  # 獲取當前選中動作
    @abstractmethod
    def activate(self, active: bool): pass  # 啟用/禁用選單
    
    def get_name(self) -> str:
        """獲取菜單名稱"""
        return self.__class__.__name__
    
    def update(self, delta_time: float) -> None:
        """更新菜單狀態（可選）"""
        pass