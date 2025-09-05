# src/dungeon/dungeon.py
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set
from src.config import *
from src.dungeon.room import Room, RoomType
from src.dungeon.bridge import Bridge
from src.dungeon.BSPnode import BSPNode
import random
import heapq

"""
地牢生成與管理模組
====================

此檔案實作整個地牢的生成流程與資料結構，核心特色如下：

1) 使用 BSP（二元空間分割）切割整張地圖，於各葉節點嘗試放置房間。
2) 房間類型分配：先固定挑選 5 種（start, end, monster, reward, npc），
   剩餘房間再依 8:1:1 比例分配（monster:reward:npc）。
3) 將房間放上地圖後，於每個房間外圍加上一圈 Border_wall（不覆蓋房內地板）。
4) 節點建圖：對每個房間取「四角指向中心」的四個中點，
   並在水平或垂直軸隨機抖動 1 格，以這些點建立完全圖，邊權重為歐式距離。
5) 以克魯斯克爾演算法（Kruskal）求最小生成樹（MST），再隨機加回 10% 的邊。
6) 路徑鋪設：用 A* 演算法從邊的兩端點尋路。Outside 權重=1，其它=10。
   把沿途 Outside 覆蓋為 Bridge_floor。
7) 橋道擴張：對 Bridge_floor 進行一圈鄰接 Outside 的膨脹（變為 Bridge_floor）。
8) 門生成：將 Bridge_floor 鄰近一格的 Border_wall 改為 Door。

備註：
- 本檔案中的「瓦片」皆以字串標記，如 'Outside'、'Room_floor'、'Bridge_floor' 等。
- 地圖以二維陣列 self.dungeon_tiles[y][x] 儲存。
"""

