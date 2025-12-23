# src/dungeon/managers/tile_manager.py
"""
瓦片管理器模塊
負責瓦片網格的操作和管理
"""
from typing import List, Set, Tuple
from ..room import Room
from src.core.config import PASSABLE_TILES

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
        # 轉移至adjust_wall方法處理更複雜的牆壁變體
        # # 四個角
        # if x == x_start - 1 and y == y_start - 1:
        #     return 'Border_wall_top_left_corner'
        # elif x == x_end and y == y_start - 1:
        #     return 'Border_wall_top_right_corner'
        # elif x == x_start - 1 and y == y_end:
        #     return 'Border_wall_bottom_left_corner'
        # elif x == x_end and y == y_end:
        #     return 'Border_wall_bottom_right_corner'
        
        # # 四條邊
        # elif y == y_start - 1:
        #     return 'Border_wall_top'
        # elif y == y_end:
        #     return 'Border_wall_bottom'
        # elif x == x_start - 1:
        #     return 'Border_wall_left'
        # elif x == x_end:
        #     return 'Border_wall_right'
        
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

    def finalize_walls(self, passable_tiles: Set[str]=PASSABLE_TILES) -> None:
        """
        協調牆壁生成和調整的步驟：
        1. 將緊鄰地板的 'Outside' 轉換為 'Border_wall' (走廊擴展後)
        2. 調整所有 'Border_wall' 的具體變體（凹凸角、獨立牆）
        
        Args:
            passable_tiles: 可通行瓦片類型集合。
        """
        # 第一步：將緊鄰可通行區的 'Outside' 轉為 'Border_wall'
        self._add_initial_walls(passable_tiles)
        
        # 第二步：調整牆壁變體
        self.adjust_wall(passable_tiles)


    def _add_initial_walls(self, passable_tiles: Set[str]=PASSABLE_TILES) -> None:
        """
        將所有緊鄰 PASSABLE_TILES 的 'Outside' 轉換為 'Border_wall'。
        （對應使用者提供的 _convert_outside_to_border_wall 邏輯）
        """
        to_border_wall: List[Tuple[int, int]] = []
        
        # 8 個方向 (含對角線)
        directions = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)] 
        
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 'Outside':
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            # 檢查鄰居是否是可通行瓦片
                            if self.grid[ny][nx] in passable_tiles:
                                to_border_wall.append((x, y))
                                break
                                
        for x, y in to_border_wall:
            self.grid[y][x] = 'Border_wall'
    
    
    def adjust_wall(self, passable_tiles: Set[str]=PASSABLE_TILES) -> None:
        """
        調整邊界牆壁為不同變體，根據鄰居瓦片決定造型，支援凹牆、凸牆等變體。
        並將獨立牆變回地板。
        """
        # 8個鄰居方向 (dx, dy)，採用標準 y-down 座標系（y 軸向下增加）：
        # 0: TL(-1, -1), 1: T(0, -1), 2: TR(1, -1)
        # 7: L(-1, 0),                       3: R(1, 0)
        # 6: BL(-1, 1), 5: B(0, 1), 4: BR(1, 1)
        directions = [
            (-1, -1), (0, -1), (1, -1),  # 0: TL, 1: T, 2: TR
                               (1, 0),   #              3: R
            (1, 1),   (0, 1),  (-1, 1),  # 4: BR, 5: B, 6: BL
            (-1, 0)                      # 7: L
        ]

        # 建立新瓦片陣列，避免迭代時修改時影響鄰居判斷
        new_grid = [row[:] for row in self.grid]

        for y in range(self.height):
            for x in range(self.width):
                # 只對通用的 'Border_wall' 瓦片進行調整
                if self.grid[y][x] == 'Border_wall': 
                    
                    neighbors_mask = 0
                    
                    # 1. 檢查8個鄰居，生成位元遮罩
                    for i, (dx, dy) in enumerate(directions):
                        nx, ny = x + dx, y + dy
                        
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            # 檢查鄰居是否是可通行瓦片
                            if self.grid[ny][nx] in passable_tiles:
                                neighbors_mask |= (1 << i)

                    # 2. 獨立牆判定 (Isolated Wall)
                    # 主軸鄰居位元：T(1), R(3), B(5), L(7)
                    main_axis_mask = neighbors_mask & 0b10101010
                    main_axis_count = bin(main_axis_mask).count('1')
                    
                    # 判斷：如果 4 個主軸方向中，有 3 個或 4 個是可通行的
                    if main_axis_count >= 3:
                        # 獨立牆變回 Bridge_floor（安全的地板類型）
                        new_grid[y][x] = 'Bridge_floor'
                        continue 

                    variant = 'Border_wall' # 預設為一般牆壁

                    # 3. 牆壁變體判斷（優先級：凹牆 > 凸牆 > 基本牆）
                    
                    # A. 凹牆 (Concave Wall) - 僅單一角落可通行
                    # 僅 TL(0) 可通行 -> 凹 BR (0b00000001)
                    if neighbors_mask == 0b00000001:
                        variant = 'Border_wall_concave_bottom_right'
                    # 僅 TR(2) 可通行 -> 凹 BL (0b00000100)
                    elif neighbors_mask == 0b00000100:
                        variant = 'Border_wall_concave_bottom_left'
                    # 僅 BR(4) 可通行 -> 凹 TL (0b00010000)
                    elif neighbors_mask == 0b00010000:
                        variant = 'Border_wall_concave_top_left'
                    # 僅 BL(6) 可通行 -> 凹 TR (0b01000000)
                    elif neighbors_mask == 0b01000000:
                        variant = 'Border_wall_concave_top_right'
                        
                    # B. 凸牆 (Convex Wall) - 三個相鄰格子可通行
                    # TL(0), T(1), L(7) 可通行 -> 凸 BR (0b10000011)
                    elif (neighbors_mask & 0b10000011) == 0b10000011:
                        variant = 'Border_wall_convex_bottom_right'
                    # T(1), TR(2), R(3) 可通行 -> 凸 BL (0b00001110)
                    elif (neighbors_mask & 0b00001110) == 0b00001110:
                        variant = 'Border_wall_convex_bottom_left'
                    # R(3), BR(4), B(5) 可通行 -> 凸 TL (0b00111000)
                    elif (neighbors_mask & 0b00111000) == 0b00111000:
                        variant = 'Border_wall_convex_top_left'
                    # B(5), BL(6), L(7) 可通行 -> 凸 TR (0b11100000)
                    elif (neighbors_mask & 0b11100000) == 0b11100000:
                        variant = 'Border_wall_convex_top_right'
                        
                    # C. 基本牆壁（單邊連接）
                    # 排除掉複雜變體後，剩下的牆壁類型大多屬於直線單邊連接。
                    # 上牆：B(5) 可通行
                    elif (neighbors_mask & 0b00100000):
                        variant = 'Border_wall_top'
                    # 下牆：T(1) 可通行
                    elif (neighbors_mask & 0b00000010):
                        variant = 'Border_wall_bottom'
                    # 左牆：R(3) 可通行
                    elif (neighbors_mask & 0b00001000):
                        variant = 'Border_wall_left'
                    # 右牆：L(7) 可通行
                    elif (neighbors_mask & 0b10000000):
                        variant = 'Border_wall_right'

                    new_grid[y][x] = variant

        # 將新瓦片陣列應用回地牢
        self.grid = new_grid
