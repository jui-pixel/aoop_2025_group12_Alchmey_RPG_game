from dataclasses import dataclass
from typing import List, Tuple, Optional
import random


# 定義房間數據結構，用於儲存房間的屬性和瓦片數據
@dataclass
class Room:
    id: int  # 房間唯一標識
    x: float  # 房間左上角 x 座標
    y: float  # 房間左上角 y 座標
    width: float  # 房間寬度（瓦片數）
    height: float  # 房間高度（瓦片數）
    tiles: List[List[str]]  # 房間的瓦片陣列（'F'、'Room_wall'、'E'、'G'）
    connections: List[Tuple[int, str]] = None  # 房間連接到其他房間的列表（房間 ID 和方向）
    is_end_room: bool = False  # 是否為終點房間

    # 初始化後處理，確保 connections 為空列表
    def __post_init__(self):
        if self.connections is None:
            self.connections = []


# 定義 BSP 樹節點，用於二元空間分割
@dataclass
class BSPNode:
    x: float  # 節點左上角 x 座標
    y: float  # 節點左上角 y 座標
    width: float  # 節點寬度（瓦片數）
    height: float  # 節點高度（瓦片數）
    room: Optional[Room] = None  # 節點包含的房間（若為葉節點）
    left: Optional['BSPNode'] = None  # 左子節點
    right: Optional['BSPNode'] = None  # 右子節點


