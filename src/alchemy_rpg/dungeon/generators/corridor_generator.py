# src/dungeon/generators/corridor_generator.py
"""
走廊生成器模塊
負責在房間之間生成走廊
"""
from typing import List, Tuple, Set
from ..room import Room
from ..algorithms.pathfinding import AStarPathfinder
from ..config.dungeon_config import DungeonConfig


class CorridorGenerator:
    """
    走廊生成器
    
    使用 A* 尋路算法在房間之間生成走廊，
    將路徑上的瓦片轉換為 Bridge_floor。
    """
    
    def __init__(self, config: DungeonConfig, pathfinder: AStarPathfinder):
        """
        初始化走廊生成器
        
        Args:
            config: 地牢配置
            pathfinder: A* 尋路器
        """
        self.config = config
        self.pathfinder = pathfinder
    
    def generate_corridors(self, 
                          rooms: List[Room], 
                          connections: List[Tuple[int, int]],
                          grid: List[List[str]]) -> None:
        """
        生成走廊連接房間
        
        Args:
            rooms: 房間列表
            connections: 連接列表 [(room1_id, room2_id), ...]
            grid: 瓦片網格
        """
        for room1_id, room2_id in connections:
            if room1_id < len(rooms) and room2_id < len(rooms):
                self._create_corridor(rooms[room1_id], rooms[room2_id], grid)
    
    def _create_corridor(self, room1: Room, room2: Room, grid: List[List[str]]) -> None:
        """
        在兩個房間之間創建走廊
        
        Args:
            room1: 第一個房間
            room2: 第二個房間
            grid: 瓦片網格
        """
        # 獲取房間的連接點
        start = self._get_room_edge_point(room1, room2)
        end = self._get_room_edge_point(room2, room1)
        
        # 使用 A* 尋找路徑
        path = self.pathfinder.find_path(start, end, allow_diagonal=False)
        
        if not path:
            print(f"Warning: Could not find path between rooms {room1.id} and {room2.id}")
            return
        
        # 將路徑上的瓦片轉換為 Bridge_floor
        self._apply_path_to_grid(path, grid)
    
    def _get_room_edge_point(self, room: Room, target_room: Room) -> Tuple[int, int]:
        """
        獲取房間邊緣最接近目標房間的點
        
        Args:
            room: 當前房間
            target_room: 目標房間
        
        Returns:
            (x, y) 邊緣點座標
        """
        # 計算房間中心
        cx = int(room.x + room.width / 2)
        cy = int(room.y + room.height / 2)
        
        # 計算目標房間中心
        tcx = int(target_room.x + target_room.width / 2)
        tcy = int(target_room.y + target_room.height / 2)
        
        # 根據方向選擇邊緣點
        if abs(tcx - cx) > abs(tcy - cy):
            # 水平方向更遠
            if tcx > cx:
                # 目標在右側，選擇右邊緣
                x = int(room.x + room.width - 2)
            else:
                # 目標在左側，選擇左邊緣
                x = int(room.x + 2)
            y = cy
        else:
            # 垂直方向更遠
            x = cx
            if tcy > cy:
                # 目標在下方，選擇下邊緣
                y = int(room.y + room.height - 2)
            else:
                # 目標在上方，選擇上邊緣
                y = int(room.y + 2)
        
        return x, y
    
    def _apply_path_to_grid(self, path: List[Tuple[int, int]], grid: List[List[str]]) -> None:
        """
        將路徑應用到網格（轉換為 Bridge_floor）
        
        Args:
            path: 路徑座標列表
            grid: 瓦片網格
        """
        for x, y in path:
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                # 只轉換 Outside 瓦片
                if grid[y][x] == 'Outside':
                    grid[y][x] = 'Bridge_floor'
    
    def expand_corridors(self, grid: List[List[str]]) -> None:
        """
        膨脹走廊（將相鄰的 Outside 轉為 Bridge_floor）
        
        Args:
            grid: 瓦片網格
        """
        height = len(grid)
        width = len(grid[0]) if grid else 0
        
        # 找出所有 Bridge_floor 瓦片
        bridge_tiles = set()
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 'Bridge_floor':
                    bridge_tiles.add((x, y))
        
        # 膨脹：將相鄰的 Outside 轉為 Bridge_floor
        to_expand = set()
        for x, y in bridge_tiles:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if grid[ny][nx] == 'Outside':
                        to_expand.add((nx, ny))
        
        # 應用膨脹
        for x, y in to_expand:
            grid[y][x] = 'Bridge_floor'
