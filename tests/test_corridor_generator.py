import pytest
from unittest.mock import MagicMock
from src.dungeon.generators.corridor_generator import CorridorGenerator
from src.dungeon.config.dungeon_config import DungeonConfig
from src.dungeon.room import Room, RoomType
from src.dungeon.algorithms.pathfinding import AStarPathfinder

# --- Fixtures ---

@pytest.fixture
def mock_pathfinder():
    """創建一個模擬的尋路器"""
    pathfinder = MagicMock(spec=AStarPathfinder)
    return pathfinder

@pytest.fixture
def basic_config():
    config = DungeonConfig()
    config.grid_width = 20
    config.grid_height = 20
    return config

@pytest.fixture
def empty_grid():
    """創建一個 20x20 的全 Outside 網格"""
    return [['Outside' for _ in range(20)] for _ in range(20)]

@pytest.fixture
def generator(basic_config, mock_pathfinder):
    return CorridorGenerator(basic_config, mock_pathfinder)

# --- 測試案例 ---

def test_get_room_edge_point_horizontal(generator):
    """測試水平方向的邊緣點計算 (左 -> 右)"""
    # Room 1 在左 (0,0) 到 (10,10), 中心 (5,5)
    room1 = Room(1, 0, 0, 10, 10, RoomType.NORMAL)
    # Room 2 在右 (20,0) 到 (30,10), 中心 (25,5)
    room2 = Room(2, 20, 0, 10, 10, RoomType.NORMAL)
    
    # 計算從 Room 1 出發去 Room 2 的點
    x, y = generator._get_room_edge_point(room1, room2)
    
    # 預期：應該選擇 Room 1 的右側邊緣
    # 邏輯是: room.x + room.width - 2 => 0 + 10 - 2 = 8
    assert x == 8
    assert y == 5 # y 應該是中心點

def test_get_room_edge_point_vertical(generator):
    """測試垂直方向的邊緣點計算 (上 -> 下)"""
    # Room 1 在上 (0,0) 到 (10,10), 中心 (5,5)
    room1 = Room(1, 0, 0, 10, 10, RoomType.NORMAL)
    # Room 2 在下 (0,20) 到 (10,30), 中心 (5,25)
    room2 = Room(2, 0, 20, 10, 10, RoomType.NORMAL)
    
    # 計算從 Room 1 出發去 Room 2 的點
    x, y = generator._get_room_edge_point(room1, room2)
    
    # 預期：應該選擇 Room 1 的下側邊緣
    # 邏輯是: room.y + room.height - 2 => 0 + 10 - 2 = 8
    assert x == 5 # x 應該是中心點
    assert y == 8

def test_apply_path_to_grid(generator, empty_grid):
    """測試路徑應用到網格的邏輯"""
    # 模擬一條路徑：(5,5) -> (5,6) -> (5,7)
    path = [(5, 5), (5, 6), (5, 7)]
    
    # 預先設置一個障礙物 (比如牆壁)，測試是否會避開覆蓋它
    empty_grid[6][5] = 'Wall' 
    
    generator._apply_path_to_grid(path, empty_grid)
    
    # 檢查路徑點是否變成 Bridge_floor
    assert empty_grid[5][5] == 'Bridge_floor'
    assert empty_grid[7][5] == 'Bridge_floor'
    
    # 關鍵：Wall 不應該被覆蓋 (根據代碼邏輯: if grid[y][x] == 'Outside')
    # 如果你的設計是走廊可以穿牆，這裡需要反過來斷言。
    # 但目前的代碼顯示只覆蓋 'Outside'
    assert empty_grid[6][5] == 'Wall'

def test_generate_corridors_integration(generator, mock_pathfinder, empty_grid):
    """測試生成走廊的主流程"""
    room1 = Room(1, 0, 0, 10, 10, RoomType.NORMAL)
    room2 = Room(2, 20, 0, 10, 10, RoomType.NORMAL)
    rooms = [room1, room2]
    connections = [(0, 1)] # Room 0 連接 Room 1
    
    # 設定 Mock 行為：當調用 find_path 時返回一條假路徑
    mock_path = [(8, 5), (9, 5), (10, 5)]
    mock_pathfinder.find_path.return_value = mock_path
    
    generator.generate_corridors(rooms, connections, empty_grid)
    
    # 驗證 find_path 是否被正確調用
    # 我們不關心具體的 start/end 參數 (已經在 _get_room_edge_point 測過了)
    mock_pathfinder.find_path.assert_called_once()
    
    # 驗證網格是否被更新
    assert empty_grid[5][8] == 'Bridge_floor'
    assert empty_grid[5][9] == 'Bridge_floor'
    assert empty_grid[5][10] == 'Bridge_floor'

def test_expand_corridors(generator, empty_grid):
    """測試走廊膨脹功能"""
    # 在網格中心設置一個單點走廊
    empty_grid[10][10] = 'Bridge_floor'
    
    generator.expand_corridors(empty_grid)
    
    # 驗證中心點保持不變
    assert empty_grid[10][10] == 'Bridge_floor'
    
    # 驗證四周是否變成 Bridge_floor (膨脹)
    assert empty_grid[10][11] == 'Bridge_floor' # 右
    assert empty_grid[10][9] == 'Bridge_floor'  # 左
    assert empty_grid[11][10] == 'Bridge_floor' # 下
    assert empty_grid[9][10] == 'Bridge_floor'  # 上
    
    # 驗證更遠的地方沒有受影響
    assert empty_grid[8][10] == 'Outside'

def test_no_path_found_warning(generator, mock_pathfinder, empty_grid, capsys):
    """測試當無法找到路徑時的處理"""
    room1 = Room(1, 0, 0, 10, 10, RoomType.NORMAL)
    room2 = Room(2, 20, 0, 10, 10, RoomType.NORMAL)
    
    # Mock 返回 None 或 空列表
    mock_pathfinder.find_path.return_value = None
    
    generator._create_corridor(room1, room2, empty_grid)
    
    # 驗證是否有打印警告
    captured = capsys.readouterr()
    assert "Warning: Could not find path" in captured.out
    
    # 驗證網格沒有被修改 (應該全是 Outside)
    assert empty_grid[5][5] == 'Outside'