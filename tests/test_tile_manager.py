import pytest
from src.dungeon.managers.tile_manager import TileManager
from src.dungeon.room import Room

# --- Fixtures ---

@pytest.fixture
def manager():
    """建立一個 10x10 的瓦片管理器，預設全為 Outside"""
    return TileManager(10, 10, default_tile='Outside')

@pytest.fixture
def passable_tiles():
    return {'Floor', 'Bridge_floor'}

# --- 基礎功能測試 ---

def test_initialization(manager):
    assert manager.width == 10
    assert manager.height == 10
    assert manager.get_tile(0, 0) == 'Outside'
    assert manager.count_tiles('Outside') == 100

def test_set_and_get_tile(manager):
    manager.set_tile(5, 5, 'Floor')
    assert manager.get_tile(5, 5) == 'Floor'
    # 邊界外測試
    assert manager.get_tile(-1, 0) == 'Outside'
    assert manager.get_tile(10, 10) == 'Outside'

def test_find_tiles(manager):
    manager.set_tile(1, 1, 'Wall')
    manager.set_tile(2, 2, 'Wall')
    positions = manager.find_tiles('Wall')
    assert len(positions) == 2
    assert (1, 1) in positions
    assert (2, 2) in positions

def test_place_room(manager):
    """測試將房間數據映射到網格"""
    # 建立一個 3x3 的房間，全為 Floor
    room = Room(0, 2, 2, 3, 3) # x=2, y=2
    # 手動填充房間內部數據 (模擬 Room 內部邏輯)
    room.tiles = [['Floor' for _ in range(3)] for _ in range(3)]
    
    manager.place_room(room)
    
    # 驗證網格 (2,2) 到 (4,4) 變成了 Floor
    assert manager.get_tile(2, 2) == 'Floor'
    assert manager.get_tile(4, 4) == 'Floor'
    # 驗證外部仍是 Outside
    assert manager.get_tile(1, 1) == 'Outside'

# --- 牆壁生成與調整測試 (核心邏輯) ---

def test_add_initial_walls(manager, passable_tiles):
    """測試地板周圍的 Outside 自動轉為 Border_wall"""
    # 在中心放一個 Floor
    manager.set_tile(5, 5, 'Floor')
    
    # 執行初始牆壁生成
    manager._add_initial_walls(passable_tiles)
    
    # 中心仍是 Floor
    assert manager.get_tile(5, 5) == 'Floor'
    
    # 周圍 8 格應該變成 Border_wall
    neighbors = manager.get_neighbors(5, 5, include_diagonal=True)
    for nx, ny, tile in neighbors:
        assert manager.get_tile(nx, ny) == 'Border_wall'

def test_adjust_wall_simple_sides(manager, passable_tiles):
    """測試基本邊牆 (Top, Bottom, Left, Right)"""
    # 設定場景：
    # W
    # F
    manager.set_tile(1, 1, 'Border_wall')
    manager.set_tile(1, 2, 'Floor') # 下方是地板 -> 這是上牆 (Top)
    
    manager.adjust_wall(passable_tiles)
    assert manager.get_tile(1, 1) == 'Border_wall_top'
    
    # 重置並測試左牆 (右邊是地板)
    manager.reset()
    manager.set_tile(1, 1, 'Border_wall')
    manager.set_tile(2, 1, 'Floor')
    manager.adjust_wall(passable_tiles)
    assert manager.get_tile(1, 1) == 'Border_wall_left'

def test_adjust_wall_convex_corner(manager, passable_tiles):
    """測試外凸角 (Convex Corner)"""
    # 測試 Convex Top Left (右下角是區域)
    # 邏輯: 右(R), 右下(BR), 下(B) 是可通行
    # W F
    # F F
    manager.set_tile(1, 1, 'Border_wall') # 目標
    manager.set_tile(2, 1, 'Floor')       # R
    manager.set_tile(2, 2, 'Floor')       # BR
    manager.set_tile(1, 2, 'Floor')       # B
    
    manager.adjust_wall(passable_tiles)
    
    assert manager.get_tile(1, 1) == 'Border_wall_convex_top_left'

def test_adjust_wall_concave_corner(manager, passable_tiles):
    """測試內凹角 (Concave Corner)"""
    # 測試 Concave Bottom Right (只有左上是地板)
    # F W
    # W W
    # 目標在 (1,1)
    manager.set_tile(0, 0, 'Floor')       # TL (唯一的可通行鄰居)
    manager.set_tile(1, 1, 'Border_wall') # 目標
    # 其他預設 Outside (不可通行)
    
    manager.adjust_wall(passable_tiles)
    
    # 根據位元遮罩 0b00000001 (TL) -> Concave Bottom Right
    assert manager.get_tile(1, 1) == 'Border_wall_concave_bottom_right'

def test_adjust_isolated_wall(manager, passable_tiles):
    """測試孤立牆 (四周都是地板) 應被移除"""
    #  F
    # F W F
    #  F
    manager.set_tile(1, 1, 'Border_wall')
    manager.set_tile(1, 0, 'Floor') # Top
    manager.set_tile(1, 2, 'Floor') # Bottom
    manager.set_tile(0, 1, 'Floor') # Left
    manager.set_tile(2, 1, 'Floor') # Right
    
    manager.adjust_wall(passable_tiles)
    
    # 應該變成 Bridge_floor
    assert manager.get_tile(1, 1) == 'Bridge_floor'

def test_finalize_walls_integration(manager, passable_tiles):
    """集成測試：從 Outside -> Border_wall -> Variant"""
    # 初始狀態：中間一個 Floor
    manager.set_tile(5, 5, 'Floor')
    
    # 執行完整流程
    manager.finalize_walls(passable_tiles)
    
    # 檢查：
    # (5,5) 仍是 Floor
    assert manager.get_tile(5, 5) == 'Floor'
    
    # (5,4) 是上方鄰居，應該先變成 Border_wall，然後因為下方是 Floor，變成 Top Wall
    assert manager.get_tile(5, 4) == 'Border_wall_top'
    
    # (4,5) 是左方鄰居，應該變成 Left Wall
    assert manager.get_tile(4, 5) == 'Border_wall_left'
    
    # (4,4) 是左上角鄰居
    # 它的鄰居只有 (5,5) 是 Floor (相對於 (4,4) 來說是 BR 方向)
    # 只有 BR 可通行 -> Concave Top Left
    assert manager.get_tile(4, 4) == 'Border_wall_concave_top_left'

def test_get_neighbors(manager):
    """測試鄰居獲取邊界檢查"""
    # 測試角落 (0,0)
    neighbors = manager.get_neighbors(0, 0)
    # 應該只有 (0,1) 和 (1,0)
    assert len(neighbors) == 2
    assert (1, 0, 'Outside') in neighbors
    assert (0, 1, 'Outside') in neighbors