import pytest
from unittest.mock import MagicMock, patch
from src.dungeon.algorithms.graph_algorithms import UnionFind, GraphAlgorithms

# --- 1. UnionFind 測試 ---

def test_union_find_basics():
    """測試並查集的基本功能：合併與查找"""
    n = 5
    uf = UnionFind(n)
    
    # 初始狀態：每個元素都是自己的集合
    for i in range(n):
        assert uf.find(i) == i
        
    # 合併 0 和 1
    assert uf.union(0, 1) is True
    assert uf.find(0) == uf.find(1)
    
    # 合併 1 和 2 (此時 0, 1, 2 應該連通)
    assert uf.union(1, 2) is True
    assert uf.find(0) == uf.find(2)
    
    # 嘗試再次合併 0 和 2 (應該返回 False，因為已經連通)
    assert uf.union(0, 2) is False

def test_union_find_rank():
    """測試按秩合併 (Rank) 邏輯"""
    # 構造兩棵樹，確保合併時是小樹掛在大樹下
    uf = UnionFind(4)
    
    # 集合 A: {0, 1}
    uf.union(0, 1)
    # 集合 B: {2, 3}
    uf.union(2, 3)
    
    # 合併 A 和 B
    uf.union(1, 3)
    
    # 全部應該連通
    root = uf.find(0)
    assert all(uf.find(i) == root for i in range(4))

# --- 2. 圖算法基礎測試 (MST, Connectivity) ---

def test_kruskal_mst():
    """測試 Kruskal 最小生成樹算法"""
    # 構建一個簡單的三角形圖
    # 0 --(1)-- 1
    # |       /
    # (10)  (2)
    # |   /
    #   2
    edges = [
        (0, 1, 1.0),
        (1, 2, 2.0),
        (0, 2, 10.0)
    ]
    num_nodes = 3
    
    mst = GraphAlgorithms.kruskal_mst(edges, num_nodes)
    
    # MST 應該選權重最小的兩條邊: (0,1) 和 (1,2)
    assert len(mst) == 2
    assert (0, 1) in mst or (1, 0) in mst
    assert (1, 2) in mst or (2, 1) in mst
    assert (0, 2) not in mst and (2, 0) not in mst

def test_is_connected():
    """測試連通性檢查"""
    # 連通圖
    # 0-1-2
    edges_connected = [(0, 1), (1, 2)]
    assert GraphAlgorithms.is_connected(edges_connected, 3) is True
    
    # 非連通圖 (0-1, 2 孤立)
    edges_disconnected = [(0, 1)]
    assert GraphAlgorithms.is_connected(edges_disconnected, 3) is False

def test_get_connected_components():
    """測試獲取連通分量"""
    # 0-1   2-3   4(孤立)
    edges = [(0, 1), (2, 3)]
    num_nodes = 5
    
    components = GraphAlgorithms.get_connected_components(edges, num_nodes)
    
    assert len(components) == 3
    # 轉換為 frozenset 以便比較 (順序不重要)
    comp_sets = {frozenset(c) for c in components}
    assert frozenset({0, 1}) in comp_sets
    assert frozenset({2, 3}) in comp_sets
    assert frozenset({4}) in comp_sets

# --- 3. 幾何運算測試 (最關鍵的部分) ---

class MockRoom:
    """用於測試的簡單房間類"""
    def __init__(self, id, x, y, w, h):
        self.id = id
        self.x = x
        self.y = y
        self.width = w
        self.height = h

def test_line_intersects_rect():
    """測試線段與矩形相交檢測"""
    # 定義一個矩形: x=10, y=10, w=20, h=20 (範圍 10~30, 10~30)
    rx, ry, rw, rh = 10, 10, 20, 20
    
    # Case 1: 穿過矩形中心 (相交)
    assert GraphAlgorithms._line_intersects_rect(0, 20, 40, 20, rx, ry, rw, rh) is True
    
    # Case 2: 完全在外部，不相交
    assert GraphAlgorithms._line_intersects_rect(0, 0, 40, 0, rx, ry, rw, rh) is False
    
    # Case 3: 線段在矩形內部 (相交/包含)
    assert GraphAlgorithms._line_intersects_rect(15, 15, 25, 25, rx, ry, rw, rh) is True
    
    # Case 4: 只有一個端點在內部 (相交)
    assert GraphAlgorithms._line_intersects_rect(20, 20, 40, 40, rx, ry, rw, rh) is True

def test_would_cross_rooms():
    """測試房間穿透邏輯"""
    # 房間 A (左邊)
    room_a = MockRoom(0, 0, 0, 10, 10) # Center (5, 5)
    # 房間 B (右邊)
    room_b = MockRoom(1, 100, 0, 10, 10) # Center (105, 5)
    
    # 房間 C (中間阻擋)
    room_c = MockRoom(2, 50, 0, 10, 10) # 範圍 x: 50~60, y: 0~10
    
    all_rooms = [room_a, room_b, room_c]
    
    # 測試 A -> B 的連線是否會穿過 C
    # A center (5,5), B center (105,5). Line y=5. C covers y=0~10. 
    # 應該回傳 True
    assert GraphAlgorithms._would_cross_rooms(room_a, room_b, all_rooms) is True
    
    # 測試 A -> B，但在沒有 C 的情況下
    assert GraphAlgorithms._would_cross_rooms(room_a, room_b, [room_a, room_b]) is False

# --- 4. 複雜邏輯測試 (Add Extra Edges) ---

def test_add_extra_edges_logic():
    """
    測試添加額外邊的邏輯：
    1. 驗證 Ratio 0 不添加
    2. 驗證會過濾掉太長的邊
    3. 驗證會過濾掉形成三角形的邊 (Adjacency check)
    """
    # 構建一個簡單的圖
    # 0 --(10)-- 1 --(10)-- 2
    # |                     |
    # +---------(100)-------+
    # 邊 (0,2) 長度 100，非常長
    
    mst_edges = [(0, 1), (1, 2)]
    all_edges = [
        (0, 1, 10.0), 
        (1, 2, 10.0), 
        (0, 2, 100.0)  # 長邊
    ]
    
    # Case 1: Ratio = 0
    result = GraphAlgorithms.add_extra_edges(mst_edges, all_edges, ratio=0.0)
    assert len(result) == 2
    
    # Case 2: Ratio = 1.0, 但 (0,2) 太長 (MST平均 10, 限制 15, 100 > 15)
    # 應該被過濾掉
    result = GraphAlgorithms.add_extra_edges(mst_edges, all_edges, ratio=1.0)
    assert (0, 2) not in result
    assert len(result) == 2

def test_add_extra_edges_with_random():
    """測試實際添加邊的情況 (Mock random)"""
    mst_edges = [(0, 1), (2, 3)]
    # 候選邊：長度合適，且不會形成三角形 (因為 MST 是斷開的兩塊)
    all_edges = [
        (0, 1, 10), (2, 3, 10),
        (1, 2, 12)  # 合法候選邊
    ]
    
    # 使用 patch 確保 random.sample 總是選中我們想要的
    with patch('random.sample') as mock_sample:
        mock_sample.return_value = [(1, 2)]
        
        result = GraphAlgorithms.add_extra_edges(mst_edges, all_edges, ratio=1.0)
        
        assert len(result) == 3 # 2 MST + 1 Extra
        assert (1, 2) in result