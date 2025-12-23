# src/dungeon_manager.py
from typing import Tuple
from .dungeon.dungeon import Dungeon
from .dungeon.room import Room
from .core.config import TILE_SIZE

class DungeonManager:
    def __init__(self, game: 'Game'):
        """初始化地牢管理器，負責管理地牢和房間。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.game = game  # 保存遊戲實例引用
        self.dungeon = Dungeon()  # 創建一個新的地牢實例
        self.dungeon.game = game  # 將遊戲實例設置到地牢中
        self.current_room_id = 0  # 當前房間的 ID，初始為 0（大廳）

    def initialize_dungeon(self, dungeon_id: int) -> None:
        """初始化整個地牢。

        調用地牢的 initialize_dungeon 方法來生成地牢結構和房間。
        """
        self.dungeon.initialize_dungeon(dungeon_id)
        self.current_room_id = 1  # 將當前房間設置為第一個房間（非大廳）
    
    def initialize_lobby(self) -> None:
        """初始化大廳房間。

        調用地牢的 initialize_lobby 方法來設置大廳房間。
        """
        self.dungeon.initialize_lobby()
        self.current_room_id = 0  # 將當前房間設置為大廳

    def get_current_room(self) -> Room:
        """獲取當前房間。

        Returns:
            Room: 當前房間的實例。
        """
        return self.dungeon.rooms[self.current_room_id]

    def get_room_center(self, room: Room) -> Tuple[float, float]:
        """計算房間的中心座標（以像素為單位）。

        Args:
            room: 要計算中心座標的房間。

        Returns:
            Tuple[float, float]: 房間中心的像素座標 (x, y)。
        """
        return (
            (room.x + room.width / 2) * TILE_SIZE,  # 計算房間中心的 x 座標
            (room.y + room.height / 2) * TILE_SIZE   # 計算房間中心的 y 座標
        )

    def switch_room(self, new_room_id: int) -> bool:
        """切換到指定的房間。

        Args:
            new_room_id: 要切換到的房間 ID。

        Returns:
            bool: 如果切換成功返回 True，否則返回 False。
        """
        if 0 <= new_room_id < len(self.dungeon.rooms):
            self.current_room_id = new_room_id  # 更新當前房間 ID
            return True
        return False

    def get_dungeon(self) -> Dungeon:
        """獲取地牢實例。

        Returns:
            Dungeon: 當前地牢實例。
        """
        return self.dungeon