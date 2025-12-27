import pytest
from src.dungeon.algorithms.pathfinding import AStarPathfinder

# --- Fixtures (測試資料準備) ---

@pytest.fixture
def basic_grid():
    """
    建立一個簡單的 5x5 網格
    . = 地板 (可通行)
    # = 牆壁 (不可通行)
    """
    return [
        ['.', '.', '.', '.', '.'],
        ['.', '#', '#', '#', '.'],
        ['.', '.', '.', '#', '.'],
        ['.', '#', '.', '.', '.'],
        ['.', '.', '.', '.', '.']
    ]

@pytest.fixture
def cost_grid():
    """
    建立一個用於測試成本的網格
    . = 普通道路 (Cost 1)
    M = 泥沼 (Cost 5) - 雖然路徑短但很慢
    """
    return [
        ['S', 'M', 'M', 'E'],  # 直走經過泥沼 (距離 3, 成本高)
        ['.', '.', '.', '.']   # 繞路走普通地 (距離 4, 成本低)
    ]

# --- 測試案例 ---

def test_basic_path_success(basic_grid):
    """測試從 A 到 B 的簡單路徑 (Happy Path)"""
    # 設定 '.' 為可通行
    pf = AStarPathfinder(basic_grid, passable_tiles={'.'})
    
    start = (0, 0)
    end = (4, 0) # 繞過牆壁
    
    path = pf.find_path(start, end)
    
    assert len(path) > 0
    assert path[0] == start
    assert path[-1] == end
    
    # 驗證路徑連續性
    for i in range(len(path) - 1):
        curr = path[i]
        next_node = path[i+1]
        # 檢查兩點距離是否為 1 (不允許對角線時)
        dist = abs(curr[0] - next_node[0]) + abs(curr[1] - next_node[1])
        assert dist == 1

def test_path_blocked(basic_grid):
    """測試當終點無法到達時"""
    # 封死一個區域
    grid = [
        ['.', '#', '.'],
        ['#', '#', '#'],  # 牆壁完全隔離
        ['.', '.', '.']
    ]
    pf = AStarPathfinder(grid, passable_tiles={'.'})
    
    path = pf.find_path((0, 0), (2, 2))
    assert path == []

def test_invalid_endpoints(basic_grid):
    """測試起點或終點無效的情況"""
    pf = AStarPathfinder(basic_grid, passable_tiles={'.'})
    
    # 終點在牆壁上
    path = pf.find_path((0, 0), (1, 1)) # (1,1) is '#'
    assert path == []
    
    # 起點出界
    path = pf.find_path((-1, 0), (0, 0))
    assert path == []

def test_diagonal_movement():
    """測試對角線移動功能"""
    grid = [
        ['.', '.', '.'],
        ['.', '.', '.'],
        ['.', '.', '.']
    ]
    pf = AStarPathfinder(grid, passable_tiles={'.'})
    
    start = (0, 0)
    end = (2, 2)
    
    # Case 1: 不允許對角線 (曼哈頓走法)
    # (0,0) -> (1,0) -> (2,0) -> (2,1) -> (2,2) = 5 nodes (4 steps)
    path_no_diag = pf.find_path(start, end, allow_diagonal=False)
    assert len(path_no_diag) == 5 
    
    # Case 2: 允許對角線
    # (0,0) -> (1,1) -> (2,2) = 3 nodes (2 steps)
    path_diag = pf.find_path(start, end, allow_diagonal=True)
    assert len(path_diag) == 3

def test_cost_weights(cost_grid):
    """
    測試 A* 是否會選擇成本最低的路徑，而不僅僅是步數最少
    """
    # 設定成本：M (Mud) = 5.0, S/E/. = 1.0
    cost_map = {'M': 5.0, '.': 1.0, 'S': 1.0, 'E': 1.0}
    pf = AStarPathfinder(cost_grid, 
                         passable_tiles={'S', 'E', '.', 'M'},
                         cost_map=cost_map)
    
    start = (0, 0) # S
    end = (3, 0)   # E
    
    path = pf.find_path(start, end)
    
    # 預期路徑應該繞路走下方 (y=1)，因為上方經過兩個 M (Cost 10)
    # 下方路徑：(0,0)->(0,1)->(1,1)->(2,1)->(3,1)->(3,0)
    
    # 檢查路徑中是否包含了 y=1 的節點
    y_coords = [p[1] for p in path]
    assert 1 in y_coords
    
    # 確保沒有走捷徑 (y=0 的 M 區域)
    # 路徑中間不應該有 (1,0) 和 (2,0)
    assert (1, 0) not in path
    assert (2, 0) not in path

def test_outside_tile_rule():
    """測試特殊的 'Outside' 瓦片規則 (即使不在 passable_tiles 也可通過)"""
    grid = [['Outside', 'Outside'],
            ['Floor', 'Floor']]
    
    # 只允許 'Floor'，沒把 'Outside' 加入
    pf = AStarPathfinder(grid, passable_tiles={'Floor'})
    
    # 嘗試走在 Outside 上
    path = pf.find_path((0, 0), (1, 0))
    
    # 根據代碼邏輯 `if tile != 'Outside'`，它應該能通過
    assert len(path) > 0
    assert path == [(0, 0), (1, 0)]

def test_find_multiple_paths(basic_grid):
    """測試同時尋找多個終點"""
    pf = AStarPathfinder(basic_grid, passable_tiles={'.'})
    
    start = (0, 0)
    ends = [(4, 0), (0, 4)]
    
    paths = pf.find_multiple_paths(start, ends)
    
    assert len(paths) == 2
    assert (4, 0) in paths
    assert (0, 4) in paths
    assert len(paths[(4, 0)]) > 0

def test_get_reachable_tiles(basic_grid):
    """測試 BFS 範圍搜索 (Flood Fill)"""
    # 小封閉空間
    grid = [
        ['.', '.', '#'],
        ['.', '.', '#'],
        ['#', '#', '#']
    ]
    pf = AStarPathfinder(grid, passable_tiles={'.'})
    
    # 測試全域搜索
    reachable = pf.get_reachable_tiles((0, 0))
    # 左上角 2x2 的區域是 4 格
    assert len(reachable) == 4
    assert (0, 0) in reachable
    assert (1, 1) in reachable
    assert (2, 0) not in reachable # 牆壁後
    
    # 測試最大距離限制 (Max Distance)
    reachable_limited = pf.get_reachable_tiles((0, 0), max_distance=1)
    # 距離 0: (0,0)
    # 距離 1: (0,1), (1,0)
    # (1,1) 距離是 2，不應包含
    assert len(reachable_limited) == 3
    assert (1, 1) not in reachable_limited