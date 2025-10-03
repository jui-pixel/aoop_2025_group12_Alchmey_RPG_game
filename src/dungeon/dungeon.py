# src/dungeon/dungeon.py
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set
import pygame
import os
from src.config import *
from src.dungeon.room import Room, RoomType
from src.dungeon.bridge import Bridge
from src.dungeon.bsp_node import BSPNode
import random
import heapq

"""
地牢生成與管理模組
====================

此模組實作基於 BSP（二元空間分割）的完整地牢生成系統，包含以下核心功能：

【地牢生成流程】
1) BSP 空間分割：遞迴地將地圖空間分割成較小的區域，在葉節點生成房間
2) 房間類型分配：固定選擇 5 種特殊房間（start, end, monster, reward, npc），
   其餘房間按 8:1:1 比例分配為 monster:reward:npc
3) 房間邊界處理：為每個房間外圍添加一圈 Border_wall，避免房間直接相鄰
4) 圖形建構：為每個房間計算四個中點（四角到中心的連線中點），
   並加入隨機抖動，建立完全加權圖，邊權重為歐式距離
5) 最小生成樹：使用 Kruskal 演算法求 MST，確保所有房間連通
6) 額外連接：隨機添加少量額外邊，增加路徑多樣性但避免過度連接
7) 路徑生成：使用 A* 演算法在房間間尋路，Outside 成本=1，其他=2，
   沿途將 Outside 瓦片替換為 Bridge_floor
8) 橋道處理：對 Bridge_floor 進行膨脹，將鄰接的 Outside 也轉為 Bridge_floor
9) 門生成：將鄰接 Bridge_floor 的 Border_wall 轉換為 Door

【技術細節】
- 瓦片系統：使用字串標記不同瓦片類型（'Outside', 'Room_floor', 'Bridge_floor' 等）
- 地圖儲存：以二維陣列 self.dungeon_tiles[y][x] 儲存整個地牢
- 房間管理：每個房間包含位置、尺寸、瓦片數據和類型資訊
- 路徑演算法：A* 使用曼哈頓距離作為啟發式函數，適合 4 向移動

【設計理念】
- 確保連通性：透過 MST 保證所有房間都能到達
- 避免過度連接：限制額外邊的數量，保持地牢的探索性
- 自然路徑：使用 A* 生成符合直覺的走廊路徑
- 視覺完整性：透過邊界牆和門的處理，創造完整的地牢外觀
"""

