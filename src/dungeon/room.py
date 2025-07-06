# src/dungeon/room.py
from typing import List, Tuple
from dataclasses import dataclass
# 定義房間數據結構，用於儲存房間的屬性和瓦片數據
@dataclass
class Room:
    # 房間類，用來表示地牢中的單個房間，包含位置、尺寸、瓦片等資訊
    id: int  # 房間的唯一標識符，每個房間有獨一無二的 ID
    x: float  # 房間左上角的 x 座標（瓦片單位）
    y: float  # 房間左上角的 y 座標（瓦片單位）
    width: float  # 房間的寬度（以瓦片數為單位）
    height: float  # 房間的高度（以瓦片數為單位）
    tiles: List[List[str]]  # 房間的瓦片陣列，儲存每個瓦片的類型（例如 'Room_floor'、'Room_wall'、'End_room_portal'）
    connections: List[Tuple[int, str]] = None  # 房間連接到其他房間的列表，包含目標房間 ID 和方向（預設為 None）
    is_end_room: bool = False  # 是否為終點房間（終點房間有特殊瓦片和傳送門）

    # 初始化後處理，確保 connections 為空列表
    def __post_init__(self):
        # __post_init__ 是 dataclass 的特殊方法，在物件創建後自動執行
        # 檢查 connections 是否為 None，若是則設為空列表，確保後續操作不會出錯
        if self.connections is None:
            self.connections = []