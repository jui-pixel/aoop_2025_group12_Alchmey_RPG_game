# src/dungeon/algorithms/pathfinding.py
"""
A* 尋路算法模塊
提供獨立的尋路功能
"""
import heapq
from typing import List, Tuple, Set, Dict, Optional, Callable


class AStarPathfinder:
    """
    A* 尋路算法
    
    使用 A* 算法在網格中尋找最短路徑，
    支持自定義瓦片成本和啟發式函數。
    """
    
    def __init__(self, 
                 grid: List[List[str]], 
                 passable_tiles: Optional[Set[str]] = None,
                 cost_map: Optional[Dict[str, float]] = None):
        """
        初始化尋路器
        
        Args:
            grid: 瓦片網格
            passable_tiles: 可通過的瓦片類型集合（如果為 None，則所有瓦片都可通過）
            cost_map: 瓦片類型到成本的映射（默認所有瓦片成本為 1.0）
        """
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0
        self.passable_tiles = passable_tiles
        self.cost_map = cost_map or {}
    
    def find_path(self, 
                  start: Tuple[int, int], 
                  end: Tuple[int, int],
                  allow_diagonal: bool = False) -> List[Tuple[int, int]]:
        """
        使用 A* 算法尋找路徑
        
        Args:
            start: 起點座標 (x, y)
            end: 終點座標 (x, y)
            allow_diagonal: 是否允許對角線移動
        
        Returns:
            路徑座標列表，如果無法到達則返回空列表
        """
        # 驗證起點和終點
        if not self._is_valid(start) or not self._is_valid(end):
            return []
        
        # 初始化
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        f_score: Dict[Tuple[int, int], float] = {start: self._heuristic(start, end)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            # 到達終點
            if current == end:
                return self._reconstruct_path(came_from, current)
            
            # 探索鄰居
            for neighbor in self._get_neighbors(current, allow_diagonal):
                # 計算到鄰居的成本
                tile_cost = self._get_tile_cost(neighbor)
                tentative_g_score = g_score[current] + tile_cost
                
                # 如果找到更好的路徑
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, end)
                    
                    # 添加到 open set
                    if neighbor not in [item[1] for item in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # 無法到達
        return []
    
    def _is_valid(self, pos: Tuple[int, int]) -> bool:
        """
        檢查位置是否有效
        
        Args:
            pos: 位置座標 (x, y)
        
        Returns:
            位置是否有效
        """
        x, y = pos
        
        # 檢查邊界
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        
        # 檢查是否可通過
        if self.passable_tiles is not None:
            tile = self.grid[y][x]
            if tile not in self.passable_tiles:
                # 特殊處理：Outside 瓦片在尋路時視為可通過
                if tile != 'Outside':
                    return False
        
        return True
    
    def _get_tile_cost(self, pos: Tuple[int, int]) -> float:
        """
        獲取瓦片的移動成本
        
        Args:
            pos: 位置座標 (x, y)
        
        Returns:
            移動成本
        """
        x, y = pos
        tile = self.grid[y][x]
        return self.cost_map.get(tile, 1.0)
    
    def _get_neighbors(self, pos: Tuple[int, int], allow_diagonal: bool) -> List[Tuple[int, int]]:
        """
        獲取有效的鄰居節點
        
        Args:
            pos: 當前位置 (x, y)
            allow_diagonal: 是否允許對角線移動
        
        Returns:
            鄰居座標列表
        """
        x, y = pos
        neighbors = []
        
        # 四向移動
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        # 對角線移動
        if allow_diagonal:
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        
        for dx, dy in directions:
            neighbor = (x + dx, y + dy)
            if self._is_valid(neighbor):
                neighbors.append(neighbor)
        
        return neighbors
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """
        啟發式函數（曼哈頓距離）
        
        Args:
            a: 起點
            b: 終點
        
        Returns:
            估計距離
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _reconstruct_path(self, 
                         came_from: Dict[Tuple[int, int], Tuple[int, int]], 
                         current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        重建路徑
        
        Args:
            came_from: 父節點映射
            current: 當前節點（終點）
        
        Returns:
            從起點到終點的路徑
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
    
    def find_multiple_paths(self,
                           start: Tuple[int, int],
                           ends: List[Tuple[int, int]],
                           allow_diagonal: bool = False) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
        """
        從一個起點到多個終點尋找路徑
        
        Args:
            start: 起點
            ends: 終點列表
            allow_diagonal: 是否允許對角線移動
        
        Returns:
            終點到路徑的映射
        """
        paths = {}
        for end in ends:
            path = self.find_path(start, end, allow_diagonal)
            if path:
                paths[end] = path
        return paths
    
    def get_reachable_tiles(self,
                           start: Tuple[int, int],
                           max_distance: Optional[int] = None) -> Set[Tuple[int, int]]:
        """
        獲取從起點可到達的所有瓦片
        
        Args:
            start: 起點
            max_distance: 最大距離（None 表示無限制）
        
        Returns:
            可到達的瓦片集合
        """
        if not self._is_valid(start):
            return set()
        
        visited = {start}
        queue = [(start, 0)]
        
        while queue:
            current, distance = queue.pop(0)
            
            if max_distance is not None and distance >= max_distance:
                continue
            
            for neighbor in self._get_neighbors(current, False):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1))
        
        return visited