def get_project_path(*subpaths):
    """Get absolute path to project root (roguelike_dungeon/) and join subpaths."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(project_root, *subpaths)

class Dungeon:
    """
    地牢生成與管理類
    
    此類負責整個地牢的生成、管理和維護，包含以下主要功能：
    - BSP 空間分割與房間生成
    - 房間類型分配與配置
    - 圖形建構與路徑生成
    - 地牢瓦片管理與渲染
    
    屬性說明：
    - ROOM_WIDTH/HEIGHT: 房間的最大寬度/高度（瓦片數）
    - GRID_WIDTH/HEIGHT: 地牢網格的總寬度/高度（瓦片數）
    - MIN_ROOM_SIZE: 房間的最小尺寸限制
    - TILE_SIZE: 每個瓦片的像素大小
    - ROOM_GAP: 房間間的最小間距
    - MAX_SPLIT_DEPTH: BSP 分割的最大深度
    - 其他比例常數用於房間類型分配和橋接生成
    """
    # 從配置檔案載入的常數
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
    game = None  # 遊戲實例引用，用於與遊戲系統整合

    def __init__(self):
        """
        初始化地牢資料結構
        
        建立地牢生成所需的所有資料結構，但不進行實際的地圖生成。
        實際生成需要呼叫 initialize_dungeon() 方法。
        
        實例變數說明：
        - rooms: 所有房間的列表，包含位置、尺寸、類型等資訊
        - bridges: 房間間橋接的列表（舊式系統，新式使用 A* 路徑）
        - current_room_id: 當前玩家所在房間的 ID
        - dungeon_tiles: 二維瓦片陣列，儲存整個地牢的瓦片類型
        - grid_width/height: 地牢網格的實際寬度/高度
        - next_room_id: 下一個房間的 ID 計數器
        - total_appeared_rooms: 總共出現的房間數量
        - bsp_tree: BSP 分割樹的根節點
        """
        self.rooms: List[Room] = []  # 房間列表
        self.bridges: List[Bridge] = []  # 橋接列表（舊式系統）
        self.current_room_id = 0  # 當前房間 ID
        self.dungeon_tiles: List[List[str]] = []  # 地牢瓦片陣列
        self.grid_width = 0  # 網格寬度
        self.grid_height = 0  # 網格高度
        self.next_room_id = 0  # 下一個房間 ID
        self.total_appeared_rooms = 0  # 總房間數
        self.bsp_tree: Optional[BSPNode] = None  # BSP 樹根節點
        self.tileset = self.load_tileset()  # 載入瓦片圖集

    def _initialize_grid(self) -> None:
        """
        初始化地牢網格
        
        建立一個填滿 'Outside' 瓦片的空白地圖網格。
        這是地牢生成的起始點，後續所有房間和路徑都會覆蓋在這個網格上。
        
        步驟：
        1. 設定網格尺寸為配置中定義的寬度和高度
        2. 建立二維陣列，所有位置都初始化為 'Outside'
        3. 輸出初始化資訊供除錯使用
        """
        self.grid_width = self.GRID_WIDTH
        self.grid_height = self.GRID_HEIGHT
        # 建立二維陣列，所有瓦片都設為 'Outside'
        self.dungeon_tiles = [['Outside' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        print(f"初始化地牢網格：寬度={self.grid_width}, 高度={self.grid_height}")

    def generate_room(self, x: float, y: float, width: float, height: float, room_id: int, room_type: RoomType = RoomType.EMPTY) -> Room:
        """
        生成單個房間物件
        
        建立一個房間物件，包含其內部瓦片數據，但尚未放置到全域地圖上。
        房間的實際瓦片配置會根據房間類型在 Room 類中處理。
        
        參數：
        - x, y: 房間左上角座標（瓦片單位）
        - width, height: 房間寬度和高度（瓦片單位）
        - room_id: 房間的唯一識別碼
        - room_type: 房間類型，預設為 EMPTY
        
        回傳：
        - Room 物件，包含位置、尺寸、瓦片數據和類型資訊
        """
        # 建立房間內部瓦片陣列，預設為 'Room_floor'
        tiles = [['Room_floor' for _ in range(int(width))] for _ in range(int(height))]
        # 建立房間物件
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
        """
        遞迴執行 BSP（二元空間分割）
        
        這是地牢生成的核心演算法，透過遞迴分割空間來創造房間。
        分割會持續進行直到達到最大深度或空間太小無法再分割。
        
        演算法流程：
        1. 計算最小分割尺寸（房間最小尺寸 + 間距）
        2. 檢查是否應該停止分割（深度限制或空間太小）
        3. 如果停止，嘗試在當前節點生成房間
        4. 如果繼續，選擇分割方向（水平或垂直）
        5. 執行分割，創建左右子節點
        6. 遞迴處理左右子節點
        
        參數：
        - node: 當前要處理的 BSP 節點
        - depth: 當前分割深度
        - max_depth: 最大分割深度限制
        """
        # 計算最小分割尺寸：房間最小尺寸 + 兩倍間距
        min_split_size = self.MIN_ROOM_SIZE + self.ROOM_GAP * 2
        
        # 檢查是否應該停止分割
        if self._should_stop_splitting(node, depth, max_depth, min_split_size):
            self._try_generate_room(node, min_split_size)
            return

        # 選擇分割方向
        split_direction = self._choose_split_direction(node, min_split_size)
        if not split_direction:
            # 無法分割，嘗試生成房間
            self._try_generate_room(node, min_split_size)
            return

        # 執行分割
        self._perform_split(node, split_direction, min_split_size)
        
        # 遞迴處理左右子節點
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
        """
        分配房間類型
        
        根據需求分配房間類型，確保地牢具有適當的挑戰性和多樣性。
        
        分配策略：
        1. 固定選擇 5 種特殊房間：
           - START: 玩家起始房間（隨機選擇）
           - END: 終點房間（距離起始房間最遠）
           - REWARD: 獎勵房間（隨機選擇一個）
           - NPC: NPC 房間（隨機選擇一個）
           - MONSTER: 怪物房間（隨機選擇一個）
        2. 剩餘房間按 8:1:1 比例分配：
           - 80% 為 MONSTER 房間（增加挑戰性）
           - 10% 為 REWARD 房間（提供獎勵）
           - 10% 為 NPC 房間（提供互動）
        
        異常：
        - ValueError: 如果沒有房間可分配
        """
        if not self.rooms:
            raise ValueError("無房間可分配類型")

        room_list = self.rooms[:]
        
        # 1) 隨機選擇起始房間
        start_room = random.choice(room_list)
        self.current_room_id = start_room.id
        start_room.room_type = RoomType.START
        
        # 2) 選擇終點房間（與起始房間曼哈頓距離最遠）
        start_center = (start_room.x + start_room.width / 2, start_room.y + start_room.height / 2)
        end_room = max(
            (r for r in room_list if r.id != start_room.id),
            key=lambda r: abs(r.x + r.width / 2 - start_center[0]) + abs(r.y + r.height / 2 - start_center[1])
        ) if len(room_list) > 1 else start_room
        end_room.room_type = RoomType.END
        
        # 3) 從剩餘房間中確保每種特殊類型至少有一個
        remaining = [r for r in room_list if r.room_type == RoomType.EMPTY]
        random.shuffle(remaining)
        
        # 確保至少有一個獎勵房間
        if remaining:
            remaining.pop(0).room_type = RoomType.REWARD
        # 確保至少有一個 NPC 房間
        if remaining:
            remaining.pop(0).room_type = RoomType.NPC
        # 確保至少有一個怪物房間
        if remaining:
            remaining.pop(0).room_type = RoomType.MONSTER

        # 4) 其餘房間按 8:1:1 比例分配（monster:reward:npc）
        for r in remaining:
            r.room_type = random.choices(
                [RoomType.MONSTER, RoomType.REWARD, RoomType.NPC],
                weights=[8, 1, 1], k=1
            )[0]
    
    def initialize_dungeon(self) -> None:
        """
        初始化整個地牢生成流程
        
        這是地牢生成的主要入口點，執行完整的 BSP 地牢生成流程。
        包含房間生成、類型分配、路徑連接和邊界處理等所有步驟。
        
        生成流程：
        1. 初始化空白網格
        2. 建立 BSP 樹並進行空間分割
        3. 收集所有生成的房間
        4. 分配房間類型（固定 5 種 + 8:1:1 分配）
        5. 將房間放置到地圖上
        6. 為每個房間添加邊界牆
        7. 建立房間間的圖形連接
        8. 使用 Kruskal 演算法求最小生成樹
        9. 添加少量額外連接
        10. 使用 A* 演算法生成路徑
        11. 處理橋道膨脹和門生成
        12. 完成邊界牆處理
        
        異常：
        - ValueError: 如果未生成任何房間
        """
        # 步驟 1: 初始化空白網格
        self._initialize_grid()
        
        # 步驟 2: 建立 BSP 樹並進行空間分割
        self.bsp_tree = BSPNode(0, 0, self.grid_width, self.grid_height)
        self._split_bsp(self.bsp_tree, 0)
        
        # 步驟 3: 收集所有生成的房間
        self.rooms = []
        self.bridges = []
        self.next_room_id = 0
        self._collect_rooms(self.bsp_tree, self.rooms)
        self.total_appeared_rooms = len(self.rooms)
        if not self.rooms:
            raise ValueError("未生成任何房間")

        # 步驟 4: 分配房間類型
        self._assign_room_types()

        # 步驟 5: 將房間放置到地圖上
        self._place_rooms()
        
        # 步驟 6: 為每個房間添加邊界牆（僅覆蓋 Outside，避免破壞房內地板）
        for room in self.rooms:
            self._add_room_border(room)
            
        # 步驟 7: 建立節點與加權邊（節點為各房四個中點；邊權重為兩點距離）
        nodes, edges = self._build_graph_nodes_edges()
        
        # 步驟 8: Kruskal MST（用並查集合併成最小生成樹）
        mst_edges = self._kruskal_mst(len(nodes), edges)
        
        # 步驟 9: 加回 1% 的邊（只連接附近且未連接的房間）
        final_edges = self._add_extra_edges(mst_edges, edges, ratio=0.01)
        
        # 步驟 10: A* 路徑生成（Outside=1，其他=2，沿途鋪設 Bridge_floor）
        for u, v, _w in final_edges:
            sx, sy = nodes[u]
            gx, gy = nodes[v]
            path = self._astar_path((sx, sy), (gx, gy))
            self._paint_path(path)
            
        # 步驟 11: 橋道膨脹（Bridge_floor 外圍一圈 Outside 轉為 Bridge_floor）
        self._dilate_bridges()
        
        # 步驟 12: 開門（鄰接 Bridge_floor 的 Border_wall 變為 Door）
        self._convert_border_to_doors()
        
        # 步驟 13: 邊界牆（鄰接可通行區域的 Outside 轉為 Border_wall）
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
        """
        使用 Kruskal 演算法計算最小生成樹
        
        這是確保地牢連通性的核心演算法。最小生成樹保證所有房間都能到達，
        同時使用最少的連接邊，避免過度連接。
        
        演算法原理：
        1. 將所有邊按權重（距離）由小到大排序
        2. 依序檢查每條邊，如果不會形成環就加入 MST
        3. 使用並查集（Union-Find）高效檢測環
        4. 當 MST 包含 n-1 條邊時停止（n 為節點數）
        
        並查集優化：
        - 路徑壓縮：在查找時將節點直接連到根節點
        - 按秩合併：總是將較小的樹合併到較大的樹下
        
        參數：
        - num_nodes: 節點總數
        - edges: 邊列表，格式為 (u, v, weight)
        
        回傳：
        - MST 邊列表，格式為 (u, v, weight)
        
        時間複雜度：O(E log E)，其中 E 為邊數
        空間複雜度：O(V)，其中 V 為節點數
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
        """
        使用 A* 演算法在網格上尋路
        
        這是地牢路徑生成的核心演算法，用於在房間間建立走廊連接。
        A* 演算法結合了最佳優先搜尋和 Dijkstra 演算法的優點，
        能夠在保證最短路徑的同時提高搜尋效率。
        
        演算法特點：
        - 啟發式函數：使用曼哈頓距離，適合 4 向移動
        - 成本函數：Outside=1，其他地形=2，越界=∞
        - 搜尋策略：優先探索最有希望的路徑
        - 路徑重建：從目標節點回溯到起始節點
        
        參數：
        - start: 起始座標 (x, y)
        - goal: 目標座標 (x, y)
        
        回傳：
        - 路徑點列表，從起始點到目標點
        - 空列表表示找不到路徑
        
        實作細節：
        1. 使用優先佇列管理待探索節點
        2. 維護 g_score（實際成本）和 f_score（總成本）
        3. 使用 came_from 字典重建路徑
        4. 避免重複探索已訪問的節點
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
    
    def load_tileset(self) -> dict:
        """Load tileset images from src/assets/processed/ and map to tile types."""
        tileset = {}
        tileset_dir = get_project_path("src", "assets", "processed")
        
        # Map tile types to image filenames
        tile_mapping = {
            "floor": "floor_0_0.png",  # Example: floor tile
            "wall": "wall_0_0.png",    # Example: wall tile
            # Add more mappings as needed (e.g., "door": "door_0_0.png")
        }

        for tile_type, filename in tile_mapping.items():
            file_path = os.path.join(tileset_dir, filename)
            try:
                image = pygame.image.load(file_path).convert_alpha()
                # Scale image to TILE_SIZE if needed
                if image.get_width() != TILE_SIZE or image.get_height() != TILE_SIZE:
                    image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                tileset[tile_type] = image
            except pygame.error as e:
                print(f"無法載入圖塊 {file_path}: {e}")
                # Create a fallback colored surface
                fallback = pygame.Surface((TILE_SIZE, TILE_SIZE))
                fallback.fill(GRAY if tile_type in PASSABLE_TILES else DARK_GRAY)
                tileset[tile_type] = fallback

        return tileset
    
    def draw_background(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """
        Draw the dungeon background tiles using tileset images, including camera view + 2 tiles outside.
        """
        offset_x, offset_y = camera_offset
        tile_size = TILE_SIZE

        # Calculate tile range: camera view + 2 tiles outside
        start_tile_x = max(0, int((offset_x - 2 * tile_size) / tile_size))
        end_tile_x = min(self.grid_width, int((offset_x + SCREEN_WIDTH + 2 * tile_size) / tile_size))
        start_tile_y = max(0, int((offset_y - 2 * tile_size) / tile_size))
        end_tile_y = min(self.grid_height, int((offset_y + SCREEN_HEIGHT + 2 * tile_size) / tile_size))

        # Draw background tiles
        for tile_y in range(start_tile_y, end_tile_y):
            for tile_x in range(start_tile_x, end_tile_x):
                tile_type = self.dungeon_tiles[tile_y][tile_x]
                tile_image = self.tileset.get(tile_type, None)
                screen_x = tile_x * tile_size - offset_x
                screen_y = tile_y * tile_size - offset_y

                if tile_image:
                    screen.blit(tile_image, (screen_x, screen_y))
                else:
                    # Fallback to colored rectangle if tile image is missing
                    color = GRAY if tile_type in PASSABLE_TILES else DARK_GRAY
                    pygame.draw.rect(screen, color, (screen_x, screen_y, tile_size, tile_size))

    def draw_foreground(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """
        Draw the dungeon foreground walls using tileset images as half-height rectangles
        to create a 2.5D effect on wall positions.
        """
        offset_x, offset_y = camera_offset
        tile_size = TILE_SIZE
        half_tile = tile_size * 0.5

        # Same tile range as background
        start_tile_x = max(0, int((offset_x - 2 * tile_size) / tile_size))
        end_tile_x = min(self.grid_width, int((offset_x + SCREEN_WIDTH + 2 * tile_size) / tile_size))
        start_tile_y = max(0, int((offset_y - 2 * tile_size) / tile_size))
        end_tile_y = min(self.grid_height, int((offset_y + SCREEN_HEIGHT + 2 * tile_size) / tile_size))

        # Draw walls as half-height tiles at the bottom of non-passable tiles
        for tile_y in range(start_tile_y, end_tile_y):
            for tile_x in range(start_tile_x, end_tile_x):
                tile_type = self.dungeon_tiles[tile_y][tile_x]
                if tile_type not in PASSABLE_TILES:  # Wall or non-passable
                    tile_image = self.tileset.get(tile_type, None)
                    screen_x = tile_x * tile_size - offset_x
                    screen_y = (tile_y * tile_size - offset_y) + half_tile  # Bottom half for 2.5D effect

                    if tile_image:
                        # Scale wall tile to half-height for 2.5D effect
                        wall_image = pygame.transform.scale(tile_image, (tile_size, int(half_tile)))
                        screen.blit(wall_image, (screen_x, screen_y))
                    else:
                        # Fallback to colored rectangle
                        wall_color = DARK_GRAY
                        pygame.draw.rect(screen, wall_color, (screen_x, screen_y, tile_size, half_tile))