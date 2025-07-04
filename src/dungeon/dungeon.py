from dataclasses import dataclass
from typing import List, Tuple, Optional
from src.config import *
import random

# 導入必要的 Python 模組：
# - dataclass: 用來簡化類的定義，自動生成初始化方法等
# - typing: 提供型別註解，幫助指定變數的資料型別
# - src.config: 導入遊戲配置（例如瓦片大小 TILE_SIZE）
# - random: 用於隨機數生成，例如房間位置或走廊寬度

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


# 定義 BSP 樹節點，用於二元空間分割
@dataclass
class BSPNode:
    # BSP（二元空間分割）節點，用於將地牢空間分割成小區域，最終生成房間
    x: float  # 節點左上角的 x 座標（瓦片單位）
    y: float  # 節點左上角的 y 座標（瓦片單位）
    width: float  # 節點的寬度（瓦片單位）
    height: float  # 節點的高度（瓦片單位）
    room: Optional[Room] = None  # 節點包含的房間物件（若為葉節點，則有房間；否則為 None）
    left: Optional['BSPNode'] = None  # 左子節點（分割後的左半部分）
    right: Optional['BSPNode'] = None  # 右子節點（分割後的右半部分）


# 地牢生成類，負責生成 BSP 地牢並管理房間與走廊
class Dungeon:
    # 地牢類，負責整個地牢的生成，包括房間、走廊（橋接）和瓦片網格
    # 地牢參數（這些是類變數，適用於所有 Dungeon 物件）
    ROOM_WIDTH = 150  # 單個房間的最大寬度（瓦片數，控制房間的最大尺寸）
    ROOM_HEIGHT = 150 # 單個房間的最大高度（瓦片數，控制房間的最大尺寸）
    GRID_WIDTH = 150  # 地牢網格的寬度（瓦片數，定義地牢的總寬度）
    GRID_HEIGHT = 150  # 地牢網格的高度（瓦片數，定義地牢的總高度）
    MIN_ROOM_SIZE = 15  # 房間的最小尺寸（寬度和高度，確保房間不會太小）
    TILE_SIZE = TILE_SIZE  # 每個瓦片的像素大小，從 src.config 導入（例如 32 像素）
    ROOM_GAP = 2  # 房間之間的最小間距（瓦片數，防止房間互相重疊）
    BIAS_RATIO = 0.6  # 房間大小偏向比例（控制房間大小的隨機性）
    BIAS_STRENGTH = 0.3  # 偏向強度（控制房間位置的隨機偏移）
    MIN_BRIDGE_WIDTH = 2  # 走廊（橋接）的最小寬度（瓦片數，確保走廊不會太窄）
    MAX_BRIDGE_WIDTH = 4  # 走廊（橋接）的最大寬度（瓦片數，控制走廊的最大寬度）
    MAX_SPLIT_DEPTH = 15  # BSP 分割的最大深度（控制生成房間的數量，深度越大房間越多）
    EXTRA_BRIDGE_RATIO = 0.2  # 額外走廊的比例（增加連通性，生成更多非必要走廊）
    game = None  # 指向 Game 物件的引用，用於與遊戲邏輯交互（目前未使用）

    def __init__(self):
        # 初始化地牢物件，設置初始屬性
        self.rooms: List[Room] = []  # 儲存所有房間物件的列表
        self.bridges: List[Tuple[float, float, float, float]] = []  # 儲存所有走廊（橋接）的列表，每個橋接包含起點和終點座標
        self.current_room_id = 0  # 當前玩家所在房間的 ID（預設為第一個房間）
        self.dungeon_tiles: List[List[str]] = []  # 地牢的 2D 瓦片陣列，儲存整個地圖的瓦片類型
        self.grid_width = 0  # 地牢網格的寬度（瓦片數）
        self.grid_height = 0  # 地牢網格的高度（瓦片數）
        self.next_room_id = 0  # 下一個房間的 ID（用於分配新房間的唯一標識）
        self.total_appeared_rooms = 0  # 生成的房間總數
        self.bsp_tree: Optional[BSPNode] = None  # BSP 樹的根節點（用於空間分割）

    def _initialize_grid(self) -> None:
        '''
        初始化地牢網格，創建一個空的瓦片陣列
        '''
        self.grid_width = self.GRID_WIDTH  # 設置網格寬度為預定義值（300 瓦片）
        self.grid_height = self.GRID_HEIGHT  # 設置網格高度為預定義值（300 瓦片）
        # 創建 2D 陣列，初始填充為 'Outside'（表示地牢外的區域）
        self.dungeon_tiles = [['Outside' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        print(f"初始化地牢網格：寬度={self.grid_width}, 高度={self.grid_height}")

    def generate_room(self, x: float, y: float, width: float, height: float, room_id: int, is_end_room: bool = False) -> Room:
        '''
        生成單個房間物件，包含房間的瓦片數據
        參數：
        - x, y: 房間左上角的座標（瓦片單位）
        - width, height: 房間的寬度和高度（瓦片單位）
        - room_id: 房間的唯一 ID
        - is_end_room: 是否為終點房間（預設為 False）
        '''
        # 創建房間的瓦片陣列，初始填充為 'Room_floor'（普通房間地板）
        tiles = [['Room_floor' for _ in range(int(width))] for _ in range(int(height))]

        # 如果是終點房間，修改內部瓦片
        if is_end_room:
            # 將房間內部（除了邊緣）設為 'End_room_floor'（終點房間地板）
            for row in range(1, int(height) - 1):
                for col in range(1, int(width) - 1):
                    tiles[row][col] = 'End_room_floor'
            # 在房間中心放置 'End_room_portal'（傳送門）
            center_x = int(width) // 2
            center_y = int(height) // 2
            tiles[center_y][center_x] = 'End_room_portal'

        # 創建並返回房間物件
        room = Room(id=room_id, x=x, y=y, width=width, height=height, tiles=tiles, is_end_room=is_end_room)
        print(f"生成房間 {room_id} 在 ({x}, {y}), 尺寸=({width}, {height}), 終點房間={is_end_room}")
        return room

    def _split_bsp(self, node: BSPNode, depth: int, max_depth: int = MAX_SPLIT_DEPTH) -> None:
        '''
        使用二元空間分割（BSP）將地牢空間分成小區域，最終在葉節點生成房間
        參數：
        - node: 當前 BSP 節點
        - depth: 當前分割深度
        - max_depth: 最大分割深度（預設為 MAX_SPLIT_DEPTH）
        '''
        # 計算最小分割尺寸（考慮房間間距）
        min_split_size = self.MIN_ROOM_SIZE + self.ROOM_GAP * 2

        # 如果達到最大深度或節點太小，停止分割，並嘗試生成房間
        if depth >= max_depth or (node.width < min_split_size * 2 and node.height < min_split_size * 2):
            # 只有當節點尺寸足夠大時才生成房間
            if node.width >= min_split_size and node.height >= min_split_size:
                # 計算房間的邊界（位置和尺寸）
                room_width, room_height, room_x, room_y = self._generate_room_bounds(
                    (node.x, node.y, node.x + node.width, node.y + node.height)
                )
                # 生成房間並分配給節點
                node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
                self.next_room_id += 1  # 增加下一個房間 ID
            return

        # 檢查是否可以進行水平或垂直分割
        can_split_horizontally = node.width >= min_split_size * 2  # 寬度足夠進行垂直分割
        can_split_vertically = node.height >= min_split_size * 2  # 高度足夠進行水平分割
        if not (can_split_horizontally or can_split_vertically):
            # 如果無法分割，但尺寸足夠，生成房間
            if node.width >= min_split_size and node.height >= min_split_size:
                room_width, room_height, room_x, room_y = self._generate_room_bounds(
                    (node.x, node.y, node.x + node.width, node.y + node.height)
                )
                node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
                self.next_room_id += 1
            return

        # 計算分割方向的權重（根據節點的寬高比例）
        w, h = node.width, node.height
        total = w * w + h * h
        vertical_weight = w * w / total  # 垂直分割的權重（寬度越大，越傾向垂直分割）
        horizontal_weight = h * h / total  # 水平分割的權重（高度越大，越傾向水平分割）
        possible_directions = []  # 可選的分割方向
        weights = []  # 對應的權重

        if can_split_horizontally:
            possible_directions.append("vertical")
            weights.append(vertical_weight)
        if can_split_vertically:
            possible_directions.append("horizontal")
            weights.append(horizontal_weight)

        # 如果沒有可分割的方向，嘗試生成房間
        if not possible_directions:
            if node.width >= min_split_size and node.height >= min_split_size:
                room_width, room_height, room_x, room_y = self._generate_room_bounds(
                    (node.x, node.y, node.x + node.width, node.y + node.height)
                )
                node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
                self.next_room_id += 1
            return

        # 根據權重隨機選擇分割方向
        direction = random.choices(possible_directions, weights=weights)[0]

        # 根據選擇的方向進行分割
        if direction == "vertical":
            # 垂直分割：將節點分成左右兩部分
            split_x = random.randint(min_split_size, int(node.width - min_split_size))
            # 創建左子節點和右子節點
            node.left = BSPNode(node.x, node.y, split_x, node.height)
            node.right = BSPNode(node.x + split_x, node.y, node.width - split_x, node.height)
        else:
            # 水平分割：將節點分成上下兩部分
            split_y = random.randint(min_split_size, int(node.height - min_split_size))
            node.left = BSPNode(node.x, node.y, node.width, split_y)
            node.right = BSPNode(node.x, node.y + split_y, node.width, node.height - split_y)

        # 遞迴分割子節點
        if node.left:
            self._split_bsp(node.left, depth + 1, max_depth)
        if node.right:
            self._split_bsp(node.right, depth + 1, max_depth)

    def _generate_room_bounds(self, partition: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        '''
        根據 BSP 分區計算房間的邊界（位置和尺寸）
        參數：
        - partition: 分區的座標 (x0, y0, x1, y1)，表示左上角和右下角
        '''
        x0, y0, x1, y1 = partition  # 分區的左上角和右下角座標

        # 房間位置從分區左上角開始，加上間距（ROOM_GAP）以避免房間緊貼
        room_x = x0 + self.ROOM_GAP
        room_y = y0 + self.ROOM_GAP

        # 計算房間的最大可能尺寸，考慮間距並限制在最大房間尺寸內
        max_width = x1 - x0 - 2 * self.ROOM_GAP
        max_height = y1 - y0 - 2 * self.ROOM_GAP
        room_width = min(max_width, self.ROOM_WIDTH)  # 限制寬度不超過 ROOM_WIDTH
        room_height = min(max_height, self.ROOM_HEIGHT)  # 限制高度不超過 ROOM_HEIGHT

        # 確保房間尺寸不小於最小尺寸
        room_width = max(room_width, self.MIN_ROOM_SIZE)
        room_height = max(room_height, self.MIN_ROOM_SIZE)

        print(f"生成房間邊界：位置=({room_x}, {room_y}), 尺寸=({room_width}, {room_height})")
        return room_width, room_height, room_x, room_y

    def _collect_rooms(self, node: BSPNode, rooms: List[Room]) -> None:
        '''
        遍歷 BSP 樹，收集所有包含房間的葉節點
        參數：
        - node: 當前 BSP 節點
        - rooms: 用於儲存房間的列表
        '''
        if node.room:
            rooms.append(node.room)  # 如果節點有房間，添加到列表
        if node.left:
            self._collect_rooms(node.left, rooms)  # 遞迴處理左子節點
        if node.right:
            self._collect_rooms(node.right, rooms)  # 遞迴處理右子節點

    def _check_bridge_room_collision(self, bridge: Tuple[float, float, float, float], room1: Room, room2: Room) -> bool:
        '''
        檢查走廊（橋接）是否與其他房間相交（除了要連接的兩個房間）
        參數：
        - bridge: 走廊的矩形範圍 (x0, y0, x1, y1)
        - room1, room2: 要連接的兩個房間（這些房間的碰撞會被忽略）
        '''
        x0 = min(bridge[0], bridge[2])  # 走廊矩形的左上角 x
        y0 = min(bridge[1], bridge[3])  # 走廊矩形的左上角 y
        x1 = max(bridge[0], bridge[2])  # 走廊矩形的右下角 x
        y1 = max(bridge[1], bridge[3])  # 走廊矩形的右下角 y

        for room in self.rooms:
            # 跳過要連接的兩個房間
            if room.id == room1.id or room.id == room2.id:
                continue
            room_x0 = room.x  # 房間左上角 x
            room_y0 = room.y  # 房間左上角 y
            room_x1 = room.x + room.width  # 房間右下角 x
            room_y1 = room.y + room.height  # 房間右下角 y

            # 檢查走廊矩形是否與房間矩形相交
            # 如果走廊的任何部分進入房間範圍，則認為相交
            if not (x1 < room_x0 or x0 > room_x1 or y1 < room_y0 or y0 > room_y1):
                return True  # 相交
        return False  # 不相交

    def _generate_bridge(self, room1: Room, room2: Room) -> List[Tuple[float, float, float, float]]:
        '''
        生成兩個房間之間的走廊（橋接），優先嘗試直線連接，若不行則用 L 形路徑
        參數：
        - room1, room2: 要連接的兩個房間物件
        '''
        def rand_room_point(room: Room) -> Tuple[int, int]:
            # 在房間內隨機選擇一個連接點，避開邊緣（牆壁）
            x = random.randint(int(room.x + 2), int(room.x + room.width - 3))
            y = random.randint(int(room.y + 2), int(room.y + room.height - 3))
            return x, y

        def add_horizontal(x1: int, y: int, x2: int, width: int) -> Tuple[float, float, float, float]:
            # 生成水平走廊段
            # 返回 (x0, y0, x1, y1)，表示走廊的矩形範圍
            return (min(x1, x2), y - width / 2, max(x1, x2), y + width / 2)

        def add_vertical(x: int, y1: int, y2: int, width: int) -> Tuple[float, float, float, float]:
            # 生成垂直走廊段
            # 返回 (x0, y0, x1, y1)，表示走廊的矩形範圍
            return (x - width / 2, min(y1, y2), x + width / 2, max(y1, y2))

        bridges = []  # 儲存生成的走廊段
        # 隨機選擇兩個房間的連接點
        start_x, start_y = rand_room_point(room1)
        end_x, end_y = rand_room_point(room2)

        # 確保 start_x 是左邊的點（簡化後續邏輯）
        if start_x > end_x:
            start_x, end_x = end_x, start_x
            start_y, end_y = end_y, start_y
            room1, room2 = room2, room1  # 交換房間順序以保持一致性

        # 使用高斯分佈隨機選擇走廊寬度，範圍在 MIN_BRIDGE_WIDTH 和 MAX_BRIDGE_WIDTH 之間
        bridge_width = int(random.gauss((self.MIN_BRIDGE_WIDTH + self.MAX_BRIDGE_WIDTH) // 2, (self.MAX_BRIDGE_WIDTH - self.MIN_BRIDGE_WIDTH) / 2))
        bridge_width = max(self.MIN_BRIDGE_WIDTH, min(bridge_width, self.MAX_BRIDGE_WIDTH))

        # 檢查是否可以直線連接
        if abs(start_x - end_x) <= 1:  # 兩個點的 x 座標幾乎相同（垂直對齊）
            bridge = add_vertical(start_x, start_y, end_y, bridge_width)
            if not self._check_bridge_room_collision(bridge, room1, room2):
                # 如果沒有碰撞，添加直線垂直走廊
                bridges.append(bridge)
                print("直線垂直橋接")
            else:
                # 如果直線走廊有碰撞，改用 L 形路徑（水平→垂直）
                bridge1 = add_horizontal(start_x, start_y, end_x, bridge_width)
                bridge2 = add_vertical(end_x, start_y, end_y, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (水平→垂直)")
                else:
                    # 如果 L 形路徑也有碰撞，仍然使用該路徑（確保連通性）
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (水平→垂直，忽略碰撞)")
        elif abs(start_y - end_y) <= 1:  # 兩個點的 y 座標幾乎相同（水平對齊）
            bridge = add_horizontal(start_x, start_y, end_x, bridge_width)
            if not self._check_bridge_room_collision(bridge, room1, room2):
                # 如果沒有碰撞，添加直線水平走廊
                bridges.append(bridge)
                print("直線水平橋接")
            else:
                # 如果直線走廊有碰撞，改用 L 形路徑（垂直→水平）
                bridge1 = add_vertical(start_x, start_y, end_y, bridge_width)
                bridge2 = add_horizontal(start_x, end_y, end_x, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (垂直→水平)")
                else:
                    # 如果 L 形路徑也有碰撞，仍然使用該路徑
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (垂直→水平，忽略碰撞)")
        else:
            # 如果無法直線連接，隨機選擇 L 形路徑
            if random.choice([True, False]):
                # 先水平後垂直
                bridge1 = add_horizontal(start_x, start_y, end_x, bridge_width)
                bridge2 = add_vertical(end_x, start_y, end_y, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("L形橋接 (水平→垂直)")
                else:
                    # 如果碰撞，嘗試另一方向（垂直→水平）
                    bridge1 = add_vertical(start_x, start_y, end_y, bridge_width)
                    bridge2 = add_horizontal(start_x, end_y, end_x, bridge_width)
                    if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                        bridges.extend([bridge1, bridge2])
                        print("L形橋接 (垂直→水平)")
                    else:
                        # 如果另一方向也碰撞，使用後備路徑
                        bridges.extend([bridge1, bridge2])
                        print("後備L形橋接 (垂直→水平，忽略碰撞)")
            else:
                # 先垂直後水平
                bridge1 = add_vertical(start_x, start_y, end_y, bridge_width)
                bridge2 = add_horizontal(start_x, end_y, end_x, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("L形橋接 (垂直→水平)")
                else:
                    # 如果碰撞，嘗試另一方向（水平→垂直）
                    bridge1 = add_horizontal(start_x, start_y, end_x, bridge_width)
                    bridge2 = add_vertical(end_x, start_y, end_y, bridge_width)
                    if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                        bridges.extend([bridge1, bridge2])
                        print("L形橋接 (水平→垂直)")
                    else:
                        # 如果另一方向也碰撞，使用後備路徑
                        bridges.extend([bridge1, bridge2])
                        print("後備L形橋接 (水平→垂直，忽略碰撞)")

        # 輸出走廊的詳細資訊以便除錯
        print(f"橋接從房間 {room1.id} 到 {room2.id}")
        print(f"起點: ({start_x}, {start_y}) → 終點: ({end_x}, {end_y}) | 寬度: {bridge_width}")
        print(f"橋接段: {bridges}")
        return bridges

    def _generate_bridges(self, rooms: List[Room]) -> List[Tuple[float, float, float, float]]:
        '''
        生成所有房間之間的走廊，確保地牢連通並添加額外走廊以增加路徑多樣性
        參數：
        - rooms: 所有房間的列表
        '''
        bridges = []  # 儲存所有走廊
        connected_pairs = set()  # 記錄已連通的房間對（避免重複連接）
        rooms_left = rooms[:]  # 複製房間列表以便修改
        current_room = rooms_left[0]  # 從第一個房間開始

        # 第一階段：生成最小生成樹，確保所有房間連通
        while rooms_left:
            rooms_left.remove(current_room)  # 移除當前房間
            closest_room = self._find_closest_room(current_room, rooms_left)  # 找到最近的房間
            if closest_room:
                # 檢查是否已連通
                pair = tuple(sorted([current_room.id, closest_room.id]))
                if pair not in connected_pairs:
                    bridges.extend(self._generate_bridge(current_room, closest_room))  # 生成走廊
                    connected_pairs.add(pair)  # 記錄連通的房間對
                current_room = closest_room  # 移動到下一個房間
            else:
                break

        # 第二階段：添加額外走廊，數量為房間數 * EXTRA_BRIDGE_RATIO
        extra_bridges = int(len(rooms) * self.EXTRA_BRIDGE_RATIO)  # 計算額外走廊數量
        room_ids = [room.id for room in rooms]  # 獲取所有房間 ID
        # 找出終點房間的 ID（終點房間只允許一個走廊）
        end_room_id = next((room.id for room in rooms if room.is_end_room), None)
        # 計算所有可能的房間對及其距離
        possible_pairs = [
            (id1, id2, ((rooms[id1].x + rooms[id1].width / 2 - rooms[id2].x - rooms[id2].width / 2) ** 2 +
                        (rooms[id1].y + rooms[id1].height / 2 - rooms[id2].y - rooms[id2].height / 2) ** 2) ** 0.5)
            for i, id1 in enumerate(room_ids)
            for id2 in room_ids[i + 1:]
            if end_room_id is None or (id1 != end_room_id and id2 != end_room_id)  # 排除終點房間
        ]
        # 按距離從大到小排序，優先選擇較遠的房間對以增加空間分佈均勻性
        possible_pairs.sort(key=lambda x: x[2], reverse=True)
        available_pairs = [(id1, id2) for id1, id2, _ in possible_pairs if tuple(sorted([id1, id2])) not in connected_pairs]
        actual_bridges = min(extra_bridges, len(available_pairs))  # 確定實際添加的額外走廊數

        # 限制每個房間的最大走廊數
        max_bridges_per_room = 3
        room_bridge_count = {room.id: 0 for room in rooms}  # 記錄每個房間的走廊數

        # 選擇房間對進行額外走廊生成
        selected_pairs = []
        for id1, id2 in available_pairs:
            if room_bridge_count[id1] < max_bridges_per_room and room_bridge_count[id2] < max_bridges_per_room:
                selected_pairs.append((id1, id2))
                room_bridge_count[id1] += 1
                room_bridge_count[id2] += 1
            if len(selected_pairs) >= actual_bridges:
                break

        # 生成額外走廊
        for id1, id2 in selected_pairs:
            room1 = next(r for r in rooms if r.id == id1)
            room2 = next(r for r in rooms if r.id == id2)
            bridges.extend(self._generate_bridge(room1, room2))
            connected_pairs.add(tuple(sorted([id1, id2])))

        print(f"總共生成 {len(bridges)} 個橋接，連通 {len(connected_pairs)} 對房間")
        return bridges

    def _find_closest_room(self, room: Room, rooms: List[Room]) -> Optional[Room]:
        '''
        找到距離指定房間最近的其他房間
        參數：
        - room: 當前房間
        - rooms: 其他房間的列表
        '''
        closest_room = None
        closest_distance = float('inf')  # 初始化為無窮大
        room_center = (room.x + room.width / 2, room.y + room.height / 2)  # 計算當前房間的中心點
        for compare_room in rooms:
            compare_center = (compare_room.x + compare_room.width / 2, compare_room.y + compare_room.height / 2)
            # 計算兩個房間中心點的歐幾里得距離
            dist = ((compare_center[0] - room_center[0]) ** 2 + (compare_center[1] - room_center[1]) ** 2) ** 0.5
            if dist < closest_distance:
                closest_distance = dist
                closest_room = compare_room
        return closest_room

    def _place_bridge(self, bridge: Tuple[float, float, float, float]) -> None:
        '''
        將走廊（橋接）放置到地牢網格中，設為 'Bridge_floor'（走廊地板）
        參數：
        - bridge: 走廊的矩形範圍 (x0, y0, x1, y1)
        '''
        x0 = int(min(bridge[0], bridge[2]))  # 走廊左上角 x
        y0 = int(min(bridge[1], bridge[3]))  # 走廊左上角 y
        x1 = int(max(bridge[0], bridge[2]))  # 走廊右下角 x
        y1 = int(max(bridge[1], bridge[3]))  # 走廊右下角 y
        # 確保走廊至少有 1 瓦片寬度
        if x1 - x0 == 0:
            x1 = x0 + 1
        if y1 - y0 == 0:
            y1 = y0 + 1
        # 填充走廊區域為 'Bridge_floor'，擴展 1 瓦片以確保連通
        for y in range(max(0, y0 - 1), min(y1 + 1, self.grid_height)):
            for x in range(max(0, x0 - 1), min(x1 + 1, self.grid_width)):
                # 僅覆蓋 'Outside' 瓦片，避免覆蓋房間或其他走廊
                if self.dungeon_tiles[y][x] and self.dungeon_tiles[y][x] != 'Outside':
                    continue
                self.dungeon_tiles[y][x] = 'Bridge_floor'
        print(f"放置橋接：從 ({x0}, {y0}) 到 ({x1}, {y1})")

    def _add_walls(self) -> None:
        '''
        為地牢中的地板瓦片（房間或走廊）添加邊界牆壁
        '''
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] in ['Room_floor', 'Bridge_floor']:
                    # 如果當前瓦片是地板，檢查其周圍是否有 'Outside' 或超出邊界
                    breaker = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            # 檢查是否超出網格邊界
                            if y + dy < 0 or y + dy >= self.grid_height or x + dx < 0 or x + dx >= self.grid_width:
                                self.dungeon_tiles[y][x] = 'Border_wall'  # 設為邊界牆壁
                                breaker = True
                            # 檢查周圍是否有 'Outside' 瓦片
                            elif self.dungeon_tiles[y + dy][x + dx] == 'Outside':
                                self.dungeon_tiles[y][x] = 'Border_wall'  # 設為邊界牆壁
                                breaker = True
                            if breaker:
                                break
                        if breaker:
                            break

        print("添加牆壁完成")

    def initialize_dungeon(self) -> None:
        '''
        初始化整個地牢，生成房間、走廊和牆壁
        '''
        self._initialize_grid()  # 初始化網格
        self.bsp_tree = BSPNode(0, 0, self.grid_width, self.grid_height)  # 創建 BSP 樹根節點
        self._split_bsp(self.bsp_tree, 0)  # 執行 BSP 分割
        self.rooms = []  # 清空房間列表
        self.bridges = []  # 清空走廊列表
        self.next_room_id = 0  # 設置下一個房間 ID 從 0 開始
        self._collect_rooms(self.bsp_tree, self.rooms)  # 收集所有房間
        self.total_appeared_rooms = len(self.rooms)  # 記錄房間總數
        if not self.rooms:
            raise ValueError("未生成任何房間")  # 如果沒有房間，拋出錯誤

        self.rooms[0].id = 0  # 設置第一個房間的 ID 為 0（起始房間）
        self.current_room_id = 0  # 設置當前房間為起始房間

        # 選擇距離起始房間最遠的房間作為終點房間
        if len(self.rooms) > 1:
            max_dist = 0
            end_room = None
            start_center = (self.rooms[0].x + self.rooms[0].width / 2, self.rooms[0].y + self.rooms[0].height / 2)
            for room in self.rooms[1:]:
                room_center = (room.x + room.width / 2, room.y + room.height / 2)
                # 使用曼哈頓距離計算房間間距
                dist = abs(room_center[0] - start_center[0]) + abs(room_center[1] - start_center[1])
                if dist > max_dist:
                    max_dist = dist
                    end_room = room
            if end_room:
                end_room.is_end_room = True  # 設置為終點房間
                # 更新終點房間的瓦片
                for row in range(1, int(end_room.height) - 1):
                    for col in range(1, int(end_room.width) - 1):
                        end_room.tiles[row][col] = 'End_room_floor'
                center_x = int(end_room.width) // 2
                center_y = int(end_room.height) // 2
                end_room.tiles[center_y][center_x] = 'End_room_portal'
                print(f"指定房間 {end_room.id} 為終點房間，距離起點 {max_dist}")

        # 將所有房間放置到網格中
        for room in self.rooms:
            self._place_room(room)

        # 生成並放置所有走廊
        self.bridges = self._generate_bridges(self.rooms)
        for bridge in self.bridges:
            self._place_bridge(bridge)

        # 為地板添加牆壁
        self._add_walls()

        print(f"初始化地牢：{len(self.rooms)} 個房間，{len(self.bridges)} 個橋接")

    def _place_room(self, room: Room) -> None:
        '''
        將房間的瓦片放置到地牢網格中
        參數：
        - room: 要放置的房間物件
        '''
        grid_x = int(room.x)  # 房間左上角 x（轉為整數）
        grid_y = int(room.y)  # 房間左上角 y（轉為整數）
        # 檢查房間是否超出網格範圍，若是則擴展網格
        if (grid_x < 0 or grid_x + int(room.width) > self.grid_width or \
            grid_y < 0 or grid_y + int(room.height) > self.grid_height):
            self.expand_grid(grid_x + int(room.width), grid_y + int(room.height))
        # 將房間的瓦片複製到網格中
        for row in range(int(room.height)):
            for col in range(int(room.width)):
                self.dungeon_tiles[grid_y + row][grid_x + col] = room.tiles[row][col]
        print(f"放置房間 {room.id} 在網格 ({grid_x}, {grid_y})")

    def get_room(self, room_id: int) -> Room:
        '''
        根據房間 ID 獲取房間物件
        參數：
        - room_id: 要查找的房間 ID
        '''
        try:
            return next(r for r in self.rooms if r.id == room_id)  # 返回第一個匹配的房間
        except StopIteration:
            raise ValueError(f"未找到房間 {room_id}")  # 如果找不到，拋出錯誤

    def expand_grid(self, new_width: int, new_height: int) -> None:
        '''
        擴展地牢網格以適應更大的尺寸
        參數：
        - new_width: 新的網格寬度
        - new_height: 新的網格高度
        '''
        if new_width > self.grid_width:
            # 為每行添加額外的 'W'（牆壁）瓦片
            for row in self.dungeon_tiles:
                row.extend(['W' for _ in range(new_width - self.grid_width)])
            self.grid_width = new_width
        if new_height > self.grid_height:
            # 添加新的行，填充為 'W'（牆壁）
            self.dungeon_tiles.extend([['W' for _ in range(self.grid_width)] for _ in range(new_height - self.grid_height)])
            self.grid_height = new_height
        print(f"擴展網格到 ({self.grid_width}, {self.grid_height})")

    def get_tile_at(self, pos: Tuple[float, float]) -> str:
        '''
        根據像素座標獲取對應的瓦片類型
        參數：
        - pos: 像素座標 (x, y)
        '''
        tile_x = int(pos[0] // self.TILE_SIZE)  # 將像素座標轉換為瓦片座標
        tile_y = int(pos[1] // self.TILE_SIZE)
        # 檢查瓦片是否在網格範圍內
        if 0 <= tile_y < self.grid_height and 0 <= tile_x < self.grid_width:
            return self.dungeon_tiles[tile_y][tile_x]
        return 'W'  # 如果超出範圍，返回牆壁瓦片