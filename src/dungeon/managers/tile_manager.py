# src/dungeon/managers/tile_manager.py
"""
瓦片管理器模塊
負責瓦片網格的操作和管理
"""
from typing import List, Set, Tuple
from ..room import Room


class TileManager:
    """
    瓦片管理器
    
    管理地牢的瓦片網格，提供瓦片操作、
    房間放置、邊界添加等功能。
    """
    
    def __init__(self, width: int, height: int, default_tile: str = 'Outside'):
        """
        初始化瓦片管理器
        
        Args:
            width: 網格寬度
            height: 網格高度
            default_tile: 默認瓦片類型
        """
        self.width = width
        self.height = height
        self.grid = [[default_tile for _ in range(width)] for _ in range(height)]
    
    def place_room(self, room: Room) -> None:
        """
        將房間放置到網格
        
        Args:
            room: 要放置的房間
        """
        # 獲取房間的瓦片數據
        room_tiles = room.get_tiles()
        
        # 放置到網格
        for local_y, row in enumerate(room_tiles):
            for local_x, tile in enumerate(row):
                grid_x = int(room.x + local_x)
                grid_y = int(room.y + local_y)
                
                if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                    self.grid[grid_y][grid_x] = tile
    
    def add_room_borders(self, rooms: List[Room]) -> None:
        """
        為所有房間添加邊界牆
        
        Args:
            rooms: 房間列表
        """
        for room in rooms:
            self._add_border_to_room(room)
    
    def _add_border_to_room(self, room: Room) -> None:
        """
        為單個房間添加邊界牆
        
        Args:
            room: 房間
        """
        x_start = int(room.x)
        y_start = int(room.y)
        x_end = int(room.x + room.width)
        y_end = int(room.y + room.height)
        
        # 添加邊界（在房間外圍一圈）
        for y in range(max(0, y_start - 1), min(self.height, y_end + 1)):
            for x in range(max(0, x_start - 1), min(self.width, x_end + 1)):
                # 檢查是否在邊界上
                is_border = (x == x_start - 1 or x == x_end or 
                           y == y_start - 1 or y == y_end)
                
                if is_border and self.grid[y][x] == 'Outside':
                    self.grid[y][x] = self._get_border_wall_type(
                        x, y, x_start, y_start, x_end, y_end
                    )
    
    def _get_border_wall_type(self, x: int, y: int, 
                             x_start: int, y_start: int, 
                             x_end: int, y_end: int) -> str:
        """
        獲取邊界牆的具體類型（角落、邊等）
        
        Args:
            x, y: 當前座標
            x_start, y_start: 房間起始座標
            x_end, y_end: 房間結束座標
        
        Returns:
            邊界牆類型
        """
        # 四個角
        if x == x_start - 1 and y == y_start - 1:
            return 'Border_wall_top_left_corner'
        elif x == x_end and y == y_start - 1:
            return 'Border_wall_top_right_corner'
        elif x == x_start - 1 and y == y_end:
            return 'Border_wall_bottom_left_corner'
        elif x == x_end and y == y_end:
            return 'Border_wall_bottom_right_corner'
        
        # 四條邊
        elif y == y_start - 1:
            return 'Border_wall_top'
        elif y == y_end:
            return 'Border_wall_bottom'
        elif x == x_start - 1:
            return 'Border_wall_left'
        elif x == x_end:
            return 'Border_wall_right'
        
        return 'Border_wall'
    
    def get_tile(self, x: int, y: int) -> str:
        """
        獲取指定位置的瓦片
        
        Args:
            x, y: 座標
        
        Returns:
            瓦片類型
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return 'Outside'
    
    def set_tile(self, x: int, y: int, tile: str) -> None:
        """
        設置指定位置的瓦片
        
        Args:
            x, y: 座標
            tile: 瓦片類型
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = tile
    
    def count_tiles(self, tile_type: str) -> int:
        """
        統計指定類型瓦片的數量
        
        Args:
            tile_type: 瓦片類型
        
        Returns:
            數量
        """
        count = 0
        for row in self.grid:
            for tile in row:
                if tile == tile_type:
                    count += 1
        return count
    
    def find_tiles(self, tile_type: str) -> List[Tuple[int, int]]:
        """
        找出所有指定類型的瓦片位置
        
        Args:
            tile_type: 瓦片類型
        
        Returns:
            座標列表
        """
        positions = []
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                if tile == tile_type:
                    positions.append((x, y))
        return positions
    
    def replace_tiles(self, old_tile: str, new_tile: str) -> int:
        """
        替換所有指定類型的瓦片
        
        Args:
            old_tile: 舊瓦片類型
            new_tile: 新瓦片類型
        
        Returns:
            替換的數量
        """
        count = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == old_tile:
                    self.grid[y][x] = new_tile
                    count += 1
        return count
    
    def get_neighbors(self, x: int, y: int, include_diagonal: bool = False) -> List[Tuple[int, int, str]]:
        """
        獲取鄰居瓦片
        
        Args:
            x, y: 座標
            include_diagonal: 是否包含對角線
        
        Returns:
            [(x, y, tile), ...] 鄰居列表
        """
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        if include_diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny, self.grid[ny][nx]))
        
        return neighbors
