import pytest
from unittest.mock import patch
from src.dungeon.generators.room_type_assigner import RoomTypeAssigner
from src.dungeon.config.dungeon_config import DungeonConfig
from src.dungeon.room import Room, RoomType

# --- Fixtures ---

@pytest.fixture
def config():
    """建立具有固定比例的配置"""
    c = DungeonConfig()
    # 設定簡單的整數比例以便計算
    # 假設剩餘 10 個房間：5 個怪物，3 個陷阱，2 個獎勵
    c.monster_room_ratio = 0.5
    c.trap_room_ratio = 0.3
    return c

@pytest.fixture
def assigner(config):
    return RoomTypeAssigner(config)

def create_rooms(n, start_x=0, spacing=10):
    """輔助函式：建立一排房間"""
    rooms = []
    for i in range(n):
        # 簡單的一維排列，方便計算距離
        rooms.append(Room(i, start_x + i * spacing, 0, 10, 10))
    return rooms

# --- 測試案例 ---

def test_assign_types_empty_input(assigner):
    """測試空輸入不會崩潰"""
    assigner.assign_types([])
    assert True # 只要沒報錯就算通過

def test_insufficient_rooms_for_special(assigner):
    """測試房間少於 2 個時，不應該分配 Start/End"""
    rooms = create_rooms(1)
    assigner.assign_types(rooms)
    
    # 應該保持 EMPTY
    assert rooms[0].room_type == RoomType.EMPTY

def test_assign_start_and_end_farthest(assigner):
    """
    測試 Start 和 End 的分配邏輯
    重點：End 必須是距離 Start 最遠的房間
    """
    # 建立 3 個房間：A(0), B(10), C(100)
    # C 離 A 最遠
    room_a = Room(0, 0, 0, 10, 10)
    room_b = Room(1, 10, 0, 10, 10)
    room_c = Room(2, 100, 0, 10, 10)
    rooms = [room_a, room_b, room_c]
    
    # Mock random.choice 讓它固定選 room_a 作為 Start
    with patch('random.choice', return_value=room_a):
        assigner.assign_types(rooms)
        
    assert room_a.room_type == RoomType.START
    assert room_c.room_type == RoomType.END # C 是最遠的
    assert room_b.room_type == RoomType.REWARD # 剩餘的變成普通房間 (因數量少，全是 Reward)

def test_npc_room_assignment_threshold(assigner):
    """測試 NPC 房間生成的數量閾值"""
    # 邏輯：_assign_special_rooms 移除 Start/End 後
    # 剩餘 available >= 3 才會生成 NPC
    # 所以總數需要 >= 5 (Start + End + 3 others)
    
    # Case 1: 4 個房間 (不夠生成 NPC)
    rooms_4 = create_rooms(4)
    assigner.assign_types(rooms_4)
    counts_4 = assigner.get_room_type_counts(rooms_4)
    assert RoomType.NPC not in counts_4
    
    # Case 2: 5 個房間 (足夠生成 NPC)
    rooms_5 = create_rooms(5)
    assigner.assign_types(rooms_5)
    counts_5 = assigner.get_room_type_counts(rooms_5)
    assert counts_5.get(RoomType.NPC) == 1

def test_regular_room_ratios(assigner):
    """測試普通房間的比例分配準確性"""
    # 我們需要足夠的房間來測試比例
    # 總共 12 個房間
    # - 2 個 (Start/End)
    # - 10 個普通房間 (剩餘)
    # Config: Monster 0.5 (5個), Trap 0.3 (3個), Reward (2個)
    
    # 為了避免 NPC 干擾測試比例，我們 Mock 掉 NPC 生成邏輯
    # 或者簡單地提供剛好不觸發 NPC 的數量？不，NPC 是基於剩餘數量
    # 讓我們構造一個場景，先手動標記 Start/End，只測試 _assign_regular_rooms
    
    rooms = create_rooms(10) # 10 個全是 EMPTY 的房間
    
    # 直接調用內部方法測試比例
    assigner._assign_regular_rooms(rooms)
    
    counts = assigner.get_room_type_counts(rooms)
    
    assert counts[RoomType.MONSTER] == 5  # 10 * 0.5
    assert counts[RoomType.TRAP] == 3     # 10 * 0.3
    assert counts[RoomType.REWARD] == 2   # 剩餘

def test_select_farthest_room_logic(assigner):
    """單獨測試幾何距離計算邏輯"""
    ref_room = Room(0, 0, 0, 10, 10)
    
    close_room = Room(1, 10, 10, 10, 10)
    far_room = Room(2, 50, 50, 10, 10)
    medium_room = Room(3, 20, 20, 10, 10)
    
    candidates = [close_room, far_room, medium_room]
    
    result = assigner._select_farthest_room(ref_room, candidates)
    
    assert result == far_room

def test_integration_full_flow(assigner):
    """測試完整的分配流程 (Integration)"""
    # 建立 20 個房間
    rooms = create_rooms(20)
    
    assigner.assign_types(rooms)
    
    counts = assigner.get_room_type_counts(rooms)
    
    # 驗證必要類型存在
    assert counts[RoomType.START] == 1
    assert counts[RoomType.END] == 1
    # 20 個房間肯定夠生成 NPC
    assert counts[RoomType.NPC] == 1 
    
    # 驗證總數守恆
    total_assigned = sum(counts.values())
    assert total_assigned == 20
    
    # 驗證沒有殘留 EMPTY
    assert RoomType.EMPTY not in counts