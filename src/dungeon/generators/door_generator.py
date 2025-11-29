# src/dungeon/generators/door_generator.py
"""
門生成器模塊
負責在房間邊界和走廊交界處生成門
"""
from typing import List


class DoorGenerator:
    """
    門生成器
    
    在邊界牆與走廊交界處生成門，
    使房間與走廊連接更自然。
    """
    
    def generate_doors(self, grid: List[List[str]]) -> None:
        """
        在邊界牆與走廊交界處生成門
        
        Args:
            grid: 瓦片網格
        """
        height = len(grid)
        width = len(grid[0]) if grid else 0
        
        for y in range(height):
            for x in range(width):
                if self._is_border_wall(grid[y][x]):
                    if self._should_be_door(grid, x, y, width, height):
                        grid[y][x] = 'Door'
    
    def _is_border_wall(self, tile: str) -> bool:
        """
        檢查瓦片是否為邊界牆
        
        Args:
            tile: 瓦片類型
        
        Returns:
            是否為邊界牆
        """
        return tile.startswith('Border_wall')
    
    def _should_be_door(self, grid: List[List[str]], x: int, y: int, 
                       width: int, height: int) -> bool:
        """
        檢查邊界牆是否應該轉換為門
        
        Args:
            grid: 瓦片網格
            x, y: 座標
            width, height: 網格尺寸
        
        Returns:
            是否應該轉換為門
        """
        # 檢查四個方向是否有 Bridge_floor
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if grid[ny][nx] == 'Bridge_floor':
                    return True
        
        return False
    
    def count_doors(self, grid: List[List[str]]) -> int:
        """
        統計門的數量
        
        Args:
            grid: 瓦片網格
        
        Returns:
            門的數量
        """
        count = 0
        for row in grid:
            for tile in row:
                if tile == 'Door':
                    count += 1
        return count
