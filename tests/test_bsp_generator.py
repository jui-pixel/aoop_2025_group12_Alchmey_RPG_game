import pytest
import random
from unittest.mock import MagicMock, patch
from src.dungeon.algorithms.bsp_generator import BSPGenerator
from src.dungeon.bsp_node import BSPNode  # 假設你的 BSPNode 結構如下，如果沒有請看下方的 Mock 說明

# 如果測試環境無法 import BSPNode，可以使用這個 Mock 類別暫時替代
# class BSPNode:
#     def __init__(self, x, y, width, height):
#         self.x, self.y = x, y
#         self.width, self.height = width, height
#         self.left = None
#         self.right = None

# --- Fixtures (測試數據準備) ---

@pytest.fixture
def mock_config():
    """建立一個模擬的配置物件"""
    config = MagicMock()
    # 設定預設測試值
    config.max_split_depth = 5
    config.min_split_size = 10
    return config

@pytest.fixture
def bsp_gen(mock_config):
    """初始化 Generator"""
    return BSPGenerator(mock_config)

# --- 測試案例 ---

def test_initialization(bsp_gen, mock_config):
    """測試初始化是否正確綁定配置"""
    assert bsp_gen.config == mock_config

def test_generate_root_node(bsp_gen):
    """測試是否生成了正確大小的根節點"""
    width, height = 100, 200
    root = bsp_gen.generate(width, height)
    
    assert isinstance(root, BSPNode)
    assert root.x == 0
    assert root.y == 0
    assert root.width == width
    assert root.height == height

def test_stop_splitting_by_depth(mock_config):
    """測試深度限制：設為 0 時不應分割"""
    mock_config.max_split_depth = 0
    gen = BSPGenerator(mock_config)
    
    root = gen.generate(100, 100)
    
    # 深度為 0，應該沒有子節點
    assert root.left is None
    assert root.right is None
    
    # 驗證統計數據
    assert gen.get_tree_depth(root) == 0
    total, leaves = gen.get_node_count(root)
    assert total == 1
    assert leaves == 1

def test_stop_splitting_by_size(mock_config):
    """測試尺寸限制：空間太小不應分割"""
    mock_config.min_split_size = 10
    gen = BSPGenerator(mock_config)
    
    # 創建一個剛好不足以分割的空間 (小於 min_size * 2)
    # min_size * 2 = 20，我們給 18
    root = gen.generate(18, 18)
    
    assert root.left is None
    assert root.right is None

def test_perform_split_geometry(bsp_gen):
    """
    測試分割後的幾何邏輯：
    左節點 + 右節點的面積 必須等於 父節點面積
    """
    # 固定隨機腫子以確保每次分割結果一致 (或使用 mock)
    random.seed(42)
    
    root = bsp_gen.generate(100, 100)
    
    # 我們只檢查第一層分割 (如果有分割的話)
    if root.left and root.right:
        parent_area = root.width * root.height
        left_area = root.left.width * root.left.height
        right_area = root.right.width * root.right.height
        
        assert parent_area == left_area + right_area
        
        # 檢查座標連續性
        if root.left.x + root.left.width == root.right.x:
            # 垂直分割
            assert root.left.y == root.right.y
            assert root.left.height == root.right.height
        else:
            # 水平分割
            assert root.left.x == root.right.x
            assert root.left.width == root.right.width

def test_split_direction_bias(bsp_gen):
    """測試分割方向的偏好（寬的偏向垂直切，高的偏向水平切）"""
    node_wide = BSPNode(0, 0, 100, 20)  # 很寬
    node_tall = BSPNode(0, 0, 20, 100)  # 很高
    
    # 模擬 random.choices
    # 因為你的代碼使用了權重選擇，這裡我們透過 Mock random 來驗證邏輯是否正確被呼叫
    
    with patch('random.choices') as mock_choices:
        # 測試寬節點
        bsp_gen._choose_split_direction(node_wide)
        # 檢查傳入的權重：vertical (切X軸) 的權重應該比較大
        args, kwargs = mock_choices.call_args
        weights = kwargs['weights']
        # weights[0] 是 vertical, weights[1] 是 horizontal
        assert weights[0] > weights[1]
        
        # 測試高節點
        bsp_gen._choose_split_direction(node_tall)
        args, kwargs = mock_choices.call_args
        weights = kwargs['weights']
        assert weights[1] > weights[0]

def test_collect_leaf_nodes(bsp_gen):
    """測試葉節點收集功能"""
    # 手動建立一個簡單的樹結構，避免依賴隨機生成的結果
    #       Root
    #      /    \
    #     L1    R1 (Leaf)
    #    /  \
    #  L2    R2
    # (Leaf) (Leaf)
    
    root = BSPNode(0, 0, 100, 100)
    root.right = BSPNode(50, 0, 50, 100) # Leaf
    
    root.left = BSPNode(0, 0, 50, 100)
    root.left.left = BSPNode(0, 0, 50, 50) # Leaf
    root.left.right = BSPNode(0, 50, 50, 50) # Leaf
    
    leaves = bsp_gen.collect_leaf_nodes(root)
    
    assert len(leaves) == 3
    assert root.right in leaves
    assert root.left.left in leaves
    assert root.left.right in leaves
    assert root.left not in leaves # 中間節點不應被包含

def test_integration_full_generation(bsp_gen):
    """
    整合測試：生成一個完整的樹並驗證所有葉節點
    這可以捕捉到遞歸邏輯中的錯誤
    """
    # 允許生成較深的樹
    bsp_gen.config.max_split_depth = 3
    bsp_gen.config.min_split_size = 5
    
    root = bsp_gen.generate(50, 50)
    leaves = bsp_gen.collect_leaf_nodes(root)
    
    # 驗證所有葉節點是否都在根節點的範圍內
    for leaf in leaves:
        assert leaf.x >= root.x
        assert leaf.y >= root.y
        assert leaf.x + leaf.width <= root.x + root.width
        assert leaf.y + leaf.height <= root.y + root.height
        
        # 驗證葉節點沒有子節點
        assert leaf.left is None
        assert leaf.right is None