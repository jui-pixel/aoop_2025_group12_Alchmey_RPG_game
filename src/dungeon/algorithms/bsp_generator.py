# src/dungeon/algorithms/bsp_generator.py
"""
BSP (Binary Space Partitioning) 生成器
提供獨立的 BSP 空間分割算法
"""
import random
from typing import Optional, Tuple
from ..bsp_node import BSPNode
from ..config.dungeon_config import DungeonConfig


class BSPGenerator:
    """
    BSP 空間分割生成器
    
    使用二元空間分割算法將空間遞歸分割成更小的區域，
    用於生成地牢房間的布局結構。
    """
    
    def __init__(self, config: DungeonConfig):
        """
        初始化 BSP 生成器
        
        Args:
            config: 地牢配置
        """
        self.config = config
    
    def generate(self, width: int, height: int) -> BSPNode:
        """
        生成 BSP 樹
        
        Args:
            width: 空間寬度
            height: 空間高度
        
        Returns:
            BSP 樹的根節點
        """
        root = BSPNode(0, 0, width, height)
        self._split_recursive(root, 0)
        return root
    
    def _split_recursive(self, node: BSPNode, depth: int) -> None:
        """
        遞歸分割 BSP 節點
        
        Args:
            node: 要分割的節點
            depth: 當前深度
        """
        # 檢查是否應該停止分割
        if self._should_stop_splitting(node, depth):
            return
        
        # 選擇分割方向
        split_direction = self._choose_split_direction(node)
        if not split_direction:
            return
        
        # 執行分割
        self._perform_split(node, split_direction)
        
        # 遞歸處理子節點
        if node.left:
            self._split_recursive(node.left, depth + 1)
        if node.right:
            self._split_recursive(node.right, depth + 1)
    
    def _should_stop_splitting(self, node: BSPNode, depth: int) -> bool:
        """
        判斷是否應該停止分割
        
        Args:
            node: 當前節點
            depth: 當前深度
        
        Returns:
            是否應該停止分割
        """
        # 達到最大深度
        if depth >= self.config.max_split_depth:
            return True
        
        # 剩餘空間不足以再分割
        min_size = self.config.min_split_size * 2
        if node.width < min_size and node.height < min_size:
            return True
        
        return False
    
    def _choose_split_direction(self, node: BSPNode) -> Optional[str]:
        """
        選擇分割方向
        
        使用加權隨機選擇，偏向於分割較長的邊，
        以產生更均勻的分割結果。
        
        Args:
            node: 要分割的節點
        
        Returns:
            'vertical' 或 'horizontal'，如果無法分割則返回 None
        """
        min_size = self.config.min_split_size * 2
        
        can_split_horizontally = node.width >= min_size
        can_split_vertically = node.height >= min_size
        
        if not (can_split_horizontally or can_split_vertically):
            return None
        
        # 計算權重（較長的邊有更高的權重）
        w, h = node.width, node.height
        total = w * w + h * h
        vertical_weight = w * w / total
        horizontal_weight = h * h / total
        
        possible_directions = []
        weights = []
        
        if can_split_horizontally:
            possible_directions.append("vertical")
            weights.append(vertical_weight)
        
        if can_split_vertically:
            possible_directions.append("horizontal")
            weights.append(horizontal_weight)
        
        return random.choices(possible_directions, weights=weights)[0]
    
    def _perform_split(self, node: BSPNode, direction: str) -> None:
        """
        執行分割操作
        
        Args:
            node: 要分割的節點
            direction: 分割方向 ('vertical' 或 'horizontal')
        """
        min_size = self.config.min_split_size
        
        if direction == "vertical":
            # 垂直分割（沿 X 軸切割）
            split_x = random.randint(min_size, int(node.width - min_size))
            node.left = BSPNode(node.x, node.y, split_x, node.height)
            node.right = BSPNode(node.x + split_x, node.y, node.width - split_x, node.height)
        else:
            # 水平分割（沿 Y 軸切割）
            split_y = random.randint(min_size, int(node.height - min_size))
            node.left = BSPNode(node.x, node.y, node.width, split_y)
            node.right = BSPNode(node.x, node.y + split_y, node.width, node.height - split_y)
    
    def collect_leaf_nodes(self, root: BSPNode) -> list[BSPNode]:
        """
        收集所有葉節點
        
        Args:
            root: BSP 樹的根節點
        
        Returns:
            所有葉節點的列表
        """
        leaves = []
        self._collect_leaves_recursive(root, leaves)
        return leaves
    
    def _collect_leaves_recursive(self, node: BSPNode, leaves: list[BSPNode]) -> None:
        """
        遞歸收集葉節點
        
        Args:
            node: 當前節點
            leaves: 葉節點列表
        """
        if node.left is None and node.right is None:
            # 這是葉節點
            leaves.append(node)
        else:
            if node.left:
                self._collect_leaves_recursive(node.left, leaves)
            if node.right:
                self._collect_leaves_recursive(node.right, leaves)
    
    def get_tree_depth(self, root: BSPNode) -> int:
        """
        獲取 BSP 樹的深度
        
        Args:
            root: BSP 樹的根節點
        
        Returns:
            樹的深度
        """
        if root.left is None and root.right is None:
            return 0
        
        left_depth = self.get_tree_depth(root.left) if root.left else 0
        right_depth = self.get_tree_depth(root.right) if root.right else 0
        
        return 1 + max(left_depth, right_depth)
    
    def get_node_count(self, root: BSPNode) -> Tuple[int, int]:
        """
        獲取節點數量
        
        Args:
            root: BSP 樹的根節點
        
        Returns:
            (總節點數, 葉節點數)
        """
        total = 1
        leaves = 0
        
        if root.left is None and root.right is None:
            leaves = 1
        else:
            if root.left:
                left_total, left_leaves = self.get_node_count(root.left)
                total += left_total
                leaves += left_leaves
            if root.right:
                right_total, right_leaves = self.get_node_count(root.right)
                total += right_total
                leaves += right_leaves
        
        return total, leaves
