import pytest
from unittest.mock import MagicMock, patch
import pygame
from src.dungeon.dungeon import Dungeon
from src.dungeon.config.dungeon_config import DungeonConfig, RoomType

# --- Fixtures ---

@pytest.fixture
def mock_config():
    """建立一個小型的配置，加快測試生成速度"""
    config = DungeonConfig()
    config.grid_width = 40
    config.grid_height = 40
    config.tile_size = 32 # 設定固定像素大小以便計算
    return config

@pytest.fixture
def mock_assets():
    """
    Mock 掉圖片加載函數。
    Dungeon 初始化時會呼叫這些函數，我們攔截它們以避免文件 IO 錯誤。
    """
    with patch('src.dungeon.dungeon.load_background_tileset') as mock_bg_load, \
         patch('src.dungeon.dungeon.load_foreground_tileset') as mock_fg_load:
        
        # 讓它們返回空字典或假字典，而不是 None
        mock_bg_load.return_value = {'Floor': MagicMock(), 'Outside': MagicMock()}
        mock_fg_load.return_value = {'Wall': MagicMock()}
        
        yield mock_bg_load, mock_fg_load

# --- 測試案例 ---

def test_initialization_full_dungeon(mock_config, mock_assets):
    """
    測試 initialize_dungeon 是否能完整運行生成管線
    並正確同步數據到 Dungeon 實例
    """
    dungeon = Dungeon(mock_config)
    
    # 執行生成
    dungeon.initialize_dungeon(dungeon_id=1)
    
    # 1. 驗證房間列表已填充
    assert len(dungeon.rooms) > 0
    
    # 2. 驗證瓦片網格不再全是 'Outside'
    outside_count = sum(row.count('Outside') for row in dungeon.dungeon_tiles)
    total_cells = mock_config.grid_width * mock_config.grid_height
    assert outside_count < total_cells # 肯定有一些地板或牆壁
    
    # 3. 驗證 Builder 的狀態已同步到 Facade
    assert dungeon.dungeon_tiles == dungeon.builder.tile_manager.grid

def test_initialization_lobby(mock_config, mock_assets):
    """測試大廳生成模式"""
    dungeon = Dungeon(mock_config)
    
    dungeon.initialize_lobby()
    
    # 大廳模式下應該只有一個房間
    assert len(dungeon.rooms) == 1
    assert dungeon.rooms[0].room_type == RoomType.LOBBY
    
    # 驗證瓦片數據存在
    center_tile = dungeon.get_tile(5, 5) # 假設大廳覆蓋了這個區域
    # 具體座標取決於 lobby 的放置邏輯，但這裡我們主要確認不會崩潰且有生成

def test_get_start_position(mock_config, mock_assets):
    """測試獲取玩家起始座標的邏輯"""
    dungeon = Dungeon(mock_config)
    dungeon.initialize_dungeon(1)
    
    start_pos = dungeon.get_start_position()
    
    # 1. 確保返回的是 tuple (x, y)
    assert isinstance(start_pos, tuple)
    assert len(start_pos) == 2
    
    # 2. 驗證座標計算正確性
    # 找出真正的 start room
    start_room = next(r for r in dungeon.rooms if r.room_type == RoomType.START)
    
    expected_x = int(start_room.x + start_room.width // 2) * mock_config.tile_size
    expected_y = int(start_room.y + start_room.height // 2) * mock_config.tile_size
    
    assert start_pos == (expected_x, expected_y)

def test_get_start_position_fallback(mock_config, mock_assets):
    """測試當沒有 Start 房間時的回退機制"""
    dungeon = Dungeon(mock_config)
    # 不調用 initialize，直接訪問，rooms 為空
    
    pos = dungeon.get_start_position()
    assert pos == (0, 0)

def test_reset_state(mock_config, mock_assets):
    """測試重置功能"""
    dungeon = Dungeon(mock_config)
    dungeon.initialize_dungeon(1)
    
    # 確保當前有數據
    assert len(dungeon.rooms) > 0
    
    # 執行重置
    dungeon.reset()
    
    # 驗證數據被清空
    assert len(dungeon.rooms) == 0
    assert len(dungeon.bridges) == 0
    
    # 驗證網格重置為全 Outside
    total_cells = mock_config.grid_width * mock_config.grid_height
    outside_count = sum(row.count('Outside') for row in dungeon.dungeon_tiles)
    assert outside_count == total_cells