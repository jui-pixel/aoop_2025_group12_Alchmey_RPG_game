# src/dungeon/algorithms/graph_algorithms.py
"""
圖算法模塊
提供 MST、圖連接等算法
"""
from typing import List, Tuple, Set
import random


class UnionFind:
    """
    並查集（Union-Find）數據結構
    用於 Kruskal 算法檢測環
    """
    
    def __init__(self, n: int):
        """
        初始化並查集
        
        Args:
            n: 元素數量
        """
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """
        查找元素的根節點（帶路徑壓縮）
        
        Args:
            x: 元素索引
        
        Returns:
            根節點索引
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """
        合併兩個集合
        
        Args:
            x: 第一個元素
            y: 第二個元素
        
        Returns:
            是否成功合併（如果已在同一集合則返回 False）
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # 按秩合併
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True


class GraphAlgorithms:
    """
    圖算法集合
    提供 MST、圖連接等靜態方法
    """
    
    @staticmethod
    def kruskal_mst(edges: List[Tuple[int, int, float]], num_nodes: int) -> List[Tuple[int, int]]:
        """
        Kruskal 最小生成樹算法
        
        Args:
            edges: 邊列表 [(node1, node2, weight), ...]
            num_nodes: 節點數量
        
        Returns:
            MST 邊列表 [(node1, node2), ...]
        """
        # 按權重排序
        sorted_edges = sorted(edges, key=lambda e: e[2])
        
        # 初始化並查集
        uf = UnionFind(num_nodes)
        
        # Kruskal 算法
        mst_edges = []
        for node1, node2, weight in sorted_edges:
            if uf.union(node1, node2):
                mst_edges.append((node1, node2))
                # MST 有 n-1 條邊
                if len(mst_edges) == num_nodes - 1:
                    break
        
        return mst_edges
    
    @staticmethod
    def add_extra_edges(mst_edges: List[Tuple[int, int]], 
                       all_edges: List[Tuple[int, int, float]], 
                       ratio: float,
                       rooms: List = None) -> List[Tuple[int, int]]:
        """
        添加額外邊以增加連通性，避免穿過房間、過長路徑和相鄰連接
        
        Args:
            mst_edges: MST 邊列表
            all_edges: 所有可能的邊
            ratio: 額外邊的比例（0.0-1.0）
            rooms: 房間列表，用於檢查是否穿過房間 (可選)
        
        Returns:
            包含 MST 和額外邊的邊列表
        """
        if ratio <= 0.0:
            return mst_edges
        
        # 將 MST 邊轉換為集合以便快速查找
        mst_set = set(mst_edges)
        mst_set.update((b, a) for a, b in mst_edges)  # 添加反向邊
        
        # 構建鄰接表（用於檢測相鄰路徑）
        adjacency = {}
        for node1, node2 in mst_edges:
            if node1 not in adjacency:
                adjacency[node1] = set()
            if node2 not in adjacency:
                adjacency[node2] = set()
            adjacency[node1].add(node2)
            adjacency[node2].add(node1)
        
        # 找出非 MST 邊
        non_mst_edges = [
            (node1, node2, weight) for node1, node2, weight in all_edges
            if (node1, node2) not in mst_set
        ]
        
        if not non_mst_edges:
            return mst_edges
        
        # 計算長度閾值（使用 MST 邊的平均長度作為參考）
        mst_weights = [w for n1, n2, w in all_edges if (n1, n2) in mst_set or (n2, n1) in mst_set]
        if mst_weights:
            avg_mst_length = sum(mst_weights) / len(mst_weights)
            max_extra_length = avg_mst_length * 1.5  # 最大允許為 MST 平均長度的 1.5 倍
        else:
            max_extra_length = float('inf')
        
        # 過濾額外邊
        valid_edges = []
        for node1, node2, weight in non_mst_edges:
            # 1. 檢查是否過長
            if weight > max_extra_length:
                continue
            
            # 2. 檢查是否為相鄰連接（避免三角形）
            # 如果 node1 和 node2 有共同鄰居，則跳過
            if node1 in adjacency and node2 in adjacency:
                common_neighbors = adjacency[node1] & adjacency[node2]
                if common_neighbors:
                    # 有共同鄰居，會形成三角形，跳過
                    continue
            
            # 3. 檢查是否會穿過房間（如果提供了房間列表）
            if rooms:
                if GraphAlgorithms._would_cross_rooms(rooms[node1], rooms[node2], rooms):
                    continue
            
            valid_edges.append((node1, node2))
        
        # 如果過濾後沒有有效邊，返回原 MST
        if not valid_edges:
            print("GraphAlgorithms: 過濾後沒有符合條件的額外邊")
            return mst_edges
        
        # 計算要添加的邊數量
        num_extra = int(len(valid_edges) * ratio)
        
        if num_extra <= 0:
            return mst_edges
        
        # 隨機選擇額外邊
        extra_edges = random.sample(valid_edges, min(num_extra, len(valid_edges)))
        print(f"GraphAlgorithms: 添加 {len(extra_edges)} 條額外邊（過濾前: {len(non_mst_edges)}）")
        return mst_edges + extra_edges
    
    @staticmethod
    def _would_cross_rooms(room1, room2, all_rooms: List) -> bool:
        """
        檢查兩個房間之間的連線是否會穿過其他房間
        
        Args:
            room1: 起始房間
            room2: 終止房間
            all_rooms: 所有房間列表
        
        Returns:
            True 如果會穿過其他房間，False 否則
        """
        # 計算兩個房間的中心點
        c1_x = room1.x + room1.width / 2
        c1_y = room1.y + room1.height / 2
        c2_x = room2.x + room2.width / 2
        c2_y = room2.y + room2.height / 2
        
        # 檢查線段是否穿過其他房間
        for room in all_rooms:
            # 跳過起始和終止房間
            if room.id == room1.id or room.id == room2.id:
                continue
            
            # 檢查線段是否與房間矩形相交
            if GraphAlgorithms._line_intersects_rect(
                c1_x, c1_y, c2_x, c2_y,
                room.x, room.y, room.width, room.height
            ):
                return True
        
        return False
    
    @staticmethod
    def _line_intersects_rect(x1: float, y1: float, x2: float, y2: float,
                               rect_x: float, rect_y: float, 
                               rect_w: float, rect_h: float) -> bool:
        """
        檢查線段是否與矩形相交（穿過矩形內部）
        
        Args:
            x1, y1: 線段起點
            x2, y2: 線段終點
            rect_x, rect_y: 矩形左上角
            rect_w, rect_h: 矩形寬高
        
        Returns:
            True 如果線段穿過矩形，False 否則
        """
        # 矩形邊界
        left = rect_x
        right = rect_x + rect_w
        top = rect_y
        bottom = rect_y + rect_h
        
        # 使用 Cohen-Sutherland 算法檢查線段是否與矩形相交
        # 簡化版本：檢查線段是否與矩形內部相交
        
        # 檢查線段的兩個端點是否都在矩形外的同一側
        out1 = GraphAlgorithms._outcode(x1, y1, left, right, top, bottom)
        out2 = GraphAlgorithms._outcode(x2, y2, left, right, top, bottom)
        
        # 如果兩個端點都在矩形外的同一側，則不相交
        if out1 & out2:
            return False
        
        # 如果至少一個端點在矩形內部或邊界上，則相交
        if out1 == 0 or out2 == 0:
            # 但要確保不是僅僅觸碰邊界
            # 檢查線段中點是否在矩形內
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            if left < mid_x < right and top < mid_y < bottom:
                return True
        
        # 更精確的線段-矩形相交檢測
        # 檢查線段是否與矩形的四條邊相交
        return (
            GraphAlgorithms._line_segment_intersect(x1, y1, x2, y2, left, top, right, top) or  # 上邊
            GraphAlgorithms._line_segment_intersect(x1, y1, x2, y2, right, top, right, bottom) or  # 右邊
            GraphAlgorithms._line_segment_intersect(x1, y1, x2, y2, right, bottom, left, bottom) or  # 下邊
            GraphAlgorithms._line_segment_intersect(x1, y1, x2, y2, left, bottom, left, top)  # 左邊
        )
    
    @staticmethod
    def _outcode(x: float, y: float, left: float, right: float, 
                 top: float, bottom: float) -> int:
        """計算點相對於矩形的位置碼"""
        code = 0
        if x < left:
            code |= 1  # 左
        elif x > right:
            code |= 2  # 右
        if y < top:
            code |= 4  # 上
        elif y > bottom:
            code |= 8  # 下
        return code
    
    @staticmethod
    def _line_segment_intersect(x1: float, y1: float, x2: float, y2: float,
                                x3: float, y3: float, x4: float, y4: float) -> bool:
        """
        檢查兩條線段是否相交
        線段1: (x1,y1) to (x2,y2)
        線段2: (x3,y3) to (x4,y4)
        """
        def ccw(ax, ay, bx, by, cx, cy):
            return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
        
        return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and
                ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4))
    
    @staticmethod
    def build_complete_graph(num_nodes: int, 
                            distance_func) -> List[Tuple[int, int, float]]:
        """
        構建完全圖
        
        Args:
            num_nodes: 節點數量
            distance_func: 距離函數 distance_func(i, j) -> float
        
        Returns:
            所有邊的列表 [(node1, node2, weight), ...]
        """
        edges = []
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                weight = distance_func(i, j)
                edges.append((i, j, weight))
        return edges
    
    @staticmethod
    def is_connected(edges: List[Tuple[int, int]], num_nodes: int) -> bool:
        """
        檢查圖是否連通
        
        Args:
            edges: 邊列表
            num_nodes: 節點數量
        
        Returns:
            圖是否連通
        """
        if num_nodes == 0:
            return True
        
        # 構建鄰接表
        adj = [set() for _ in range(num_nodes)]
        for node1, node2 in edges:
            adj[node1].add(node2)
            adj[node2].add(node1)
        
        # DFS 檢查連通性
        visited = set()
        stack = [0]
        
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            stack.extend(adj[node])
        
        return len(visited) == num_nodes
    
    @staticmethod
    def get_connected_components(edges: List[Tuple[int, int]], 
                                 num_nodes: int) -> List[Set[int]]:
        """
        獲取圖的所有連通分量
        
        Args:
            edges: 邊列表
            num_nodes: 節點數量
        
        Returns:
            連通分量列表，每個分量是一個節點集合
        """
        # 構建鄰接表
        adj = [set() for _ in range(num_nodes)]
        for node1, node2 in edges:
            adj[node1].add(node2)
            adj[node2].add(node1)
        
        # DFS 找出所有連通分量
        visited = set()
        components = []
        
        for start in range(num_nodes):
            if start in visited:
                continue
            
            component = set()
            stack = [start]
            
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                stack.extend(adj[node])
            
            components.append(component)
        
        return components
