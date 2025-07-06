# src/dungeon/room.py
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum

# 定義房間類型枚舉，表示地牢中房間的不同功能
class RoomType(Enum):
    EMPTY = "empty"  # 空房間，沒有特殊功能
    START = "start"  # 出生點房間，玩家的起始位置
    MONSTER = "monster"  # 怪物房，包含敵人
    TRAP = "trap"  # 陷阱房，包含危險陷阱
    REWARD = "reward"  # 獎勵房，包含寶藏或道具
    END = "end"  # 終點房間，包含傳送門

# 定義房間數據結構，用於儲存房間的屬性和瓦片數據
@dataclass
class Room:
    # 房間類，用來表示地牢中的單個房間，包含位置、尺寸、瓦片和類型等資訊
    id: int  # 房間的唯一標識符，每個房間有獨一無二的 ID
    x: float  # 房間左上角的 x 座標（瓦片單位）
    y: float  # 房間左上角的 y 座標（瓦片單位）
    width: float  # 房間的寬度（以瓦片數為單位）
    height: float  # 房間的高度（以瓦片數為單位）
    tiles: List[List[str]]  # 房間的瓦片陣列，儲存每個瓦片的類型（例如 'Room_floor'、'End_room_portal'）
    room_type: RoomType = RoomType.EMPTY  # 房間的類型，預設為空房間
    connections: List[Tuple[int, str]] = None  # 房間連接到其他房間的列表，包含目標房間 ID 和方向（預設為 None）

    def __post_init__(self):
        # 初始化後處理，確保 connections 為空列表
        if self.connections is None:
            self.connections = []
        # 根據房間類型設置瓦片
        self._configure_tiles()

    def _configure_tiles(self) -> None:
        """根據房間類型配置瓦片"""
        if self.room_type == RoomType.END:
            # 終點房間：設置內部為 End_room_floor，中間放置傳送門
            for row in range(1, int(self.height) - 1):
                for col in range(1, int(self.width) - 1):
                    self.tiles[row][col] = 'End_room_floor'
            center_x = int(self.width) // 2
            center_y = int(self.height) // 2
            self.tiles[center_y][center_x] = 'End_room_portal'
        # 未來可為其他房間類型（如 MONSTER、TRAP、REWARD）添加特殊瓦片邏輯

    @property
    def is_end_room(self) -> bool:
        """檢查房間是否為終點房間，向後相容"""
        return self.room_type == RoomType.END