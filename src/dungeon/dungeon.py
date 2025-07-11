# src/dungeon/dungeon.py
from dataclasses import dataclass
from typing import List, Tuple, Optional
from src.config import DungeonConfig
from src.dungeon.room import Room, RoomType
from src.dungeon.bridge import Bridge
from src.dungeon.BSPnode import BSPNode
import random

# 地牢生成類，負責生成 BSP 地牢並管理房間與走廊
class Dungeon:
    ROOM_WIDTH = DungeonConfig.ROOM_WIDTH.value
    ROOM_HEIGHT = DungeonConfig.ROOM_HEIGHT.value
    GRID_WIDTH = DungeonConfig.GRID_WIDTH.value
    GRID_HEIGHT = DungeonConfig.GRID_HEIGHT.value
    MIN_ROOM_SIZE = DungeonConfig.MIN_ROOM_SIZE.value
    TILE_SIZE = DungeonConfig.TILE_SIZE.value
    ROOM_GAP = DungeonConfig.ROOM_GAP.value
    BIAS_RATIO = DungeonConfig.BIAS_RATIO.value
    BIAS_STRENGTH = DungeonConfig.BIAS_STRENGTH.value
    MIN_BRIDGE_WIDTH = DungeonConfig.MIN_BRIDGE_WIDTH.value
    MAX_BRIDGE_WIDTH = DungeonConfig.MAX_BRIDGE_WIDTH.value
    MAX_SPLIT_DEPTH = DungeonConfig.MAX_SPLIT_DEPTH.value
    EXTRA_BRIDGE_RATIO = DungeonConfig.EXTRA_BRIDGE_RATIO.value
    MOMSTER_ROOM_RATIO = DungeonConfig.MOMSTER_ROOM_RATIO.value
    TRAP_ROOM_RATIO = DungeonConfig.TRAP_ROOM_RATIO.value
    REWARD_ROOM_RATIO = DungeonConfig.REWARD_ROOM_RATIO.value
    LOBBY_WIDTH = DungeonConfig.LOBBY_WIDTH.value
    LOBBY_HEIGHT = DungeonConfig.LOBBY_HEIGHT.value
    game = None

    def __init__(self):
        self.rooms: List[Room] = []
        self.bridges: List[Bridge] = []
        self.current_room_id = 0
        self.dungeon_tiles: List[List[str]] = []
        self.grid_width = 0
        self.grid_height = 0
        self.next_room_id = 0
        self.total_appeared_rooms = 0
        self.bsp_tree: Optional[BSPNode] = None

    def _initialize_grid(self) -> None:
        """初始化地牢網格，創建空的瓦片陣列"""
        self.grid_width = self.GRID_WIDTH
        self.grid_height = self.GRID_HEIGHT
        self.dungeon_tiles = [['Outside' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        print(f"初始化地牢網格：寬度={self.grid_width}, 高度={self.grid_height}")

    def generate_room(self, x: float, y: float, width: float, height: float, room_id: int, room_type: RoomType = RoomType.EMPTY) -> Room:
        """生成單個房間物件，包含房間的瓦片數據"""
        tiles = [['Room_floor' for _ in range(int(width))] for _ in range(int(height))]
        room = Room(id=room_id, x=x, y=y, width=width, height=height, tiles=tiles, room_type=room_type)
        print(f"生成房間 {room_id} 在 ({x}, {y}), 尺寸=({width}, {height}), 房間類型={room_type}")
        return room

    def _configure_end_room(self, tiles: List[List[str]], width: float, height: float) -> None:
        """配置終點房間的瓦片，將內部設為 End_room_floor，中間放置傳送門"""
        for row in range(1, int(height) - 1):
            for col in range(1, int(width) - 1):
                tiles[row][col] = 'End_room_floor'
        center_x = int(width) // 2
        center_y = int(height) // 2
        tiles[center_y][center_x] = 'End_room_portal'

    def _split_bsp(self, node: BSPNode, depth: int, max_depth: int = MAX_SPLIT_DEPTH) -> None:
        """使用二元空間分割（BSP）將地牢空間分成小區域"""
        min_split_size = self.MIN_ROOM_SIZE + self.ROOM_GAP * 2
        if self._should_stop_splitting(node, depth, max_depth, min_split_size):
            self._try_generate_room(node, min_split_size)
            return

        split_direction = self._choose_split_direction(node, min_split_size)
        if not split_direction:
            self._try_generate_room(node, min_split_size)
            return

        self._perform_split(node, split_direction, min_split_size)
        if node.left:
            self._split_bsp(node.left, depth + 1, max_depth)
        if node.right:
            self._split_bsp(node.right, depth + 1, max_depth)

    def _should_stop_splitting(self, node: BSPNode, depth: int, max_depth: int, min_split_size: float) -> bool:
        """判斷是否應停止 BSP 分割"""
        return depth >= max_depth or (node.width < min_split_size * 2 and node.height < min_split_size * 2)

    def _try_generate_room(self, node: BSPNode, min_split_size: float) -> None:
        """嘗試在 BSP 節點中生成房間"""
        if node.width >= min_split_size and node.height >= min_split_size:
            room_width, room_height, room_x, room_y = self._generate_room_bounds(
                (node.x, node.y, node.x + node.width, node.y + node.height)
            )
            node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
            self.next_room_id += 1

    def _choose_split_direction(self, node: BSPNode, min_split_size: float) -> Optional[str]:
        """根據節點尺寸選擇分割方向"""
        can_split_horizontally = node.width >= min_split_size * 2
        can_split_vertically = node.height >= min_split_size * 2
        if not (can_split_horizontally or can_split_vertically):
            return None

        w, h = node.width, node.height
        total = w * w + h * h
        vertical_weight = w * w / total
        horizontal_weight = h * h / total
        possible_directions = []
        weights = []

        if can_split_horizontally:
            possible_directions.append("vertical")
            weights.append(vertical_weight)
        if can_split_vertically:
            possible_directions.append("horizontal")
            weights.append(horizontal_weight)

        return random.choices(possible_directions, weights=weights)[0]

    def _perform_split(self, node: BSPNode, direction: str, min_split_size: float) -> None:
        """執行 BSP 分割，創建左和右子節點"""
        if direction == "vertical":
            split_x = random.randint(min_split_size, int(node.width - min_split_size))
            node.left = BSPNode(node.x, node.y, split_x, node.height)
            node.right = BSPNode(node.x + split_x, node.y, node.width - split_x, node.height)
        else:
            split_y = random.randint(min_split_size, int(node.height - min_split_size))
            node.left = BSPNode(node.x, node.y, node.width, split_y)
            node.right = BSPNode(node.x, node.y + split_y, node.width, node.height - split_y)

    def _generate_room_bounds(self, partition: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """根據 BSP 分區計算房間的邊界（位置和尺寸）"""
        x0, y0, x1, y1 = partition
        room_x = x0 + self.ROOM_GAP
        room_y = y0 + self.ROOM_GAP
        max_width = x1 - x0 - 2 * self.ROOM_GAP
        max_height = y1 - y0 - 2 * self.ROOM_GAP
        room_width = min(max_width, self.ROOM_WIDTH)
        room_height = min(max_height, self.ROOM_HEIGHT)
        room_width = max(room_width, self.MIN_ROOM_SIZE)
        room_height = max(room_height, self.MIN_ROOM_SIZE)
        print(f"生成房間邊界：位置=({room_x}, {room_y}), 尺寸=({room_width}, {room_height})")
        return room_width, room_height, room_x, room_y

    def _collect_rooms(self, node: BSPNode, rooms: List[Room]) -> None:
        """遍歷 BSP 樹，收集所有包含房間的葉節點"""
        if node.room:
            rooms.append(node.room)
        if node.left:
            self._collect_rooms(node.left, rooms)
        if node.right:
            self._collect_rooms(node.right, rooms)

    def _check_bridge_room_collision(self, bridge: Bridge, room1: Room, room2: Room) -> bool:
        """檢查走廊是否與其他房間相交（除了要連接的兩個房間）"""
        x0 = min(bridge.x0, bridge.x1)
        y0 = min(bridge.y0, bridge.y1)
        x1 = max(bridge.x0, bridge.x1)
        y1 = max(bridge.y0, bridge.y1)

        for room in self.rooms:
            if room.id == room1.id or room.id == room2.id:
                continue
            room_x0 = room.x
            room_y0 = room.y
            room_x1 = room.x + room.width
            room_y1 = room.y + room.height
            if not (x1 < room_x0 or x0 > room_x1 or y1 < room_y0 or y0 > room_y1):
                return True
        return False

    def _generate_bridge(self, room1: Room, room2: Room) -> List[Bridge]:
        """生成兩個房間之間的走廊，優先直線，否則用 L 形路徑"""
        start_x, start_y, end_x, end_y, room1, room2 = self._select_connection_points(room1, room2)
        bridge_width = self._calculate_bridge_width()

        return self._try_generate_bridge_paths(room1, room2, start_x, start_y, end_x, end_y, bridge_width)

    def _select_connection_points(self, room1: Room, room2: Room) -> Tuple[int, int, int, int, Room, Room]:
        """選擇兩個房間的隨機連接點，並確保起點在左側"""
        def rand_room_point(room: Room) -> Tuple[int, int]:
            x = random.randint(int(room.x + 2), int(room.x + room.width - 3))
            y = random.randint(int(room.y + 2), int(room.y + room.height - 3))
            return x, y

        start_x, start_y = rand_room_point(room1)
        end_x, end_y = rand_room_point(room2)

        if start_x > end_x:
            start_x, end_x = end_x, start_x
            start_y, end_y = end_y, start_y
            room1, room2 = room2, room1
        return start_x, start_y, end_x, end_y, room1, room2

    def _calculate_bridge_width(self) -> int:
        """計算隨機走廊寬度，使用高斯分佈"""
        bridge_width = int(random.gauss((self.MIN_BRIDGE_WIDTH + self.MAX_BRIDGE_WIDTH) // 2,
                                        (self.MAX_BRIDGE_WIDTH - self.MIN_BRIDGE_WIDTH) / 2))
        return max(self.MIN_BRIDGE_WIDTH, min(bridge_width, self.MAX_BRIDGE_WIDTH))

    def _create_horizontal_bridge(self, x1: int, y: int, x2: int, width: int, room1: Room, room2: Room) -> Bridge:
        """生成水平走廊段"""
        return Bridge(
            x0=min(x1, x2),
            y0=y - width / 2,
            x1=max(x1, x2),
            y1=y + width / 2,
            width=width,
            room1_id=room1.id,
            room2_id=room2.id
        )

    def _create_vertical_bridge(self, x: int, y1: int, y2: int, width: int, room1: Room, room2: Room) -> Bridge:
        """生成垂直走廊段"""
        return Bridge(
            x0=x - width / 2,
            y0=min(y1, y2),
            x1=x + width / 2,
            y1=max(y1, y2),
            width=width,
            room1_id=room1.id,
            room2_id=room2.id
        )

    def _try_generate_bridge_paths(self, room1: Room, room2: Room, start_x: int, start_y: int, end_x: int, end_y: int, bridge_width: int) -> List[Bridge]:
        """嘗試生成直線或 L 形走廊路徑"""
        bridges = []
        if abs(start_x - end_x) <= 1:
            bridge = self._create_vertical_bridge(start_x, start_y, end_y, bridge_width, room1, room2)
            if not self._check_bridge_room_collision(bridge, room1, room2):
                bridges.append(bridge)
                print("直線垂直橋接")
            else:
                bridges = self._generate_l_shape_bridge(room1, room2, start_x, start_y, end_x, end_y, bridge_width, horizontal_first=True)
        elif abs(start_y - end_y) <= 1:
            bridge = self._create_horizontal_bridge(start_x, start_y, end_x, bridge_width, room1, room2)
            if not self._check_bridge_room_collision(bridge, room1, room2):
                bridges.append(bridge)
                print("直線水平橋接")
            else:
                bridges = self._generate_l_shape_bridge(room1, room2, start_x, start_y, end_x, end_y, bridge_width, horizontal_first=False)
        else:
            bridges = self._generate_l_shape_bridge(room1, room2, start_x, start_y, end_x, end_y, bridge_width, random.choice([True, False]))

        print(f"橋接從房間 {room1.id} 到 {room2.id}")
        print(f"起點: ({start_x}, {start_y}) → 終點: ({end_x}, {end_y}) | 寬度: {bridge_width}")
        print(f"橋接段: {[str(bridge) for bridge in bridges]}")
        return bridges

    def _generate_l_shape_bridge(self, room1: Room, room2: Room, start_x: int, start_y: int, end_x: int, end_y: int, bridge_width: int, horizontal_first: bool) -> List[Bridge]:
        """生成 L 形走廊路徑，優先嘗試指定方向，失敗則嘗試另一方向"""
        bridges = []
        if horizontal_first:
            bridge1 = self._create_horizontal_bridge(start_x, start_y, end_x, bridge_width, room1, room2)
            bridge2 = self._create_vertical_bridge(end_x, start_y, end_y, bridge_width, room1, room2)
            if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                bridges.extend([bridge1, bridge2])
                print("L形橋接 (水平→垂直)")
            else:
                bridge1 = self._create_vertical_bridge(start_x, start_y, end_y, bridge_width, room1, room2)
                bridge2 = self._create_horizontal_bridge(start_x, end_y, end_x, bridge_width, room1, room2)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("L形橋接 (垂直→水平)")
                else:
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (垂直→水平，忽略碰撞)")
        else:
            bridge1 = self._create_vertical_bridge(start_x, start_y, end_y, bridge_width, room1, room2)
            bridge2 = self._create_horizontal_bridge(start_x, end_y, end_x, bridge_width, room1, room2)
            if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                bridges.extend([bridge1, bridge2])
                print("L形橋接 (垂直→水平)")
            else:
                bridge1 = self._create_horizontal_bridge(start_x, start_y, end_x, bridge_width, room1, room2)
                bridge2 = self._create_vertical_bridge(end_x, start_y, end_y, bridge_width, room1, room2)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("L形橋接 (水平→垂直)")
                else:
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (水平→垂直，忽略碰撞)")
        return bridges

    def _generate_bridges(self, rooms: List[Room]) -> List[Bridge]:
        """生成所有房間之間的走廊，確保連通並添加額外走廊"""
        bridges = []
        connected_pairs = set()
        rooms_left = rooms[:]
        current_room = rooms_left[0]

        # 生成最小生成樹，確保所有房間連通
        bridges.extend(self._generate_minimum_spanning_bridges(rooms_left, connected_pairs))

        # 添加額外走廊以增加路徑多樣性
        bridges.extend(self._generate_extra_bridges(rooms, connected_pairs))

        print(f"總共生成 {len(bridges)} 個橋接，連通 {len(connected_pairs)} 對房間")
        return bridges

    def _generate_minimum_spanning_bridges(self, rooms_left: List[Room], connected_pairs: set) -> List[Bridge]:
        """生成最小生成樹的走廊，確保所有房間連通"""
        bridges = []
        current_room = rooms_left[0]
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
        return bridges

    def _generate_extra_bridges(self, rooms: List[Room], connected_pairs: set) -> List[Bridge]:
        """生成額外走廊，增加地牢連通性"""
        bridges = []
        extra_bridges = int(len(rooms) * self.EXTRA_BRIDGE_RATIO)
        room_ids = [room.id for room in rooms]
        end_room_id = next((room.id for room in rooms if room.is_end_room), None)

        possible_pairs = [
            (id1, id2, ((rooms[id1].x + rooms[id1].width / 2 - rooms[id2].x - rooms[id2].width / 2) ** 2 +
                        (rooms[id1].y + rooms[id1].height / 2 - rooms[id2].y - rooms[id2].height / 2) ** 2) ** 0.5)
            for i, id1 in enumerate(room_ids)
            for id2 in room_ids[i + 1:]
            if (id2 < len(room_ids)) and (end_room_id is None or (id1 != end_room_id and id2 != end_room_id))
        ]
        possible_pairs.sort(key=lambda x: x[2], reverse=True)
        available_pairs = [(id1, id2) for id1, id2, _ in possible_pairs if tuple(sorted([id1, id2])) not in connected_pairs]
        actual_bridges = min(extra_bridges, len(available_pairs))

        max_bridges_per_room = 3
        room_bridge_count = {room.id: 0 for room in rooms}
        selected_pairs = []
        for id1, id2 in available_pairs:
            if room_bridge_count[id1] < max_bridges_per_room and room_bridge_count[id2] < max_bridges_per_room:
                selected_pairs.append((id1, id2))
                room_bridge_count[id1] += 1
                room_bridge_count[id2] += 1
            if len(selected_pairs) >= actual_bridges:
                break

        for id1, id2 in selected_pairs:
            room1 = next(r for r in rooms if r.id == id1)
            room2 = next(r for r in rooms if r.id == id2)
            bridges.extend(self._generate_bridge(room1, room2))
            connected_pairs.add(tuple(sorted([id1, id2])))
        return bridges

    def _find_closest_room(self, room: Room, rooms: List[Room]) -> Optional[Room]:
        """找到距離指定房間最近的其他房間"""
        closest_room = None
        closest_distance = float('inf')
        room_center = (room.x + room.width / 2, room.y + room.height / 2)
        for compare_room in rooms:
            compare_center = (compare_room.x + compare_room.width / 2, compare_room.y + compare_room.height / 2)
            dist = ((compare_center[0] - room_center[0]) ** 2 + (compare_center[1] - room_center[1]) ** 2) ** 0.5
            if dist < closest_distance:
                closest_distance = dist
                closest_room = compare_room
        return closest_room

    def _place_bridge(self, bridge: Bridge) -> None:
        """將走廊放置到地牢網格中，設為 Bridge_floor"""
        x0 = int(min(bridge.x0, bridge.x1))
        y0 = int(min(bridge.y0, bridge.y1))
        x1 = int(max(bridge.x0, bridge.x1))
        y1 = int(max(bridge.y0, bridge.y1))
        if x1 - x0 == 0:
            x1 = x0 + 1
        if y1 - y0 == 0:
            y1 = y0 + 1
        for y in range(max(0, y0 - 1), min(y1 + 1, self.grid_height)):
            for x in range(max(0, x0 - 1), min(x1 + 1, self.grid_width)):
                if self.dungeon_tiles[y][x] and self.dungeon_tiles[y][x] != 'Outside':
                    continue
                self.dungeon_tiles[y][x] = 'Bridge_floor'
        print(f"放置橋接：從 ({x0}, {y0}) 到 ({x1}, {y1})")

    def _add_walls(self) -> None:
        """為地牢中的地板瓦片添加邊界牆壁"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] in ['Room_floor', 'Bridge_floor']:
                    if self._is_border_tile(x, y):
                        self.dungeon_tiles[y][x] = 'Border_wall'

    def _is_border_tile(self, x: int, y: int) -> bool:
        """檢查指定瓦片是否應設為邊界牆壁"""
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if y + dy < 0 or y + dy >= self.grid_height or x + dx < 0 or x + dx >= self.grid_width:
                    return True
                if self.dungeon_tiles[y + dy][x + dx] == 'Outside':
                    return True
        return False

    def _assign_room_types(self) -> None:
        """分配房間類型：隨機選擇出生房，設置最遠房間為終點房，其餘隨機分配"""
        if not self.rooms:
            raise ValueError("無房間可分配類型")

        # 隨機選擇出生房
        self.current_room_id = random.choice(range(len(self.rooms)))
        start_room = self.rooms[self.current_room_id]
        start_room.room_type = RoomType.START
        print(f"指定房間 {start_room.id} 為出生房")

        # 找到離出生房最遠的房間作為終點房
        if len(self.rooms) > 1:
            max_dist = 0
            end_room = None
            start_center = (start_room.x + start_room.width / 2, start_room.y + start_room.height / 2)
            for room in self.rooms:
                if room.id == start_room.id:
                    continue
                room_center = (room.x + room.width / 2, room.y + room.height / 2)
                dist = abs(room_center[0] - start_center[0]) + abs(room_center[1] - start_center[1])
                if dist > max_dist:
                    max_dist = dist
                    end_room = room
            if end_room:
                end_room.room_type = RoomType.END
                print(f"指定房間 {end_room.id} 為終點房間，距離出生房 {max_dist}")

        # 隨機分配其他房間類型
        for room in self.rooms:
            if room.room_type not in [RoomType.START, RoomType.END]:
                room_type = random.choices(
                    [RoomType.MONSTER, RoomType.TRAP, RoomType.REWARD],
                    weights=[self.MOMSTER_ROOM_RATIO, self.TRAP_ROOM_RATIO, self.REWARD_ROOM_RATIO],
                    k=1
                )[0]
                room.room_type = room_type
                print(f"房間 {room.id} 分配為 {room_type} 類型")
    
    def initialize_dungeon(self) -> None:
        """初始化整個地牢，生成房間、走廊和牆壁"""
        self._initialize_grid()
        self.bsp_tree = BSPNode(0, 0, self.grid_width, self.grid_height)
        self._split_bsp(self.bsp_tree, 0)
        self.rooms = []
        self.bridges = []
        self.next_room_id = 0
        self._collect_rooms(self.bsp_tree, self.rooms)
        self.total_appeared_rooms = len(self.rooms)
        if not self.rooms:
            raise ValueError("未生成任何房間")

        self._assign_room_types()

        self._place_rooms()
        self.bridges = self._generate_bridges(self.rooms)
        for bridge in self.bridges:
            self._place_bridge(bridge)
        self._add_walls()
        print(f"初始化地牢：{len(self.rooms)} 個房間，{len(self.bridges)} 個橋接")

    def _place_rooms(self) -> None:
        """將所有房間放置到地牢網格中"""
        for room in self.rooms:
            room._configure_tiles()
            self._place_room(room)

    def _place_room(self, room: Room) -> None:
        """將單個房間的瓦片放置到地牢網格中"""
        grid_x = int(room.x)
        grid_y = int(room.y)
        if (grid_x < 0 or grid_x + int(room.width) > self.grid_width or
                grid_y < 0 or grid_y + int(room.height) > self.grid_height):
            self.expand_grid(grid_x + int(room.width), grid_y + int(room.height))
        for row in range(int(room.height)):
            for col in range(int(room.width)):
                self.dungeon_tiles[grid_y + row][grid_x + col] = room.tiles[row][col]
        print(f"放置房間 {room.id} 在網格 ({grid_x}, {grid_y})")

    def get_room(self, room_id: int) -> Room:
        """根據房間 ID 獲取房間物件"""
        try:
            return next(r for r in self.rooms if r.id == room_id)
        except StopIteration:
            raise ValueError(f"未找到房間 {room_id}")

    def expand_grid(self, new_width: int, new_height: int) -> None:
        """擴展地牢網格以適應更大的尺寸"""
        if new_width > self.grid_width:
            for row in self.dungeon_tiles:
                row.extend(['W' for _ in range(new_width - self.grid_width)])
            self.grid_width = new_width
        if new_height > self.grid_height:
            self.dungeon_tiles.extend([['W' for _ in range(self.grid_width)] for _ in range(new_height - self.grid_height)])
            self.grid_height = new_height
        print(f"擴展網格到 ({self.grid_width}, {self.grid_height})")

    def get_tile_at(self, pos: Tuple[float, float]) -> str:
        """根據像素座標獲取對應的瓦片類型"""
        tile_x = int(pos[0] // self.TILE_SIZE)
        tile_y = int(pos[1] // self.TILE_SIZE)
        if 0 <= tile_y < self.grid_height and 0 <= tile_x < self.grid_width:
            return self.dungeon_tiles[tile_y][tile_x]
        return 'W'

    def initialize_lobby(self) -> None:
        self._initialize_grid()
        self.rooms = []
        self.bridges = []
        self.next_room_id = 0
        lobby_width = self.LOBBY_WIDTH
        lobby_height = self.LOBBY_HEIGHT
        lobby_x = (self.grid_width - lobby_width) // 2
        lobby_y = (self.grid_height - lobby_height) // 2
        lobby_room = self.generate_room(lobby_x, lobby_y, lobby_width, lobby_height, self.next_room_id, RoomType.LOBBY)
        self.next_room_id += 1
        self.rooms.append(lobby_room)
        self.total_appeared_rooms = len(self.rooms)
        self._place_room(lobby_room)
        self._add_walls()
        print(f"初始化大廳：房間 {lobby_room.id} 在 ({lobby_x}, {lobby_y})")