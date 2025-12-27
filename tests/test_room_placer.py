import pytest
from unittest.mock import MagicMock, patch
from src.dungeon.generators.room_placer import RoomPlacer
from src.dungeon.config.dungeon_config import DungeonConfig
from src.dungeon.bsp_node import BSPNode
from src.dungeon.room import Room

# --- Fixtures ---

@pytest.fixture
def placer_config():
    """建立測試用的配置"""
    config = DungeonConfig()
    config.room_gap = 2
    config.min_room_size = 5
    # 設定目標房間大小（這在 RoomPlacer 中充當最大限制）
    config.room_width = 10 
    config.room_height = 10
    return config

@pytest.fixture
def placer(placer_config):
    return RoomPlacer(placer_config)

@pytest.fixture
def leaf_node():
    """建立一個標準的葉節點 (20x20)"""
    return BSPNode(0, 0, 20, 20)

# --- Helper ---
def create_split_node():
    """建立一個簡單的樹結構：Root -> [Left, Right]"""
    root = BSPNode(0, 0, 40, 20)
    left = BSPNode(0, 0, 20, 20)
    right = BSPNode(20, 0, 20, 20)
    root.left = left
    root.right = right
    return root

# --- 測試案例 ---

def test_place_rooms_in_leaf_only(placer):
    """測試房間只會生成在葉節點，而不是中間節點"""
    root = create_split_node()
    
    rooms = placer.place_rooms_in_bsp(root)
    
    # 預期：生成 2 個房間 (Left 和 Right)
    assert len(rooms) == 2
    
    # Root 不應該有房間
    assert root.room is None
    
    # 葉節點應該有房間
    assert root.left.room is not None
    assert root.right.room is not None
    
    # 檢查房間 ID 是否遞增
    assert rooms[0].id == 0
    assert rooms[1].id == 1

def test_room_too_small_to_place(placer, placer_config):
    """測試當節點太小（考慮 gap 後）時，不應該生成房間"""
    # Gap = 2, Min = 5. 需要最小空間: 2+2+5 = 9
    # 建立一個 8x8 的節點
    small_node = BSPNode(0, 0, 8, 8)
    
    rooms = placer.place_rooms_in_bsp(small_node)
    
    assert len(rooms) == 0
    assert small_node.room is None



def test_calculate_room_bounds(placer, placer_config):
    """測試房間邊界計算邏輯 (Gap 和 Size 限制)"""
    # 節點: (x=10, y=10, w=30, h=30)
    # Config: gap=2, room_width=10 (max preferred)
    node = BSPNode(10, 10, 30, 30)
    
    x, y, w, h = placer._calculate_room_bounds(node)
    
    # 1. 檢查起始位置 (x + gap)
    assert x == 10 + 2
    assert y == 10 + 2
    
    # 2. 檢查寬高
    # 可用空間 = 30 - 2*2 = 26
    # Config.room_width = 10
    # min(26, 10) = 10
    assert w == 10
    assert h == 10

def test_calculate_room_bounds_clamped_by_node(placer, placer_config):
    """測試當節點比配置的目標尺寸小時，房間應該被縮小以適應節點"""
    # Config: target size = 10
    # Node: size = 10 (可用空間 = 10 - 4 = 6)
    node = BSPNode(0, 0, 10, 10)
    
    x, y, w, h = placer._calculate_room_bounds(node)
    
    # 預期寬度被限制在可用空間 (6)
    assert w == 6
    assert h == 6

def test_get_room_connection_point(placer):
    """測試連接點是否在房間內部的安全區域"""
    room = Room(1, 10, 10, 20, 20) # (10,10) -> (30,30)
    
    # 測試多次以覆蓋隨機性
    for _ in range(20):
        cx, cy = placer.get_room_connection_point(room)
        
        # 邏輯: x + 2 <= cx <= x + w - 3
        # 範圍: 12 <= cx <= 27
        assert 12 <= cx <= 27
        assert 12 <= cy <= 27

def test_get_room_midpoints(placer):
    """測試獲取房間四個中點的邏輯"""
    room = Room(1, 0, 0, 20, 20)
    # Center = (10, 10)
    
    points = placer.get_room_midpoints(room, jitter=0)
    
    assert len(points) == 4
    
    # 預期點位 (無抖動)
    expected_points = {
        (5.0, 10.0),  # 左中
        (15.0, 10.0), # 右中
        (10.0, 5.0),  # 上中
        (10.0, 15.0)  # 下中
    }
    
    assert set(points) == expected_points

def test_get_room_midpoints_with_jitter(placer):
    """測試抖動參數是否生效"""
    room = Room(1, 0, 0, 20, 20)
    jitter = 1.0
    
    points = placer.get_room_midpoints(room, jitter=jitter)
    
    # 檢查點是否稍微偏離了標準位置
    # 例如左中標準是 (5, 10)，現在應該在 4~6 和 9~11 之間
    p_left = points[0]
    assert 4.0 <= p_left[0] <= 6.0
    assert 9.0 <= p_left[1] <= 11.0