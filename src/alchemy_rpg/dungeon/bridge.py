# src/dungeon/bridge.py
from dataclasses import dataclass
# 定義 Bridge 類，用於表示房間之間的走廊
@dataclass
class Bridge:
    x0: float  # 走廊起點的 x 座標
    y0: float  # 走廊起點的 y 座標
    x1: float  # 走廊終點的 x 座標
    y1: float  # 走廊終點的 y 座標
    width: float  # 走廊的寬度（瓦片單位）
    room1_id: int  # 連接的第一個房間 ID
    room2_id: int  # 連接的第二個房間 ID