# 地牢生成類，負責生成 BSP 地牢並管理房間與走廊
class Dungeon:
    # 地牢參數
    ROOM_WIDTH = 40  # 單個房間的最大寬度（瓦片數）
    ROOM_HEIGHT = 40  # 單個房間的最大高度（瓦片數）
    MIN_ROOM_SIZE = 30  # 房間的最小尺寸（寬度和高度）
    TILE_SIZE = 32  # 每個瓦片的像素大小（假設值，應從 config 導入）
    ROOM_GAP = 4  # 房間之間的最小間距（瓦片數）
    BIAS_RATIO = 0.6  # 房間大小偏向比例
    BIAS_STRENGTH = 0.3  # 偏向強度
    MIN_BRIDGE_WIDTH = 4  # 橋接（走廊）的最小寬度（瓦片數）
    MAX_BRIDGE_WIDTH = 5  # 橋接（走廊）的最大寬度（瓦片數）
    MAX_SPLIT_DEPTH = 20  # BSP 分割的最大深度
    EXTRA_BRIDGE_RATIO = 0.2  # 額外橋接的比例（相對於房間數）
    game = None  # 指向 Game 對象的引用，用於與遊戲邏輯交互

    def __init__(self):
        # 初始化地牢屬性
        self.rooms: List[Room] = []  # 儲存所有房間
        self.current_room_id = 0  # 當前玩家所在房間的 ID
        self.dungeon_tiles: List[List[str]] = []  # 地牢的 2D 瓦片陣列
        self.grid_width = 0  # 地牢網格寬度（瓦片數）
        self.grid_height = 0  # 地牢網格高度（瓦片數）
        self.next_room_id = 0  # 下一個房間的 ID
        self.total_appeared_rooms = 0  # 生成的房間總數
        self.bsp_tree: Optional[BSPNode] = None  # BSP 樹根節點

    def _initialize_grid(self) -> None:
        # 初始化地牢網格，填充為 'Outside'
        self.grid_width = self.ROOM_WIDTH * 10  # 網格尺寸（400x400）
        self.grid_height = self.ROOM_HEIGHT * 10
        self.dungeon_tiles = [['Outside' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        print(f"初始化地牢網格：寬度={self.grid_width}, 高度={self.grid_height}")

    def generate_room(self, x: float, y: float, width: float, height: float, room_id: int, is_end_room: bool = False) -> Room:
        # 生成房間對象，創建房間瓦片空間
        tiles = [['Room_floor' for _ in range(int(width))] for _ in range(int(height))]

        # 如果是終點房間，將內部瓦片設為 'E'，中心設為 'G'（終點標記）
        if is_end_room:
            for row in range(1, int(height) - 1):
                for col in range(1, int(width) - 1):
                    tiles[row][col] = 'End_room_floor'
            center_x = int(width) // 2
            center_y = int(height) // 2
            tiles[center_y][center_x] = 'End_room_portal'  # 設置終點傳送門

        # 創建房間對象
        room = Room(id=room_id, x=x, y=y, width=width, height=height, tiles=tiles, is_end_room=is_end_room)
        print(f"生成房間 {room_id} 在 ({x}, {y}), 尺寸=({width}, {height}), 終點房間={is_end_room}")
        return room

    def _split_bsp(self, node: BSPNode, depth: int, max_depth: int = MAX_SPLIT_DEPTH) -> None:
        # 執行 BSP 分割，將節點分為子區域或生成房間
        min_split_size = self.MIN_ROOM_SIZE + self.ROOM_GAP * 2  # 最小分割尺寸（考慮間距）
        # 如果達到最大深度或節點太小，停止分割
        if depth >= max_depth or node.width < min_split_size * 2 or node.height < min_split_size * 2:
            if node.width >= min_split_size and node.height >= min_split_size:
                room_width, room_height, room_x, room_y = self._generate_room_bounds(
                    (node.x, node.y, node.x + node.width, node.y + node.height)
                )
                node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
                self.next_room_id += 1
            return

        # 檢查是否可以水平或垂直分割
        can_split_horizontally = node.width >= min_split_size * 2
        can_split_vertically = node.height >= min_split_size * 2
        if not (can_split_horizontally or can_split_vertically):
            if node.width >= min_split_size and node.height >= min_split_size:
                room_width, room_height, room_x, room_y = self._generate_room_bounds(
                    (node.x, node.y, node.x + node.width, node.y + node.height)
                )
                node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
                self.next_room_id += 1
            return

        # 隨機選擇水平或垂直分割
        if random.random() < 0.5 and can_split_horizontally:
            split_x = random.randint(min_split_size, int(node.width - min_split_size))
            node.left = BSPNode(node.x, node.y, split_x, node.height)
            node.right = BSPNode(node.x + split_x, node.y, node.width - split_x, node.height)
        else:
            split_y = random.randint(min_split_size, int(node.height - min_split_size))
            node.left = BSPNode(node.x, node.y, node.width, split_y)
            node.right = BSPNode(node.x, node.y + split_y, node.width, node.height - split_y)

        # 遞迴分割子節點
        if node.left:
            self._split_bsp(node.left, depth + 1, max_depth)
        if node.right:
            self._split_bsp(node.right, depth + 1, max_depth)

    def _generate_room_bounds(self, partition: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        # 根據分區生成房間的邊界，應用偏向邏輯並限制尺寸
        x0, y0, x1, y1 = partition  # 分區的左上角和右下角座標
        # 計算 x 軸中點
        x_avg = (x0 + x1) / 2
        x_origin_rand = random.uniform(x0, x_avg)  # 隨機選擇起始 x
        x_origin_bias_point = x0 + (x1 - x0) * (1 - self.BIAS_RATIO)  # 偏向點
        room_x = x_origin_rand + (x_origin_bias_point - x_origin_rand) * self.BIAS_STRENGTH  # 應用偏向

        # 計算 y 軸中點
        y_avg = (y0 + y1) / 2
        y_origin_rand = random.uniform(y0, y_avg)  # 隨機選擇起始 y
        y_origin_bias_point = y0 + (y1 - y0) * (1 - self.BIAS_RATIO)  # 偏向點
        room_y = y_origin_rand + (y_origin_bias_point - y_origin_rand) * self.BIAS_STRENGTH  # 應用偏向

        # 計算房間結束座標，限制最大尺寸
        x_end_rand = random.uniform(x_avg, x1)
        x_end_bias_point = x1 - (x1 - x0) * (1 - self.BIAS_RATIO)
        room_end_x = x_end_rand + (x_end_bias_point - x_end_rand) * self.BIAS_STRENGTH
        room_width = min(room_end_x - room_x, self.ROOM_WIDTH)  # 限制寬度不超過 ROOM_WIDTH

        y_end_rand = random.uniform(y_avg, y1)
        y_end_bias_point = y1 - (y1 - y0) * (1 - self.BIAS_RATIO)
        room_end_y = y_end_rand + (y_end_bias_point - y_end_rand) * self.BIAS_STRENGTH
        room_height = min(room_end_y - room_y, self.ROOM_HEIGHT)  # 限制高度不超過 ROOM_HEIGHT

        # 確保最小尺寸
        room_width = max(room_width, self.MIN_ROOM_SIZE)
        room_height = max(room_height, self.MIN_ROOM_SIZE)
        print(f"生成房間邊界：位置=({room_x}, {room_y}), 尺寸=({room_width}, {room_height})")
        return room_width, room_height, room_x, room_y

    def _collect_rooms(self, node: BSPNode, rooms: List[Room]) -> None:
        # 收集 BSP 樹中的所有房間
        if node.room:
            rooms.append(node.room)  # 添加葉節點的房間
        if node.left:
            self._collect_rooms(node.left, rooms)  # 遞迴左子節點
        if node.right:
            self._collect_rooms(node.right, rooms)  # 遞迴右子節點

    def _generate_bridge(self, room1: Room, room2: Room) -> List[Tuple[float, float, float, float]]:
        # 生成兩個房間之間的橋接（走廊），優先選擇直線或單次轉彎
        def rand_room_point(room: Room) -> Tuple[int, int]:
            # 選擇房間內的有效橋接點（避開牆壁）
            x = random.randint(int(room.x + 2), int(room.x + room.width - 3))
            y = random.randint(int(room.y + 2), int(room.y + room.height - 3))
            return x, y

        def add_horizontal(x1, y, x2, width):
            # 生成水平橋接段
            return (min(x1, x2), y - width / 2, max(x1, x2), y + width / 2)

        def add_vertical(x, y1, y2, width):
            # 生成垂直橋接段
            return (x - width / 2, min(y1, y2), x + width / 2, max(y1, y2))

        start_x, start_y = rand_room_point(room1)
        end_x, end_y = rand_room_point(room2)
        bridge_width = random.randint(self.MIN_BRIDGE_WIDTH, self.MAX_BRIDGE_WIDTH)
        bridges = []

        print(f"橋接從房間 {room1.id} 到 {room2.id}")
        print(f"起點: ({start_x}, {start_y}) → 終點: ({end_x}, {end_y}) | 寬度: {bridge_width}")

        # 檢查是否可以直線連接
        if start_x == end_x or abs(start_x - end_x) <= 1:
            bridges.append(add_vertical(start_x, start_y, end_y, bridge_width))
            print("直線垂直橋接")
        elif start_y == end_y or abs(start_y - end_y) <= 1:
            bridges.append(add_horizontal(start_x, start_y, end_x, bridge_width))
            print("直線水平橋接")
        else:
            # L 形橋接（單次轉彎）
            if random.choice([True, False]):
                bridges.append(add_horizontal(start_x, start_y, end_x, bridge_width))
                bridges.append(add_vertical(end_x, start_y, end_y, bridge_width))
                print("L形橋接 (水平→垂直)")
            else:
                bridges.append(add_vertical(start_x, start_y, end_y, bridge_width))
                bridges.append(add_horizontal(start_x, end_y, end_x, bridge_width))
                print("L形橋接 (垂直→水平)")

        print(f"橋接段: {bridges}")
        return bridges

    def _generate_bridges(self, rooms: List[Room]) -> List[Tuple[float, float, float, float]]:
        # 生成所有房間之間的橋接，確保連通性
        bridges = []
        connected_pairs = set()  # 記錄已連通的房間對
        rooms_left = rooms[:]  # 複製房間列表
        current_room = rooms_left[0]  # 從第一個房間開始

        # 第一階段：生成最小生成樹，確保所有房間連通
        while rooms_left:
            rooms_left.remove(current_room)
            closest_room = self._find_closest_room(current_room, rooms_left)
            if closest_room:
                pair = tuple(sorted([current_room.id, closest_room.id]))
                if pair not in connected_pairs:
                    bridges.extend(self._generate_bridge(current_room, closest_room))
                    connected_pairs.add(pair)
                current_room = closest_room
            else:
                break

        # 第二階段：添加額外橋接，數量為房間數 * EXTRA_BRIDGE_RATIO
        extra_bridges = int(len(rooms) * self.EXTRA_BRIDGE_RATIO)
        room_ids = [room.id for room in rooms]
        possible_pairs = [
            tuple(sorted([id1, id2]))
            for i, id1 in enumerate(room_ids)
            for id2 in room_ids[i + 1:]
        ]
        available_pairs = [pair for pair in possible_pairs if pair not in connected_pairs]
        actual_bridges = min(extra_bridges, len(available_pairs))
        selected_pairs = random.sample(available_pairs, actual_bridges)

        for id1, id2 in selected_pairs:
            room1 = next(r for r in rooms if r.id == id1)
            room2 = next(r for r in rooms if r.id == id2)
            bridges.extend(self._generate_bridge(room1, room2))
            connected_pairs.add((id1, id2))

        print(f"總共生成 {len(bridges)} 個橋接，連通 {len(connected_pairs)} 對房間")
        return bridges

    def _find_closest_room(self, room: Room, rooms: List[Room]) -> Optional[Room]:
        # 找到距離指定房間最近的其他房間
        closest_room = None
        closest_distance = float('inf')
        room_center = (room.x + room.width / 2, room.y + room.height / 2)  # 當前房間中心
        for compare_room in rooms:
            compare_center = (compare_room.x + compare_room.width / 2, compare_room.y + compare_room.height / 2)
            dist = ((compare_center[0] - room_center[0]) ** 2 + (compare_center[1] - room_center[1]) ** 2) ** 0.5
            if dist < closest_distance:
                closest_distance = dist
                closest_room = compare_room
        return closest_room

    def _place_bridge(self, bridge: Tuple[float, float, float, float]) -> None:
        # 將橋接矩形放置到地牢網格中，設為 'F'（地板）
        x0 = int(min(bridge[0], bridge[2]))  # 橋接左上角 x
        y0 = int(min(bridge[1], bridge[3]))  # 橋接左上角 y
        x1 = int(max(bridge[0], bridge[2]))  # 橋接右下角 x
        y1 = int(max(bridge[1], bridge[3]))  # 橋接右下角 y
        # 處理寬度為 0 的橋接，確保至少 1 瓦片寬
        if x1 - x0 == 0:
            x1 = x0 + 1
        if y1 - y0 == 0:
            y1 = y0 + 1
        # 填充橋接區域為 'F'，包括房間牆壁
        for y in range(max(0, y0 - 1), min(y1 + 1, self.grid_height)):
            for x in range(max(0, x0 - 1), min(x1 + 1, self.grid_width)):
                if self.dungeon_tiles[y][x] and self.dungeon_tiles[y][x] != 'Outside':
                    # 如果已經有瓦片，則不覆蓋
                    continue
                self.dungeon_tiles[y][x] = 'Bridge_floor'
        print(f"放置橋接：從 ({x0}, {y0}) 到 ({x1}, {y1})")

    def _add_walls(self) -> None:
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] in ['Room_floor', 'Bridge_floor', 'End_room_floor']:
                    # 為每個地板瓦片添加牆壁
                    breaker = False  # 用於檢查是否已經添加過牆壁
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if y + dy < 0 or y + dy >= self.grid_height or x + dx < 0 or x + dx >= self.grid_width:
                                self.dungeon_tiles[y][x] = 'Border_wall'  # 邊界牆壁
                                breaker = True
                            elif self.dungeon_tiles[y + dy][x + dx] == 'Outside':
                                self.dungeon_tiles[y][x] = 'Border_wall'  # 邊界牆壁
                                breaker = True
                            if breaker:
                                break
                        if breaker:
                            break

        print("添加牆壁完成")

    def initialize_dungeon(self) -> None:
        # 初始化地牢，生成房間和橋接
        self._initialize_grid()  # 初始化網格
        self.bsp_tree = BSPNode(0, 0, self.grid_width, self.grid_height)  # 創建 BSP 樹根節點
        self._split_bsp(self.bsp_tree, 0)  # 執行 BSP 分割
        self.rooms = []
        self._collect_rooms(self.bsp_tree, self.rooms)  # 收集所有房間
        self.total_appeared_rooms = len(self.rooms)
        if not self.rooms:
            raise ValueError("未生成任何房間")

        self.rooms[0].id = 0  # 設置起始房間 ID
        self.current_room_id = 0

        # 選擇距離房間 0 最遠的房間作為終點房間
        if len(self.rooms) > 1:
            max_dist = 0
            end_room = None
            start_center = (self.rooms[0].x + self.rooms[0].width / 2, self.rooms[0].y + self.rooms[0].height / 2)
            for room in self.rooms[1:]:
                room_center = (room.x + room.width / 2, room.y + room.height / 2)
                dist = abs(room_center[0] - start_center[0]) + abs(room_center[1] - start_center[1])  # 曼哈頓距離
                if dist > max_dist:
                    max_dist = dist
                    end_room = room
            if end_room:
                end_room.is_end_room = True
                # 更新終點房間的瓦片
                for row in range(1, int(end_room.height) - 1):
                    for col in range(1, int(end_room.width) - 1):
                        end_room.tiles[row][col] = 'E'
                center_x = int(end_room.width) // 2
                center_y = int(end_room.height) // 2
                end_room.tiles[center_y][center_x] = 'G'
                print(f"指定房間 {end_room.id} 為終點房間，距離起點 {max_dist}")

        # 放置所有房間
        for room in self.rooms:
            self._place_room(room)

        # 生成並放置橋接
        bridges = self._generate_bridges(self.rooms)
        for bridge in bridges:
            self._place_bridge(bridge)

        # 加入牆壁
        self._add_walls()

        print(f"初始化地牢：{len(self.rooms)} 個房間，{len(bridges)} 個橋接")

    def _place_room(self, room: Room) -> None:

        # 將房間瓦片放置到地牢網格中
        grid_x = int(room.x)
        grid_y = int(room.y)
        # 如果房間超出網格，擴展網格
        if (grid_x < 0 or grid_x + int(room.width) > self.grid_width or \
            grid_y < 0 or grid_y + int(room.height) > self.grid_height):
            self.expand_grid(grid_x + int(room.width), grid_y + int(room.height))
        # 複製房間瓦片到網格
        for row in range(int(room.height)):
            for col in range(int(room.width)):
                self.dungeon_tiles[grid_y + row][grid_x + col] = room.tiles[row][col]
        print(f"放置房間 {room.id} 在網格 ({grid_x}, {grid_y})")

    def get_room(self, room_id: int) -> Room:
        # 根據房間 ID 獲取房間對象
        try:
            return next(r for r in self.rooms if r.id == room_id)
        except StopIteration:
            raise ValueError(f"未找到房間 {room_id}")

    def expand_grid(self, new_width: int, new_height: int) -> None:
        # 擴展地牢網格以適應新尺寸
        if new_width > self.grid_width:
            for row in self.dungeon_tiles:
                row.extend(['W' for _ in range(new_width - self.grid_width)])
            self.grid_width = new_width
        if new_height > self.grid_height:
            self.dungeon_tiles.extend([['W' for _ in range(self.grid_width)] for _ in range(new_height - self.grid_height)])
            self.grid_height = new_height
        print(f"擴展網格到 ({self.grid_width}, {self.grid_height})")

    def get_tile_at(self, pos: Tuple[float, float]) -> str:
        # 根據像素座標獲取瓦片類型
        tile_x = int(pos[0] // self.TILE_SIZE)  # 轉換為瓦片座標
        tile_y = int(pos[1] // self.TILE_SIZE)
        if 0 <= tile_y < self.grid_height and 0 <= tile_x < self.grid_width:
            return self.dungeon_tiles[tile_y][tile_x]
        return 'W'  # 超出範圍返回牆壁
