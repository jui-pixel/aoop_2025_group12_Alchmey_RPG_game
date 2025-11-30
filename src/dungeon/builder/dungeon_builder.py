# src/dungeon/builder/dungeon_builder.py
"""
地牢構建器模塊
協調所有組件生成完整地牢
"""
import math
from typing import List, Tuple
from ..config.dungeon_config import DungeonConfig
from ..algorithms.bsp_generator import BSPGenerator
from ..algorithms.graph_algorithms import GraphAlgorithms
from ..algorithms.pathfinding import AStarPathfinder
from ..generators.room_placer import RoomPlacer
from ..generators.room_type_assigner import RoomTypeAssigner
from ..generators.corridor_generator import CorridorGenerator
from ..generators.door_generator import DoorGenerator
from ..managers.tile_manager import TileManager
from ..room import Room, RoomType


class DungeonBuilder:
    """
    地牢構建器
    
    協調所有組件，按照正確的順序生成完整的地牢。
    這是地牢生成的主要入口點。
    """
    
    def __init__(self, config: DungeonConfig):
        """
        初始化地牢構建器
        
        Args:
            config: 地牢配置
        """
        self.config = config
        
        # 初始化所有組件
        self.bsp_generator = BSPGenerator(config)
        self.room_placer = RoomPlacer(config)
        self.room_type_assigner = RoomTypeAssigner(config)
        self.door_generator = DoorGenerator()
    
    def build(self) -> Tuple[List[Room], List[List[str]]]:
        """
        構建完整地牢
        
        Returns:
            (rooms, grid): 房間列表和瓦片網格
        """
        print("=" * 60)
        print("開始生成地牢...")
        print("=" * 60)
        
        # 1. 生成 BSP 樹
        print("\n[1/10] 生成 BSP 樹...")
        bsp_tree = self.bsp_generator.generate(
            self.config.grid_width,
            self.config.grid_height
        )
        depth = self.bsp_generator.get_tree_depth(bsp_tree)
        total_nodes, leaf_nodes = self.bsp_generator.get_node_count(bsp_tree)
        print(f"  ✓ BSP 樹深度: {depth}, 總節點: {total_nodes}, 葉節點: {leaf_nodes}")
        
        # 2. 在 BSP 樹中放置房間
        print("\n[2/10] 放置房間...")
        rooms = self.room_placer.place_rooms_in_bsp(bsp_tree)
        print(f"  ✓ 生成 {len(rooms)} 個房間")
        
        # 3. 分配房間類型
        print("\n[3/10] 分配房間類型...")
        self.room_type_assigner.assign_types(rooms)
        type_counts = self.room_type_assigner.get_room_type_counts(rooms)
        print(f"  ✓ 房間類型分布: {type_counts}")
        
        # 4. 構建房間圖
        print("\n[4/10] 構建房間連接圖...")
        edges = self._build_room_graph(rooms)
        print(f"  ✓ 生成 {len(edges)} 條可能的連接")
        
        # 5. 計算最小生成樹
        print("\n[5/10] 計算最小生成樹...")
        mst_edges = GraphAlgorithms.kruskal_mst(edges, len(rooms))
        print(f"  ✓ MST 包含 {len(mst_edges)} 條邊")
        
        # 6. 添加額外邊
        print("\n[6/10] 添加額外連接...")
        connections = GraphAlgorithms.add_extra_edges(
            mst_edges, edges, self.config.extra_bridge_ratio
        )
        print(f"  ✓ 總連接數: {len(connections)}")
        
        # 7. 初始化瓦片網格
        print("\n[7/10] 初始化瓦片網格...")
        tile_manager = TileManager(self.config.grid_width, self.config.grid_height)
        
        # 為每個房間生成瓦片
        for room in rooms:
            room.generate_tiles()
        
        # 放置房間到網格
        for room in rooms:
            tile_manager.place_room(room)
        print(f"  ✓ 網格尺寸: {self.config.grid_width}x{self.config.grid_height}")
        
        # 8. 生成走廊
        print("\n[8/10] 生成走廊...")
        pathfinder = AStarPathfinder(
            tile_manager.grid,
            passable_tiles=None,  # 允許在 Outside 上尋路
            cost_map=self.config.pathfinding_costs
        )
        corridor_gen = CorridorGenerator(self.config, pathfinder)
        corridor_gen.generate_corridors(rooms, connections, tile_manager.grid)
        
        # 膨脹走廊
        corridor_gen.expand_corridors(tile_manager.grid)
        corridor_count = tile_manager.count_tiles('Bridge_floor')
        print(f"  ✓ 走廊瓦片數: {corridor_count}")
        
        # 9. 添加房間邊界
        print("\n[9/10] 添加房間邊界...")
        tile_manager.add_room_borders(rooms)
        border_count = sum(
            tile_manager.count_tiles(f'Border_wall{suffix}')
            for suffix in ['', '_top', '_bottom', '_left', '_right',
                          '_top_left_corner', '_top_right_corner',
                          '_bottom_left_corner', '_bottom_right_corner']
        )
        print(f"  ✓ 邊界牆瓦片數: {border_count}")
        
        # 10. 生成門
        print("\n[10/10] 生成門...")
        self.door_generator.generate_doors(tile_manager.grid)
        door_count = self.door_generator.count_doors(tile_manager.grid)
        print(f"  ✓ 門數量: {door_count}")
        
        print("\n" + "=" * 60)
        print("地牢生成完成！")
        print("=" * 60)
        
        return rooms, tile_manager.grid
    
    def _build_room_graph(self, rooms: List[Room]) -> List[Tuple[int, int, float]]:
        """
        構建房間連接圖（完全圖）
        
        Args:
            rooms: 房間列表
        
        Returns:
            邊列表 [(room1_id, room2_id, weight), ...]
        """
        edges = []
        
        for i in range(len(rooms)):
            for j in range(i + 1, len(rooms)):
                # 計算兩個房間中心的距離
                distance = self._calculate_room_distance(rooms[i], rooms[j])
                edges.append((i, j, distance))
        
        return edges
    
    def generate_room(self, x: float, y: float, width: float, height: float, room_id: int, room_type: RoomType) -> Room:
        """
        創建並返回一個房間實例，它將自動生成房間瓦片。
        
        Args:
            x, y: 座標
            width, height: 尺寸
            room_id: 房間 ID
            room_type: 房間類型
        
        Returns:
            創建的房間
        """
        # Room 的 __post_init__ 會根據 room_type 自動調用 generate_tiles()
        room = Room(
            id=room_id,
            x=x,
            y=y,
            width=width,
            height=height,
            room_type=room_type
        )
        return room
    
    def _place_room(self, room: Room) -> None:
        """
        將房間放置到瓦片網格
        
        Args:
            room: 要放置的房間
            tile_manager: 瓦片管理器
        """
        if not hasattr(self, 'tile_manager'):
            self.tile_manager = TileManager(self.config.grid_width, self.config.grid_height)
        self.tile_manager.place_room(room)
    
    def _add_walls(self) -> None:
        """
        為所有房間添加邊界牆
        """
        if not hasattr(self, 'tile_manager'):
            self.tile_manager = TileManager(self.config.grid_width, self.config.grid_height)
        pass
    
    def adjust_wall(self) -> None:
        """
        調整牆壁以適應走廊和門
        """
        if not hasattr(self, 'tile_manager'):
            self.tile_manager = TileManager(self.config.grid_width, self.config.grid_height)
        # 這裡可以添加更多的牆壁調整邏輯
        pass
    
    def _calculate_room_distance(self, room1: Room, room2: Room) -> float:
        """
        計算兩個房間之間的距離（歐幾里得距離）
        
        Args:
            room1: 第一個房間
            room2: 第二個房間
        
        Returns:
            距離
        """
        cx1 = room1.x + room1.width / 2
        cy1 = room1.y + room1.height / 2
        cx2 = room2.x + room2.width / 2
        cy2 = room2.y + room2.height / 2
        
        return math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
    
    def get_statistics(self, rooms: List[Room], grid: List[List[str]]) -> dict:
        """
        獲取地牢統計信息
        
        Args:
            rooms: 房間列表
            grid: 瓦片網格
        
        Returns:
            統計信息字典
        """
        tile_manager = TileManager(len(grid[0]), len(grid))
        tile_manager.grid = grid
        
        return {
            'num_rooms': len(rooms),
            'room_types': self.room_type_assigner.get_room_type_counts(rooms),
            'corridor_tiles': tile_manager.count_tiles('Bridge_floor'),
            'door_count': tile_manager.count_tiles('Door'),
            'grid_size': (len(grid[0]), len(grid)),
        }
    
    def _initialize_grid(self) -> List[List[str]]:
        """
        初始化空的地牢網格
        
        Returns:
            初始化的瓦片網格
        """
        return [['Outside' for _ in range(self.config.grid_width)]
                for _ in range(self.config.grid_height)]
