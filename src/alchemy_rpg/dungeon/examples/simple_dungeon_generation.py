# src/dungeon/examples/simple_dungeon_generation.py
"""
簡單的地牢生成示例
展示如何使用新的模塊化系統生成地牢
"""
from ..config import DungeonConfig, DEFAULT_CONFIG, SMALL_DUNGEON_CONFIG
from ..builder import DungeonBuilder


def generate_default_dungeon():
    """使用默認配置生成地牢"""
    print("使用默認配置生成地牢...")
    
    # 創建配置
    config = DEFAULT_CONFIG
    
    # 驗證配置
    is_valid, error = config.validate()
    if not is_valid:
        print(f"配置無效: {error}")
        return None, None
    
    # 創建構建器並生成地牢
    builder = DungeonBuilder(config)
    rooms, grid = builder.build()
    
    # 獲取統計信息
    stats = builder.get_statistics(rooms, grid)
    print(f"\n統計信息: {stats}")
    
    return rooms, grid


def generate_small_dungeon():
    """使用小型配置生成地牢"""
    print("使用小型配置生成地牢...")
    
    config = SMALL_DUNGEON_CONFIG
    builder = DungeonBuilder(config)
    rooms, grid = builder.build()
    
    return rooms, grid


def generate_custom_dungeon():
    """使用自定義配置生成地牢"""
    print("使用自定義配置生成地牢...")
    
    # 創建自定義配置
    config = DungeonConfig(
        grid_width=80,
        grid_height=60,
        max_split_depth=5,
        extra_bridge_ratio=0.2,  # 增加連通性
        monster_room_ratio=0.7,
        reward_room_ratio=0.2,
        trap_room_ratio=0.1,
    )
    
    # 驗證配置
    is_valid, error = config.validate()
    if not is_valid:
        print(f"配置無效: {error}")
        return None, None
    
    builder = DungeonBuilder(config)
    rooms, grid = builder.build()
    
    return rooms, grid


def test_individual_components():
    """測試單個組件"""
    from ..algorithms import BSPGenerator, GraphAlgorithms, AStarPathfinder
    from ..generators import RoomPlacer, RoomTypeAssigner
    
    print("\n測試單個組件...")
    
    # 測試 BSP 生成器
    print("\n1. 測試 BSP 生成器")
    config = SMALL_DUNGEON_CONFIG
    bsp_gen = BSPGenerator(config)
    tree = bsp_gen.generate(50, 50)
    depth = bsp_gen.get_tree_depth(tree)
    total, leaves = bsp_gen.get_node_count(tree)
    print(f"  BSP 深度: {depth}, 總節點: {total}, 葉節點: {leaves}")
    
    # 測試房間放置器
    print("\n2. 測試房間放置器")
    placer = RoomPlacer(config)
    rooms = placer.place_rooms_in_bsp(tree)
    print(f"  生成房間數: {len(rooms)}")
    
    # 測試房間類型分配器
    print("\n3. 測試房間類型分配器")
    assigner = RoomTypeAssigner(config)
    assigner.assign_types(rooms)
    counts = assigner.get_room_type_counts(rooms)
    print(f"  房間類型: {counts}")
    
    # 測試圖算法
    print("\n4. 測試圖算法")
    edges = [(0, 1, 1.0), (1, 2, 2.0), (0, 2, 3.0), (2, 3, 1.5)]
    mst = GraphAlgorithms.kruskal_mst(edges, 4)
    print(f"  MST 邊: {mst}")
    is_connected = GraphAlgorithms.is_connected(mst, 4)
    print(f"  圖是否連通: {is_connected}")


if __name__ == "__main__":
    # 生成默認地牢
    rooms, grid = generate_default_dungeon()
    
    # 測試單個組件
    test_individual_components()
