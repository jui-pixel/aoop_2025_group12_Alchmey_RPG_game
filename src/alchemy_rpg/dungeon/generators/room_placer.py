# src/dungeon/generators/room_placer.py
"""
房間放置器模塊
負責在 BSP 樹中放置房間
"""
import random
from typing import List, Tuple
from ..room import Room
from ..bsp_node import BSPNode
from ..config.dungeon_config import DungeonConfig


class RoomPlacer:
    """
    房間放置器
    
    在 BSP 樹的葉節點中放置房間，
    確保房間符合尺寸限制和間距要求。
    """
    
    def __init__(self, config: DungeonConfig):
        """
        初始化房間放置器
        
        Args:
            config: 地牢配置
        """
        self.config = config
        self.next_room_id = 0
    
    def place_rooms_in_bsp(self, bsp_tree: BSPNode) -> List[Room]:
        """
        在 BSP 樹的葉節點中放置房間
        
        Args:
            bsp_tree: BSP 樹的根節點
        
        Returns:
            房間列表
        """
        rooms = []
        self._place_rooms_recursive(bsp_tree, rooms)
        return rooms
    
    def _place_rooms_recursive(self, node: BSPNode, rooms: List[Room]) -> None:
        """
        遞歸在葉節點中放置房間
        
        Args:
            node: 當前節點
            rooms: 房間列表
        """
        if node.left is None and node.right is None:
            # 葉節點，嘗試放置房間
            if self._can_place_room(node):
                room = self._create_room_in_node(node)
                node.room = room
                rooms.append(room)
        else:
            # 非葉節點，遞歸處理子節點
            if node.left:
                self._place_rooms_recursive(node.left, rooms)
            if node.right:
                self._place_rooms_recursive(node.right, rooms)
    
    def _can_place_room(self, node: BSPNode) -> bool:
        """
        檢查節點是否可以放置房間
        
        Args:
            node: BSP 節點
        
        Returns:
            是否可以放置房間
        """
        # 考慮 ROOM_GAP 後的可用空間
        available_width = node.width - 2 * self.config.room_gap
        available_height = node.height - 2 * self.config.room_gap
        
        return (available_width >= self.config.min_room_size and 
                available_height >= self.config.min_room_size)
    
    def _create_room_in_node(self, node: BSPNode) -> Room:
        """
        在節點中創建房間
        
        Args:
            node: BSP 節點
        
        Returns:
            創建的房間
        """
        # 計算房間邊界
        room_x, room_y, room_width, room_height = self._calculate_room_bounds(node)
        
        # 創建房間
        room = Room(
            id=self.next_room_id,
            x=room_x,
            y=room_y,
            width=room_width,
            height=room_height,
        )
        
        self.next_room_id += 1
        return room
    
    def _calculate_room_bounds(self, node: BSPNode) -> Tuple[float, float, float, float]:
        """
        計算房間在節點中的邊界
        
        Args:
            node: BSP 節點
        
        Returns:
            (room_x, room_y, room_width, room_height)
        """
        # 預留 ROOM_GAP
        room_x = node.x + self.config.room_gap
        room_y = node.y + self.config.room_gap
        
        # 計算最大可用空間
        max_width = node.width - 2 * self.config.room_gap
        max_height = node.height - 2 * self.config.room_gap
        
        # 限制在配置的最大尺寸內
        room_width = min(max_width, self.config.room_width)
        room_height = min(max_height, self.config.room_height)
        
        # 確保不小於最小尺寸
        room_width = max(room_width, self.config.min_room_size)
        room_height = max(room_height, self.config.min_room_size)
        
        return room_x, room_y, room_width, room_height
    
    def get_room_center(self, room: Room) -> Tuple[float, float]:
        """
        獲取房間中心點
        
        Args:
            room: 房間
        
        Returns:
            (center_x, center_y)
        """
        return (
            room.x + room.width / 2,
            room.y + room.height / 2
        )
    
    def get_room_connection_point(self, room: Room) -> Tuple[int, int]:
        """
        獲取房間的連接點（用於走廊連接）
        
        Args:
            room: 房間
        
        Returns:
            (x, y) 連接點座標
        """
        # 在房間內部隨機選擇一個點（避開邊緣）
        x = random.randint(int(room.x + 2), int(room.x + room.width - 3))
        y = random.randint(int(room.y + 2), int(room.y + room.height - 3))
        return x, y
    
    def get_room_midpoints(self, room: Room, jitter: float = 0.0) -> List[Tuple[float, float]]:
        """
        獲取房間的四個中點（用於圖構建）
        
        Args:
            room: 房間
            jitter: 隨機抖動量
        
        Returns:
            四個中點的座標列表
        """
        cx, cy = self.get_room_center(room)
        
        midpoints = [
            (room.x + room.width / 4, cy),  # 左中
            (room.x + 3 * room.width / 4, cy),  # 右中
            (cx, room.y + room.height / 4),  # 上中
            (cx, room.y + 3 * room.height / 4),  # 下中
        ]
        
        # 添加隨機抖動
        if jitter > 0:
            midpoints = [
                (x + random.uniform(-jitter, jitter), 
                 y + random.uniform(-jitter, jitter))
                for x, y in midpoints
            ]
        
        return midpoints
