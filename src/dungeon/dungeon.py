from dataclasses import dataclass
from typing import List, Tuple, Optional
from src.config import DungeonConfig
from src.dungeon.room import Room
import random

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

# 定義 Bridge 類，用於表示房間之間的走廊
@dataclass
class Bridge:
    x0: float  # 走廊起點的 x 座標
    y0: float  # 走廊起點的 y 座標
    x1: float  # 走廊終點的 x 座標
    y1: float  # 走廊終點的 y 座標
    width: float  # 走廊的寬度（瓦片單位）
    room1_id: int  # 連接的第一個房間 ID
    room2_id: int  # 連接的第二個房間 ID

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
    game = None

    def __init__(self):
        self.rooms: List[Room] = []
        self.bridges: List[Bridge] = []  # 改用 Bridge 物件列表
        self.current_room_id = 0
        self.dungeon_tiles: List[List[str]] = []
        self.grid_width = 0
        self.grid_height = 0
        self.next_room_id = 0
        self.total_appeared_rooms = 0
        self.bsp_tree: Optional[BSPNode] = None

    def _initialize_grid(self) -> None:
        self.grid_width = self.GRID_WIDTH
        self.grid_height = self.GRID_HEIGHT
        self.dungeon_tiles = [['Outside' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        print(f"初始化地牢網格：寬度={self.grid_width}, 高度={self.grid_height}")

    def generate_room(self, x: float, y: float, width: float, height: float, room_id: int, is_end_room: bool = False) -> Room:
        tiles = [['Room_floor' for _ in range(int(width))] for _ in range(int(height))]
        if is_end_room:
            for row in range(1, int(height) - 1):
                for col in range(1, int(width) - 1):
                    tiles[row][col] = 'End_room_floor'
            center_x = int(width) // 2
            center_y = int(height) // 2
            tiles[center_y][center_x] = 'End_room_portal'
        room = Room(id=room_id, x=x, y=y, width=width, height=height, tiles=tiles, is_end_room=is_end_room)
        print(f"生成房間 {room_id} 在 ({x}, {y}), 尺寸=({width}, {height}), 終點房間={is_end_room}")
        return room

    def _split_bsp(self, node: BSPNode, depth: int, max_depth: int = MAX_SPLIT_DEPTH) -> None:
        min_split_size = self.MIN_ROOM_SIZE + self.ROOM_GAP * 2
        if depth >= max_depth or (node.width < min_split_size * 2 and node.height < min_split_size * 2):
            if node.width >= min_split_size and node.height >= min_split_size:
                room_width, room_height, room_x, room_y = self._generate_room_bounds(
                    (node.x, node.y, node.x + node.width, node.y + node.height)
                )
                node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
                self.next_room_id += 1
            return

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

        if not possible_directions:
            if node.width >= min_split_size and node.height >= min_split_size:
                room_width, room_height, room_x, room_y = self._generate_room_bounds(
                    (node.x, node.y, node.x + node.width, node.y + node.height)
                )
                node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
                self.next_room_id += 1
            return

        direction = random.choices(possible_directions, weights=weights)[0]
        if direction == "vertical":
            split_x = random.randint(min_split_size, int(node.width - min_split_size))
            node.left = BSPNode(node.x, node.y, split_x, node.height)
            node.right = BSPNode(node.x + split_x, node.y, node.width - split_x, node.height)
        else:
            split_y = random.randint(min_split_size, int(node.height - min_split_size))
            node.left = BSPNode(node.x, node.y, node.width, split_y)
            node.right = BSPNode(node.x, node.y + split_y, node.width, node.height - split_y)

        if node.left:
            self._split_bsp(node.left, depth + 1, max_depth)
        if node.right:
            self._split_bsp(node.right, depth + 1, max_depth)

    def _generate_room_bounds(self, partition: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
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
        if node.room:
            rooms.append(node.room)
        if node.left:
            self._collect_rooms(node.left, rooms)
        if node.right:
            self._collect_rooms(node.right, rooms)

    def _check_bridge_room_collision(self, bridge: Bridge, room1: Room, room2: Room) -> bool:
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
        def rand_room_point(room: Room) -> Tuple[int, int]:
            x = random.randint(int(room.x + 2), int(room.x + room.width - 3))
            y = random.randint(int(room.y + 2), int(room.y + room.height - 3))
            return x, y

        def add_horizontal(x1: int, y: int, x2: int, width: int) -> Bridge:
            return Bridge(
                x0=min(x1, x2),
                y0=y - width / 2,
                x1=max(x1, x2),
                y1=y + width / 2,
                width=width,
                room1_id=room1.id,
                room2_id=room2.id
            )

        def add_vertical(x: int, y1: int, y2: int, width: int) -> Bridge:
            return Bridge(
                x0=x - width / 2,
                y0=min(y1, y2),
                x1=x + width / 2,
                y1=max(y1, y2),
                width=width,
                room1_id=room1.id,
                room2_id=room2.id
            )

        bridges = []
        start_x, start_y = rand_room_point(room1)
        end_x, end_y = rand_room_point(room2)

        if start_x > end_x:
            start_x, end_x = end_x, start_x
            start_y, end_y = end_y, start_y
            room1, room2 = room2, room1

        bridge_width = int(random.gauss((self.MIN_BRIDGE_WIDTH + self.MAX_BRIDGE_WIDTH) // 2, (self.MAX_BRIDGE_WIDTH - self.MIN_BRIDGE_WIDTH) / 2))
        bridge_width = max(self.MIN_BRIDGE_WIDTH, min(bridge_width, self.MAX_BRIDGE_WIDTH))

        if abs(start_x - end_x) <= 1:
            bridge = add_vertical(start_x, start_y, end_y, bridge_width)
            if not self._check_bridge_room_collision(bridge, room1, room2):
                bridges.append(bridge)
                print("直線垂直橋接")
            else:
                bridge1 = add_horizontal(start_x, start_y, end_x, bridge_width)
                bridge2 = add_vertical(end_x, start_y, end_y, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (水平→垂直)")
                else:
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (水平→垂直，忽略碰撞)")
        elif abs(start_y - end_y) <= 1:
            bridge = add_horizontal(start_x, start_y, end_x, bridge_width)
            if not self._check_bridge_room_collision(bridge, room1, room2):
                bridges.append(bridge)
                print("直線水平橋接")
            else:
                bridge1 = add_vertical(start_x, start_y, end_y, bridge_width)
                bridge2 = add_horizontal(start_x, end_y, end_x, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (垂直→水平)")
                else:
                    bridges.extend([bridge1, bridge2])
                    print("後備L形橋接 (垂直→水平，忽略碰撞)")
        else:
            if random.choice([True, False]):
                bridge1 = add_horizontal(start_x, start_y, end_x, bridge_width)
                bridge2 = add_vertical(end_x, start_y, end_y, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("L形橋接 (水平→垂直)")
                else:
                    bridge1 = add_vertical(start_x, start_y, end_y, bridge_width)
                    bridge2 = add_horizontal(start_x, end_y, end_x, bridge_width)
                    if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                        bridges.extend([bridge1, bridge2])
                        print("L形橋接 (垂直→水平)")
                    else:
                        bridges.extend([bridge1, bridge2])
                        print("後備L形橋接 (垂直→水平，忽略碰撞)")
            else:
                bridge1 = add_vertical(start_x, start_y, end_y, bridge_width)
                bridge2 = add_horizontal(start_x, end_y, end_x, bridge_width)
                if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                    bridges.extend([bridge1, bridge2])
                    print("L形橋接 (垂直→水平)")
                else:
                    bridge1 = add_horizontal(start_x, start_y, end_x, bridge_width)
                    bridge2 = add_vertical(end_x, start_y, end_y, bridge_width)
                    if not self._check_bridge_room_collision(bridge1, room1, room2) and not self._check_bridge_room_collision(bridge2, room1, room2):
                        bridges.extend([bridge1, bridge2])
                        print("L形橋接 (水平→垂直)")
                    else:
                        bridges.extend([bridge1, bridge2])
                        print("後備L形橋接 (水平→垂直，忽略碰撞)")

        print(f"橋接從房間 {room1.id} 到 {room2.id}")
        print(f"起點: ({start_x}, {start_y}) → 終點: ({end_x}, {end_y}) | 寬度: {bridge_width}")
        print(f"橋接段: {[str(bridge) for bridge in bridges]}")
        return bridges

    def _generate_bridges(self, rooms: List[Room]) -> List[Bridge]:
        bridges = []
        connected_pairs = set()
        rooms_left = rooms[:]
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

        extra_bridges = int(len(rooms) * self.EXTRA_BRIDGE_RATIO)
        room_ids = [room.id for room in rooms]
        end_room_id = next((room.id for room in rooms if room.is_end_room), None)
        possible_pairs = [
            (id1, id2, ((rooms[id1].x + rooms[id1].width / 2 - rooms[id2].x - rooms[id2].width / 2) ** 2 +
                        (rooms[id1].y + rooms[id1].height / 2 - rooms[id2].y - rooms[id2].height / 2) ** 2) ** 0.5)
            for i, id1 in enumerate(room_ids)
            for id2 in room_ids[i + 1:]
            if end_room_id is None or (id1 != end_room_id and id2 != end_room_id)
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

        print(f"總共生成 {len(bridges)} 個橋接，連通 {len(connected_pairs)} 對房間")
        return bridges

    def _find_closest_room(self, room: Room, rooms: List[Room]) -> Optional[Room]:
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
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] in ['Room_floor', 'Bridge_floor']:
                    breaker = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if y + dy < 0 or y + dy >= self.grid_height or x + dx < 0 or x + dx >= self.grid_width:
                                self.dungeon_tiles[y][x] = 'Border_wall'
                                breaker = True
                            elif self.dungeon_tiles[y + dy][x + dx] == 'Outside':
                                self.dungeon_tiles[y][x] = 'Border_wall'
                                breaker = True
                            if breaker:
                                break
                        if breaker:
                            break
        print("添加牆壁完成")

    def initialize_dungeon(self) -> None:
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

        self.rooms[0].id = 0
        self.current_room_id = 0

        if len(self.rooms) > 1:
            max_dist = 0
            end_room = None
            start_center = (self.rooms[0].x + self.rooms[0].width / 2, self.rooms[0].y + self.rooms[0].height / 2)
            for room in self.rooms[1:]:
                room_center = (room.x + room.width / 2, room.y + room.height / 2)
                dist = abs(room_center[0] - start_center[0]) + abs(room_center[1] - start_center[1])
                if dist > max_dist:
                    max_dist = dist
                    end_room = room
            if end_room:
                end_room.is_end_room = True
                for row in range(1, int(end_room.height) - 1):
                    for col in range(1, int(end_room.width) - 1):
                        end_room.tiles[row][col] = 'End_room_floor'
                center_x = int(end_room.width) // 2
                center_y = int(end_room.height) // 2
                end_room.tiles[center_y][center_x] = 'End_room_portal'
                print(f"指定房間 {end_room.id} 為終點房間，距離起點 {max_dist}")

        for room in self.rooms:
            self._place_room(room)

        self.bridges = self._generate_bridges(self.rooms)
        for bridge in self.bridges:
            self._place_bridge(bridge)

        self._add_walls()
        print(f"初始化地牢：{len(self.rooms)} 個房間，{len(self.bridges)} 個橋接")

    def _place_room(self, room: Room) -> None:
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
        try:
            return next(r for r in self.rooms if r.id == room_id)
        except StopIteration:
            raise ValueError(f"未找到房間 {room_id}")

    def expand_grid(self, new_width: int, new_height: int) -> None:
        if new_width > self.grid_width:
            for row in self.dungeon_tiles:
                row.extend(['W' for _ in range(new_width - self.grid_width)])
            self.grid_width = new_width
        if new_height > self.grid_height:
            self.dungeon_tiles.extend([['W' for _ in range(self.grid_width)] for _ in range(new_height - self.grid_height)])
            self.grid_height = new_height
        print(f"擴展網格到 ({self.grid_width}, {self.grid_height})")

    def get_tile_at(self, pos: Tuple[float, float]) -> str:
        tile_x = int(pos[0] // self.TILE_SIZE)
        tile_y = int(pos[1] // self.TILE_SIZE)
        if 0 <= tile_y < self.grid_height and 0 <= tile_x < self.grid_width:
            return self.dungeon_tiles[tile_y][tile_x]
        return 'W'