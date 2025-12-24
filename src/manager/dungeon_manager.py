# src/dungeon_manager.py
from typing import Tuple
from src.dungeon.dungeon import Dungeon
from src.dungeon.room import Room
from src.core.config import TILE_SIZE

class DungeonManager:
    def __init__(self, game: 'Game'):
        """初始化地牢管理器，負責管理地牢和房間。
        
        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.game = game
        self.dungeon = Dungeon()
        self.dungeon.game = game
        self.current_room_id = 0
        
        # 加載地牢配置
        self.dungeon_flow = self._load_dungeon_flow()
        self.current_dungeon_config = None # 當前地牢的配置數據
        
    def _load_dungeon_flow(self) -> dict:
        import json
        import os
        from src.utils.helpers import get_project_path
        
        try:
            path = get_project_path("src", "assets", "config", "dungeon_flow.json")
            if not os.path.exists(path):
                print(f"DungeonManager: Config file not found at {path}")
                return {}
                
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"DungeonManager: Loaded dungeon flow config.")
                return data
        except Exception as e:
            print(f"DungeonManager: Failed to load dungeon flow: {e}")
            return {}

    def initialize_dungeon(self, dungeon_id: int) -> None:
        """初始化整個地牢。"""
        # 1. 從 JSON 獲取配置
        dungeon_data = self.dungeon_flow.get("dungeons", {}).get(str(dungeon_id))
        
        if dungeon_data:
            print(f"DungeonManager: Initializing Dungeon {dungeon_id} ({dungeon_data.get('name')})")
            
            # 應用配置到 DungeonConfig
            config_data = dungeon_data.get("config", {})
            self.dungeon.config.grid_width = config_data.get("grid_width", 120)
            self.dungeon.config.grid_height = config_data.get("grid_height", 100)
            self.dungeon.config.monster_room_ratio = config_data.get("monster_room_ratio", 0.8)
            
            # 儲存配置供 EntityManager 使用 (Portal 數據)
            self.current_dungeon_config = dungeon_data
        else:
            print(f"DungeonManager: No config found for Dungeon ID {dungeon_id}, using defaults.")
            self.current_dungeon_config = None

        self.dungeon.initialize_dungeon(dungeon_id)
        self.current_room_id = 1
    
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