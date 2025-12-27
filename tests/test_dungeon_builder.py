import pytest
import math
from src.dungeon.builder.dungeon_builder import DungeonBuilder
from src.dungeon.config.dungeon_config import DungeonConfig
from src.dungeon.room import Room, RoomType

# --- Fixtures ---

@pytest.fixture
def small_config():
    """
    創建一個較小的地牢配置，並初始化空的 special_rooms 結構
    """
    config = DungeonConfig()
    config.grid_width = 40
    config.grid_height = 40
    config.min_room_size = 5
    config.max_room_size = 10
    config.bsp_depth = 3
    
    # [修正] 初始化默認結構，避免 KeyError
    config.special_rooms = {
        "boss_room": {"enabled": False, "boss_id": "none", "room_size": (10, 10)},
        "final_room": {"enabled": False, "npc_id": "none", "room_size": (10, 10)}
    }
    return config

@pytest.fixture
def boss_only_config():
    """配置僅生成 Boss 房間的模式"""
    config = DungeonConfig()
    config.grid_width = 30
    config.grid_height = 30
    config.monster_room_ratio = 0.0  # 設置為 0 以觸發 special-only 邏輯
    
    # [修正] 完整定義字典結構，使用 Tuple 作為 size
    config.special_rooms = {
        "boss_room": {
            "enabled": True, 
            "boss_id": "boss_01", 
            "room_size": (10, 10)  # Tuple[int, int]
        },
        "final_room": {
            "enabled": False, 
            "npc_id": "none", 
            "room_size": (10, 10)
        }
    }
    return config

# --- 測試案例 ---

def test_build_standard_flow(small_config):
    """測試標準地牢生成流程 (Happy Path)"""
    builder = DungeonBuilder(small_config)
    rooms, grid = builder.build()
    
    # 驗證基本輸出
    assert isinstance(rooms, list)
    assert len(grid) == small_config.grid_height
    assert len(rooms) > 0
    # 確保包含 START 房間
    assert any(r.room_type == RoomType.START for r in rooms)

def test_boss_only_mode(boss_only_config):
    """
    測試特殊的 'Boss Room Only' 模式
    """
    builder = DungeonBuilder(boss_only_config)
    rooms, grid = builder.build()
    
    # 應該只有 1 個房間
    assert len(rooms) == 1
    room = rooms[0]
    
    # 類型必須被轉換為 BOSS
    assert room.room_type == RoomType.BOSS
    
    # 尺寸驗證 (Tuple (10, 10))
    assert room.width == 10
    assert room.height == 10
    
    # 位置驗證 (確保在中心附近)
    center_x = boss_only_config.grid_width // 2
    room_center = room.x + room.width // 2
    assert abs(room_center - center_x) < 5

def test_apply_special_rooms_logic(small_config):
    """測試將 END 房間轉換為 FINAL 房間的邏輯"""
    # [修正] 修改已初始化的字典，而不是假設鍵存在
    small_config.special_rooms["final_room"]["enabled"] = True
    small_config.special_rooms["final_room"]["npc_id"] = "npc_guide"
    
    # 確保 Boss 房是關閉的
    small_config.special_rooms["boss_room"]["enabled"] = False
    
    builder = DungeonBuilder(small_config)
    rooms, grid = builder.build()
    
    # 檢查是否存在 FINAL 類型的房間
    # 注意：build() 內部會自動調用 _apply_special_rooms
    has_final = any(r.room_type == RoomType.FINAL for r in rooms)
    assert has_final is True

def test_room_graph_construction(small_config):
    """測試房間連接圖的距離計算"""
    builder = DungeonBuilder(small_config)
    
    # 手動創建兩個房間進行距離測試
    room1 = Room(1, 0, 0, 10, 10, RoomType.NORMAL) # Center (5, 5)
    room2 = Room(2, 10, 0, 10, 10, RoomType.NORMAL) # Center (15, 5)
    
    rooms = [room1, room2]
    
    # 調用私有方法構建圖
    edges = builder._build_room_graph(rooms)
    
    # 驗證邊與距離
    assert len(edges) == 1
    edge = edges[0]
    # edge 格式: (index1, index2, weight)
    assert edge[0] == 0
    assert edge[1] == 1
    assert edge[2] == 10.0

def test_statistics_generation(small_config):
    """測試統計信息生成"""
    builder = DungeonBuilder(small_config)
    rooms, grid = builder.build()
    
    stats = builder.get_statistics(rooms, grid)
    
    assert 'num_rooms' in stats
    assert stats['num_rooms'] == len(rooms)
    assert 'grid_size' in stats