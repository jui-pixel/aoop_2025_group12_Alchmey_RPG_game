# src/dungeon/bsp_node.py
from dataclasses import dataclass
from typing import Optional
from src.dungeon.room import Room  # 引入 Room 類型，用於表示 BSP 樹節點中的房間
# 定義 BSP 樹節點，用於二元空間分割
@dataclass
class BSPNode:
    x: float  # 節點左上角的 x 座標（瓦片單位）
    y: float  # 節點左上角的 y 座標（瓦片單位）
    width: float  # 節點的寬度（瓦片單位）
    height: float  # 節點的高度（瓦片單位）
    room: Optional[Room] = None  # 節點包含的房間物件（若為葉節點，則有房間；否則為 None）
    left: Optional['BSPNode'] = None  # 左子節點（分割後的左半部分）
    right: Optional['BSPNode'] = None  # 右子節點（分割後的右半部分）