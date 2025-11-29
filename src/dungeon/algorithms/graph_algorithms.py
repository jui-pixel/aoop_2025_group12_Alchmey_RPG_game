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
                       ratio: float) -> List[Tuple[int, int]]:
        """
        添加額外邊以增加連通性
        
        Args:
            mst_edges: MST 邊列表
            all_edges: 所有可能的邊
            ratio: 額外邊的比例（0.0-1.0）
        
        Returns:
            包含 MST 和額外邊的邊列表
        """
        if ratio <= 0.0:
            return mst_edges
        
        # 將 MST 邊轉換為集合以便快速查找
        mst_set = set(mst_edges)
        mst_set.update((b, a) for a, b in mst_edges)  # 添加反向邊
        
        # 找出非 MST 邊
        non_mst_edges = [
            (node1, node2) for node1, node2, weight in all_edges
            if (node1, node2) not in mst_set
        ]
        
        # 計算要添加的邊數量
        num_extra = int(len(non_mst_edges) * ratio)
        
        # 隨機選擇額外邊
        if num_extra > 0 and non_mst_edges:
            extra_edges = random.sample(non_mst_edges, min(num_extra, len(non_mst_edges)))
            return mst_edges + extra_edges
        
        return mst_edges
    
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
