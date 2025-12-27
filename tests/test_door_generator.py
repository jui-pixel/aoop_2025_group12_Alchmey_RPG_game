import pytest
from src.dungeon.generators.door_generator import DoorGenerator

# --- Fixtures ---

@pytest.fixture
def door_gen():
    """建立門生成器實例"""
    return DoorGenerator()

@pytest.fixture
def empty_grid():
    """建立一個 5x5 的空白網格 (全 Outside)"""
    return [['Outside' for _ in range(5)] for _ in range(5)]

# --- 測試案例 ---

def test_basic_door_generation(door_gen, empty_grid):
    """測試基本的門生成邏輯 (Happy Path)"""
    # 設定場景：牆壁在 (2,2)，走廊在 (2,3) [右邊]
    empty_grid[2][2] = 'Border_wall'
    empty_grid[2][3] = 'Bridge_floor'
    
    door_gen.generate_doors(empty_grid)
    
    # 驗證：牆壁變成了門
    assert empty_grid[2][2] == 'Door'
    # 驗證：走廊保持不變
    assert empty_grid[2][3] == 'Bridge_floor'

def test_four_directions(door_gen):
    """測試上下左右四個方向的鄰接都能觸發門生成"""
    # 建立一個十字形的測試網格
    # W = Wall, B = Bridge
    #   B
    # B W B
    #   B
    
    grid = [['Outside' for _ in range(3)] for _ in range(3)]
    
    # 中心放牆壁
    grid[1][1] = 'Border_wall'
    
    # 測試上 (0, 1)
    grid[0][1] = 'Bridge_floor'
    door_gen.generate_doors(grid)
    assert grid[1][1] == 'Door'
    
    # 重置
    grid[1][1] = 'Border_wall'
    grid[0][1] = 'Outside'
    
    # 測試下 (2, 1)
    grid[2][1] = 'Bridge_floor'
    door_gen.generate_doors(grid)
    assert grid[1][1] == 'Door'

    # 重置
    grid[1][1] = 'Border_wall'
    grid[2][1] = 'Outside'
    
    # 測試左 (1, 0)
    grid[1][0] = 'Bridge_floor'
    door_gen.generate_doors(grid)
    assert grid[1][1] == 'Door'

def test_ignore_isolated_walls(door_gen, empty_grid):
    """測試沒有鄰接走廊的牆壁不會變形"""
    empty_grid[2][2] = 'Border_wall'
    # 四周都是 Outside，沒有 Bridge_floor
    
    door_gen.generate_doors(empty_grid)
    
    assert empty_grid[2][2] == 'Border_wall'

def test_ignore_non_border_walls(door_gen, empty_grid):
    """測試非 Border_wall 的瓦片即使鄰接走廊也不會變形"""
    # 設定場景：普通地板 (Floor) 在走廊旁邊
    empty_grid[2][2] = 'Floor'
    empty_grid[2][3] = 'Bridge_floor'
    
    door_gen.generate_doors(empty_grid)
    
    # 應該保持原樣，因為它不是牆
    assert empty_grid[2][2] == 'Floor'

def test_different_wall_types(door_gen, empty_grid):
    """測試不同後綴的牆壁類型 (startswith 邏輯)"""
    # 測試 Border_wall_top, Border_wall_side 等等
    empty_grid[1][1] = 'Border_wall_top'
    empty_grid[1][2] = 'Bridge_floor'
    
    empty_grid[3][3] = 'Border_wall_side'
    empty_grid[3][4] = 'Bridge_floor'
    
    door_gen.generate_doors(empty_grid)
    
    assert empty_grid[1][1] == 'Door'
    assert empty_grid[3][3] == 'Door'

def test_grid_boundary_safety(door_gen):
    """測試在網格邊緣的操作不會導致 IndexOutOfBounds"""
    # 3x3 網格
    grid = [['Outside' for _ in range(3)] for _ in range(3)]
    
    # 在 (0,0) 放牆壁，在 (0,1) 放走廊
    grid[0][0] = 'Border_wall'
    grid[0][1] = 'Bridge_floor'
    
    # 在最右下角 (2,2) 放牆壁，但沒有走廊
    grid[2][2] = 'Border_wall'
    
    try:
        door_gen.generate_doors(grid)
    except IndexError:
        pytest.fail("generate_doors raised IndexError on grid boundary")
        
    assert grid[0][0] == 'Door'
    assert grid[2][2] == 'Border_wall'

def test_count_doors(door_gen, empty_grid):
    """測試門數量統計功能"""
    empty_grid[0][0] = 'Door'
    empty_grid[1][1] = 'Door'
    empty_grid[2][2] = 'Border_wall' # 混淆項
    
    count = door_gen.count_doors(empty_grid)
    
    assert count == 2