# 地牢生成類，負責生成 BSP 地牢並管理房間與走廊
class Dungeon:
    ROOM_WIDTH = ROOM_WIDTH
    ROOM_HEIGHT = ROOM_HEIGHT
    GRID_WIDTH = GRID_WIDTH
    GRID_HEIGHT = GRID_HEIGHT
    MIN_ROOM_SIZE = MIN_ROOM_SIZE
    TILE_SIZE = TILE_SIZE
    ROOM_GAP = ROOM_GAP
    BIAS_RATIO = BIAS_RATIO
    BIAS_STRENGTH = BIAS_STRENGTH
    MIN_BRIDGE_WIDTH = MIN_BRIDGE_WIDTH
    MAX_BRIDGE_WIDTH = MAX_BRIDGE_WIDTH
    MAX_SPLIT_DEPTH = MAX_SPLIT_DEPTH
    EXTRA_BRIDGE_RATIO = EXTRA_BRIDGE_RATIO
    MOMSTER_ROOM_RATIO = MOMSTER_ROOM_RATIO
    TRAP_ROOM_RATIO = TRAP_ROOM_RATIO
    REWARD_ROOM_RATIO = REWARD_ROOM_RATIO
    LOBBY_WIDTH = LOBBY_WIDTH
    LOBBY_HEIGHT = LOBBY_HEIGHT
    game = None

    def __init__(self):
        """初始化地牢資料結構，不做實際地圖生成。"""
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
        """初始化地牢網格，建立填滿 'Outside' 的空白地圖。"""
        self.grid_width = self.GRID_WIDTH
        self.grid_height = self.GRID_HEIGHT
        self.dungeon_tiles = [['Outside' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        print(f"初始化地牢網格：寬度={self.grid_width}, 高度={self.grid_height}")

    def generate_room(self, x: float, y: float, width: float, height: float, room_id: int, room_type: RoomType = RoomType.EMPTY) -> Room:
        """生成單個房間物件（含內部地板瓦片），尚未放置到全域地圖。"""
        tiles = [['Room_floor' for _ in range(int(width))] for _ in range(int(height))]
        room = Room(id=room_id, x=x, y=y, width=width, height=height, tiles=tiles, room_type=room_type)
        print(f"生成房間 {room_id} 在 ({x}, {y}), 尺寸=({width}, {height}), 房間類型={room_type}")
        return room

    def _configure_end_room(self, tiles: List[List[str]], width: float, height: float) -> None:
        """（備用）配置終點房地板與傳送門，已整合至 Room 類內。"""
        for row in range(1, int(height) - 1):
            for col in range(1, int(width) - 1):
                tiles[row][col] = 'End_room_floor'
        center_x = int(width) // 2
        center_y = int(height) // 2
        tiles[center_y][center_x] = 'End_room_portal'

    def _split_bsp(self, node: BSPNode, depth: int, max_depth: int = MAX_SPLIT_DEPTH) -> None:
        """遞迴地以 BSP 分割地圖，當不可再分或達深度時，在節點嘗試造房。"""
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
        """判斷是否停止分割：已達深度上限或剩餘區域不足以再切兩半。"""
        return depth >= max_depth or (node.width < min_split_size * 2 and node.height < min_split_size * 2)

    def _try_generate_room(self, node: BSPNode, min_split_size: float) -> None:
        """在符合最小尺寸的葉節點中生成房間。"""
        if node.width >= min_split_size and node.height >= min_split_size:
            room_width, room_height, room_x, room_y = self._generate_room_bounds(
                (node.x, node.y, node.x + node.width, node.y + node.height)
            )
            node.room = self.generate_room(room_x, room_y, room_width, room_height, self.next_room_id)
            self.next_room_id += 1

    def _choose_split_direction(self, node: BSPNode, min_split_size: float) -> Optional[str]:
        """根據節點長寬判斷分割方向，權重偏向較長邊，以提升分割品質。"""
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
        """實際執行分割：垂直分割切 X；水平分割切 Y。"""
        if direction == "vertical":
            split_x = random.randint(min_split_size, int(node.width - min_split_size))
            node.left = BSPNode(node.x, node.y, split_x, node.height)
            node.right = BSPNode(node.x + split_x, node.y, node.width - split_x, node.height)
        else:
            split_y = random.randint(min_split_size, int(node.height - min_split_size))
            node.left = BSPNode(node.x, node.y, node.width, split_y)
            node.right = BSPNode(node.x, node.y + split_y, node.width, node.height - split_y)

    def _generate_room_bounds(self, partition: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """將房間配置在分區內，預留間距 ROOM_GAP，並限制於最大/最小尺寸。"""
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
        """中序遍歷 BSP 樹，蒐集所有葉節點上的房間。"""
        if node.room:
            rooms.append(node.room)
        if node.left:
            self._collect_rooms(node.left, rooms)
        if node.right:
            self._collect_rooms(node.right, rooms)

    def _check_bridge_room_collision(self, bridge: Bridge, room1: Room, room2: Room) -> bool:
        """（舊式橋接檢查）判定橋段是否穿過不相干房間。"""
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
        """（舊式）在兩房之間嘗試直線或 L 形橋接。"""
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
        """（舊式）生成直線或 L 形路徑，必要時忽略碰撞作為保底方案。"""
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
        """（舊式）L 形橋接，雙路徑嘗試，盡量避免與房間碰撞。"""
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
        """（舊式）以最近鄰策略生成連通走廊，並補充額外橋接。"""
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
        """（舊式）貪婪連線成骨幹路徑，近似連通。"""
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
        """（舊式）尋找遠距候選對，限制每房橋接數量後補幾條。"""
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
        """（輔助）找出與給定房間中心距離最近的另一房。"""
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
        """（舊式）直接把橋段覆蓋到地圖（以矩形區塊）為 Bridge_floor。"""
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
        """（舊式）對所有可通行瓦片邊緣加上 Border_wall。"""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] in PASSABLE_TILES:
                    if self._is_border_tile(x, y):
                        self.dungeon_tiles[y][x] = 'Border_wall'

    def _is_border_tile(self, x: int, y: int) -> bool:
        """（舊式）若周邊越界或接觸 Outside，則視為邊界需設牆。"""
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if y + dy < 0 or y + dy >= self.grid_height or x + dx < 0 or x + dx >= self.grid_width:
                    return True
                if self.dungeon_tiles[y + dy][x + dx] == 'Outside':
                    return True
        return False

    def _assign_room_types(self) -> None:
        """分配房間類型（依需求）
        1. 先選定 5 個房間：start, monster, reward, end, npc
        2. 剩餘房間依 8:1:1 分配為 monster:reward:npc
        """
        if not self.rooms:
            raise ValueError("無房間可分配類型")

        room_list = self.rooms[:]
        # 1) 選 start
        start_room = random.choice(room_list)
        self.current_room_id = start_room.id
        start_room.room_type = RoomType.START
        # 2) 選 end 為與 start 曼哈頓距離最遠
        start_center = (start_room.x + start_room.width / 2, start_room.y + start_room.height / 2)
        end_room = max(
            (r for r in room_list if r.id != start_room.id),
            key=lambda r: abs(r.x + r.width / 2 - start_center[0]) + abs(r.y + r.height / 2 - start_center[1])
        ) if len(room_list) > 1 else start_room
        end_room.room_type = RoomType.END
        # 3) 從剩餘挑一個 reward, 一個 npc, 一個 monster（確保至少各 1）
        remaining = [r for r in room_list if r.room_type == RoomType.EMPTY]
        random.shuffle(remaining)
        if remaining:
            remaining.pop(0).room_type = RoomType.REWARD
        if remaining:
            remaining.pop(0).room_type = RoomType.NPC
        if remaining:
            remaining.pop(0).room_type = RoomType.MONSTER

        # 4) 其餘依 8:1:1 分配（monster:reward:npc）。
        for r in remaining:
            r.room_type = random.choices(
                [RoomType.MONSTER, RoomType.REWARD, RoomType.NPC],
                weights=[8, 1, 1], k=1
            )[0]
    
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
        # 每個房間外圈加一圈 Border_wall（僅覆蓋 Outside，避免破壞房內地板）
        for room in self.rooms:
            self._add_room_border(room)
        # 建立節點與加權邊：節點為各房四個中點；邊權重為兩點距離
        nodes, edges = self._build_graph_nodes_edges()
        # Kruskal MST：用並查集合併成最小生成樹
        mst_edges = self._kruskal_mst(len(nodes), edges)
        # 加回 20% 的邊：隨機挑選非 MST 的候選邊
        final_edges = self._add_extra_edges(mst_edges, edges, ratio=0.01)
        # 以 A* 連線路徑：Outside 成本 1，其它 2；沿途把 Outside 貼成 Bridge_floor
        for u, v, _w in final_edges:
            sx, sy = nodes[u]
            gx, gy = nodes[v]
            path = self._astar_path((sx, sy), (gx, gy))
            self._paint_path(path)
        # 橋道膨脹：對 Bridge_floor 外圍一圈 Outside 也轉成 Bridge_floor
        self._dilate_bridges()
        # 開門：將鄰接 Bridge_floor 的 Border_wall 變成 Door
        self._convert_border_to_doors()
        # 對 PASSABLE_TILES 外圍一圈 Outside 轉成 Border_wall
        self._convert_outside_to_border_wall()
        print(f"初始化地牢：{len(self.rooms)} 個房間，{len(self.bridges)} 個橋接")

    def _place_rooms(self) -> None:
        """呼叫各房間內部配置，並把房間貼上地圖。"""
        for room in self.rooms:
            room._configure_tiles()
            self._place_room(room)

    def _place_room(self, room: Room) -> None:
        """把單一房間瓦片寫入全域地圖（必要時自動擴張地圖）。"""
        grid_x = int(room.x)
        grid_y = int(room.y)
        if (grid_x < 0 or grid_x + int(room.width) > self.grid_width or
                grid_y < 0 or grid_y + int(room.height) > self.grid_height):
            self.expand_grid(grid_x + int(room.width), grid_y + int(room.height))
        for row in range(int(room.height)):
            for col in range(int(room.width)):
                self.dungeon_tiles[grid_y + row][grid_x + col] = room.tiles[row][col]
        print(f"放置房間 {room.id} 在網格 ({grid_x}, {grid_y})")

    def _add_room_border(self, room: Room) -> None:
        """在房間外圍一圈設置 Border_wall（只覆蓋 Outside，不影響房內地板）。"""
        x0 = max(0, int(room.x) - 1)
        y0 = max(0, int(room.y) - 1)
        x1 = min(self.grid_width - 1, int(room.x + room.width))
        y1 = min(self.grid_height - 1, int(room.y + room.height))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                is_outer_ring = (
                    x == x0 or x == x1 or y == y0 or y == y1
                )
                if not is_outer_ring:
                    continue
                if self.dungeon_tiles[y][x] == 'Outside':
                    self.dungeon_tiles[y][x] = 'Border_wall'

    def _room_center(self, room: Room) -> Tuple[int, int]:
        """回傳房間中心（取整數瓦片座標）。"""
        cx = int(room.x + room.width // 2)
        cy = int(room.y + room.height // 2)
        return cx, cy

    def _compute_room_nodes(self, room: Room) -> List[Tuple[int, int]]:
        """取四角到中心的四個中點，加上單軸隨機位移 1 格（或 0），避免過度規整。"""
        cx, cy = self._room_center(room)
        corners = [
            (int(room.x), int(room.y)),
            (int(room.x + room.width - 1), int(room.y)),
            (int(room.x), int(room.y + room.height - 1)),
            (int(room.x + room.width - 1), int(room.y + room.height - 1)),
        ]
        mids = []
        for (px, py) in corners:
            mx = (px + cx) // 2
            my = (py + cy) // 2
            # 單軸抖動 1（含 0）
            if random.random() < 0.5:
                mx += random.choice([-1, 0, 1])
            else:
                my += random.choice([-1, 0, 1])
            mx = max(0, min(self.grid_width - 1, mx))
            my = max(0, min(self.grid_height - 1, my))
            mids.append((mx, my))
        return mids

    def _build_graph_nodes_edges(self) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int, float]]]:
        """建立所有節點（每房四個中點），並生成完全圖加權邊（歐式距離）。"""
        nodes: List[Tuple[int, int]] = []
        room_nodes: List[List[int]] = []
        for room in self.rooms:
            mids = self._compute_room_nodes(room)
            idxs = []
            for p in mids:
                idxs.append(len(nodes))
                nodes.append(p)
            room_nodes.append(idxs)
        edges: List[Tuple[int, int, float]] = []
        # 連線所有不同房間的節點對
        all_idxs = list(range(len(nodes)))
        for i in range(len(all_idxs)):
            x1, y1 = nodes[i]
            for j in range(i + 1, len(all_idxs)):
                x2, y2 = nodes[j]
                w = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                edges.append((i, j, w))
        return nodes, edges

    def _kruskal_mst(self, num_nodes: int, edges: List[Tuple[int, int, float]]) -> List[Tuple[int, int, float]]:
        """以 Kruskal 演算法計算最小生成樹。

        使用並查集（Union-Find）避免形成環，將邊依權重由小到大挑選。
        回傳的為 MST 邊集合（u, v, w）。
        """
        parent = list(range(num_nodes))
        rank = [0] * num_nodes

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> bool:
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            if rank[ra] < rank[rb]:
                parent[ra] = rb
            elif rank[ra] > rank[rb]:
                parent[rb] = ra
            else:
                parent[rb] = ra
                rank[ra] += 1
            return True

        mst: List[Tuple[int, int, float]] = []
        for u, v, w in sorted(edges, key=lambda e: e[2]):
            if union(u, v):
                mst.append((u, v, w))
                if len(mst) == num_nodes - 1:
                    break
        return mst

    def _add_extra_edges(self, mst: List[Tuple[int, int, float]], edges: List[Tuple[int, int, float]], ratio: float = 0.1) -> List[Tuple[int, int, float]]:
        """在 MST 基礎上隨機加入部分非 MST 邊，只連接附近不同房間的點。
        
        先找出每個房間的節點索引範圍，只考慮跨房間且距離較近的邊。
        避免選擇已經有連接的房間對，以及通過2條邊可到達的房間對。
        """
        mst_set = {(min(u, v), max(u, v)) for u, v, _ in mst}
        
        # 建立房間到節點索引的映射
        room_to_nodes = {}
        node_idx = 0
        for room in self.rooms:
            room_nodes = []
            for _ in range(4):  # 每個房間4個節點
                room_nodes.append(node_idx)
                node_idx += 1
            room_to_nodes[room.id] = room_nodes
        
        # 建立房間間的鄰接圖（基於MST）
        room_adjacency = {}
        for room in self.rooms:
            room_adjacency[room.id] = set()
        
        for u, v, _ in mst:
            u_room_id = None
            v_room_id = None
            for room_id, node_indices in room_to_nodes.items():
                if u in node_indices:
                    u_room_id = room_id
                if v in node_indices:
                    v_room_id = room_id
            if u_room_id is not None and v_room_id is not None and u_room_id != v_room_id:
                room_adjacency[u_room_id].add(v_room_id)
                room_adjacency[v_room_id].add(u_room_id)
        
        # 找出通過最多2條邊可到達的房間對
        reachable_in_2_hops = set()
        for room_id in room_adjacency:
            # 直接連接的房間
            for neighbor in room_adjacency[room_id]:
                reachable_in_2_hops.add(tuple(sorted([room_id, neighbor])))
            # 通過一個中間房間可到達的房間
            for neighbor in room_adjacency[room_id]:
                for second_neighbor in room_adjacency[neighbor]:
                    if second_neighbor != room_id:
                        reachable_in_2_hops.add(tuple(sorted([room_id, second_neighbor])))
        
        # 只考慮跨房間的邊，且距離較近的，且房間對通過2條邊無法到達
        max_distance = 50  # 最大連接距離閾值
        candidates = []
        for u, v, w in edges:
            if (min(u, v), max(u, v)) in mst_set:
                continue
            # 檢查是否為跨房間的邊
            u_room_id = None
            v_room_id = None
            for room_id, node_indices in room_to_nodes.items():
                if u in node_indices:
                    u_room_id = room_id
                if v in node_indices:
                    v_room_id = room_id
            
            # 如果是跨房間且距離在閾值內，且房間對通過2條邊無法到達
            if (u_room_id is not None and v_room_id is not None and 
                u_room_id != v_room_id and w <= max_distance and
                tuple(sorted([u_room_id, v_room_id])) not in reachable_in_2_hops):
                candidates.append((u, v, w))
        
        # 按距離排序，優先選擇較近的邊
        candidates.sort(key=lambda x: x[2])
        random.shuffle(candidates)
        extra_count = max(0, int(len(candidates) * ratio))
        return mst + candidates[:extra_count]

    def _tile_cost(self, x: int, y: int) -> float:
        """回傳 A* 用瓦片通行成本：Outside=1，其它=2，越界=∞。"""
        if x < 0 or y < 0 or x >= self.grid_width or y >= self.grid_height:
            return float('inf')
        t = self.dungeon_tiles[y][x]
        if t == 'Outside':
            return 1.0
        if t == 'Border_wall':
            return 2.0
        if t == 'Bridge_floor':
            return 0.0
        # 其他地形成本 2
        return 0.0

    def _astar_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """使用 A* 演算法在網格上尋路（4 向鄰接），返回點列路徑。

        - 啟發式：曼哈頓距離，以符合 4 向移動。
        - 成本：呼叫 _tile_cost，Outside=1，其它=2。
        - 若找不到路徑，回傳空陣列。
        """
        sx, sy = start
        gx, gy = goal
        if (sx, sy) == (gx, gy):
            return [start]
        open_set: List[Tuple[float, int, Tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, 0, (sx, sy)))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {(sx, sy): 0.0}
        visited: Set[Tuple[int, int]] = set()

        def heuristic(ax: int, ay: int) -> float:
            return abs(ax - gx) + abs(ay - gy)

        while open_set:
            _f, _ord, (x, y) = heapq.heappop(open_set)
            if (x, y) in visited:
                continue
            visited.add((x, y))
            if (x, y) == (gx, gy):
                # reconstruct
                path = [(x, y)]
                while (x, y) in came_from:
                    x, y = came_from[(x, y)]
                    path.append((x, y))
                path.reverse()
                return path
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy
                step = self._tile_cost(nx, ny)
                if step == float('inf'):
                    continue
                tentative = g_score[(x, y)] + step
                if tentative < g_score.get((nx, ny), float('inf')):
                    came_from[(nx, ny)] = (x, y)
                    g_score[(nx, ny)] = tentative
                    f = tentative + heuristic(nx, ny)
                    heapq.heappush(open_set, (f, len(came_from), (nx, ny)))
        return []

    def _paint_path(self, path: List[Tuple[int, int]]) -> None:
        """將路徑上的 Outside 覆蓋為 Bridge_floor，不改動非 Outside 瓦片。"""
        for (x, y) in path:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                if self.dungeon_tiles[y][x] == 'Outside':
                    self.dungeon_tiles[y][x] = 'Bridge_floor'

    def _dilate_bridges(self) -> None:
        """將 Bridge_floor 外圍一圈的 Outside 一併轉成 Bridge_floor（一次膨脹）。"""
        to_fill: List[Tuple[int, int]] = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] == 'Bridge_floor':
                    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                            if self.dungeon_tiles[ny][nx] == 'Outside':
                                to_fill.append((nx, ny))
        for x, y in to_fill:
            self.dungeon_tiles[y][x] = 'Bridge_floor'

    def _convert_border_to_doors(self) -> None:
        """將所有緊鄰 Bridge_floor 的 Border_wall 轉換為 Door。"""
        to_door: List[Tuple[int, int]] = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] == 'Border_wall':
                    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                            if self.dungeon_tiles[ny][nx] == 'Bridge_floor':
                                to_door.append((x, y))
                                break
        for x, y in to_door:
            self.dungeon_tiles[y][x] = 'Door'
    
    def _convert_outside_to_border_wall(self) -> None:
        """將所有緊鄰 PASSABLE_TILES 的 Outside 轉換為 Border_wall。"""
        to_outside: List[Tuple[int, int]] = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.dungeon_tiles[y][x] == 'Outside':
                    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                            if self.dungeon_tiles[ny][nx] in PASSABLE_TILES:
                                to_outside.append((x, y))
                                break
        for x, y in to_outside:
            self.dungeon_tiles[y][x] = 'Border_wall'

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