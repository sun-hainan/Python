# -*- coding: utf-8 -*-
"""
算法实现：数据库算法 / btree_index

本文件实现 btree_index 相关的算法功能。
"""

from typing import List, Optional, Tuple, Any
from dataclasses import dataclass
import bisect


@dataclass
class BPlusNode:
    """B+树节点"""
    is_leaf: bool  # 是否为叶子节点
    keys: List[int] = None  # 关键字列表（排序）
    values: List[Any] = None  # 值列表（叶子节点）
    children: List['BPlusNode'] = None  # 子节点列表（内部节点）
    next: Optional['BPlusNode'] = None  # 叶子节点链表后继
    
    def __post_init__(self):
        if self.keys is None:
            self.keys = []
        if self.values is None:
            self.values = []
        if self.children is None:
            self.children = []


class BPlusTree:
    """
    B+树实现
    
    参数:
        degree: 阶数（每个节点最多degree个子节点）
    """
    
    def __init__(self, degree: int = 4):
        if degree < 3:
            raise ValueError("Degree must be at least 3")
        self.degree = degree  # 阶数
        self.min_keys = (degree - 1) // 2  # 最少关键字数
        self.max_keys = degree - 1  # 最多关键字数
        self.root: Optional[BPlusNode] = None
    
    def _create_node(self, is_leaf: bool = False) -> BPlusNode:
        """创建新节点"""
        return BPlusNode(is_leaf=is_leaf)
    
    def search(self, key: int) -> Optional[Any]:
        """
        搜索关键字，返回对应的值
        
        时间复杂度: O(log n)
        """
        if self.root is None:
            return None
        return self._search_node(self.root, key)
    
    def _search_node(self, node: BPlusNode, key: int) -> Optional[Any]:
        """在节点中搜索"""
        # 在keys中二分查找
        idx = bisect.bisect_left(node.keys, key)
        
        if node.is_leaf:
            # 叶子节点：检查是否找到
            if idx < len(node.keys) and node.keys[idx] == key:
                return node.values[idx]
            return None
        else:
            # 内部节点：根据索引进入子节点
            if idx >= len(node.keys):
                idx = len(node.keys) - 1
            if idx < 0:
                idx = 0
            return self._search_node(node.children[idx], key)
    
    def insert(self, key: int, value: Any) -> None:
        """
        插入关键字-值对
        
        时间复杂度: O(log n)
        """
        if self.root is None:
            self.root = self._create_node(is_leaf=True)
            self.root.keys.append(key)
            self.root.values.append(value)
            return
        
        # 查找插入位置
        result = self._search_and_split(self.root, key, value)
        
        if result is not None:
            # 根节点分裂，创建新根
            left, up_key, right = result
            new_root = self._create_node(is_leaf=False)
            new_root.keys = [up_key]
            new_root.children = [left, right]
            self.root = new_root
    
    def _search_and_split(self, node: BPlusNode, key: int, value: Any) -> Optional[Tuple[BPlusNode, int, BPlusNode]]:
        """
        递归插入，如果节点满则分裂
        返回: None（无需分裂）或 (左节点, 上浮关键字, 右节点)
        """
        if node.is_leaf:
            # 叶子节点：直接插入
            idx = bisect.bisect_left(node.keys, key)
            
            # 检查是否已存在
            if idx < len(node.keys) and node.keys[idx] == key:
                node.values[idx] = value
                return None
            
            # 插入
            node.keys.insert(idx, key)
            node.values.insert(idx, value)
            
            # 检查是否需要分裂
            if len(node.keys) > self.max_keys:
                return self._split_leaf_node(node)
            return None
        else:
            # 内部节点：递归到子节点
            idx = bisect.bisect_left(node.keys, key)
            if idx >= len(node.keys):
                idx = len(node.keys) - 1
            if idx < 0:
                idx = 0
            
            result = self._search_and_split(node.children[idx], key, value)
            
            if result is None:
                return None
            
            left, up_key, right = result
            
            # 插入上浮关键字和子节点
            node.keys.insert(idx, up_key)
            node.children.insert(idx + 1, right)
            
            # 检查是否需要分裂
            if len(node.keys) > self.max_keys:
                return self._split_internal_node(node)
            
            return None
    
    def _split_leaf_node(self, node: BPlusNode) -> Tuple[BPlusNode, int, BPlusNode]:
        """分裂叶子节点"""
        mid = len(node.keys) // 2
        
        # 创建右节点
        right = self._create_node(is_leaf=True)
        right.keys = node.keys[mid:]
        right.values = node.values[mid:]
        right.next = node.next
        
        # 更新左节点
        left = self._create_node(is_leaf=True)
        left.keys = node.keys[:mid]
        left.values = node.values[:mid]
        left.next = right
        
        # 上浮关键字
        up_key = right.keys[0]
        
        return left, up_key, right
    
    def _split_internal_node(self, node: BPlusNode) -> Tuple[BPlusNode, int, BPlusNode]:
        """分裂内部节点"""
        mid = len(node.keys) // 2
        
        # 上浮关键字
        up_key = node.keys[mid]
        
        # 创建左右节点
        left = self._create_node(is_leaf=False)
        right = self._create_node(is_leaf=False)
        
        left.keys = node.keys[:mid]
        left.children = node.children[:mid + 1]
        
        right.keys = node.keys[mid + 1:]
        right.children = node.children[mid + 1:]
        
        return left, up_key, right
    
    def range_search(self, start_key: int, end_key: int) -> List[Any]:
        """
        范围查询
        
        时间复杂度: O(log n + k)，k为结果数量
        """
        results = []
        
        if self.root is None:
            return results
        
        # 找到起始叶子节点
        leaf = self._find_leaf(self.root, start_key)
        
        # 遍历叶子节点链表
        while leaf is not None:
            for i, key in enumerate(leaf.keys):
                if key >= start_key and key <= end_key:
                    results.append(leaf.values[i])
                elif key > end_key:
                    return results
            leaf = leaf.next
        
        return results
    
    def _find_leaf(self, node: BPlusNode, key: int) -> BPlusNode:
        """找到包含关键字的叶子节点"""
        if node.is_leaf:
            return node
        
        idx = bisect.bisect_left(node.keys, key)
        if idx >= len(node.keys):
            idx = len(node.keys) - 1
        if idx < 0:
            idx = 0
        
        return self._find_leaf(node.children[idx], key)
    
    def delete(self, key: int) -> bool:
        """
        删除关键字
        
        时间复杂度: O(log n)
        """
        if self.root is None:
            return False
        
        result = self._delete_node(self.root, key)
        
        if result is None:
            return False
        
        # 如果根变成叶子节点，更新root
        if len(self.root.keys) == 0 and not self.root.is_leaf:
            self.root = self.root.children[0] if self.root.children else None
        
        return True
    
    def _delete_node(self, node: BPlusNode, key: int) -> Optional[BPlusNode]:
        """递归删除"""
        idx = bisect.bisect_left(node.keys, key)
        
        if node.is_leaf:
            # 叶子节点删除
            if idx < len(node.keys) and node.keys[idx] == key:
                node.keys.pop(idx)
                node.values.pop(idx)
                return node
            return None
        else:
            # 内部节点
            if idx < len(node.keys) and node.keys[idx] == key:
                # 删除内部关键字，需要特殊处理（用后继前驱替换）
                # 简化：找后继关键字
                successor = self._find_min_key(node.children[idx + 1])
                node.keys[idx] = successor
                return self._delete_node(node.children[idx + 1], successor)
            else:
                target_child = idx if idx == 0 else idx - 1
                return self._delete_node(node.children[target_child], key)
    
    def _find_min_key(self, node: BPlusNode) -> int:
        """找最小关键字"""
        if node.is_leaf:
            return node.keys[0]
        return self._find_min_key(node.children[0])
    
    def get_height(self) -> int:
        """获取树高度"""
        if self.root is None:
            return 0
        return self._get_height(self.root, 0)
    
    def _get_height(self, node: BPlusNode, depth: int) -> int:
        """递归计算高度"""
        if node.is_leaf:
            return depth + 1
        return self._get_height(node.children[0], depth + 1)
    
    def get_stats(self) -> dict:
        """获取树统计信息"""
        if self.root is None:
            return {'n_keys': 0, 'height': 0, 'n_nodes': 0}
        
        stats = {'n_nodes': 0}
        
        def traverse(node: BPlusNode):
            stats['n_nodes'] += 1
            if not node.is_leaf:
                for child in node.children:
                    traverse(child)
        
        traverse(self.root)
        
        # 统计关键字数
        n_keys = sum(len(node.keys) for node in [self.root] if hasattr(node, 'keys'))
        
        return {
            'n_keys': self._count_keys(self.root),
            'height': self.get_height(),
            'n_nodes': stats['n_nodes'],
            'degree': self.degree
        }
    
    def _count_keys(self, node: BPlusNode) -> int:
        """统计关键字总数"""
        if node.is_leaf:
            return len(node.keys)
        return len(node.keys) + sum(self._count_keys(c) for c in node.children)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("B+树索引测试")
    print("=" * 50)
    
    # 创建B+树
    tree = BPlusTree(degree=4)
    
    # 测试插入
    print("\n--- 插入测试 ---")
    
    test_data = [
        (5, "value5"), (10, "value10"), (3, "value3"),
        (7, "value7"), (1, "value1"), (8, "value8"),
        (12, "value12"), (15, "value15"), (20, "value20"),
        (6, "value6"), (9, "value9"), (11, "value11")
    ]
    
    for key, value in test_data:
        tree.insert(key, value)
        print(f"插入 ({key}, {value}), 树高度={tree.get_height()}")
    
    # 测试搜索
    print("\n--- 搜索测试 ---")
    
    search_keys = [7, 10, 15, 100]
    for key in search_keys:
        result = tree.search(key)
        print(f"搜索 key={key}: {'找到 ' + str(result) if result else '未找到'}")
    
    # 测试范围查询
    print("\n--- 范围查询测试 ---")
    
    range_results = tree.range_search(5, 12)
    print(f"范围查询 [5, 12]: {range_results}")
    
    # 统计信息
    print("\n--- 统计信息 ---")
    
    stats = tree.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 大量插入测试
    print("\n--- 大量插入测试 ---")
    
    import random
    import time
    
    random.seed(42)
    
    large_tree = BPlusTree(degree=32)
    n_insert = 10000
    
    start = time.time()
    for i in range(n_insert):
        key = random.randint(1, 1000000)
        large_tree.insert(key, f"value_{i}")
    insert_time = time.time() - start
    
    print(f"插入 {n_insert} 条记录耗时: {insert_time:.3f}秒")
    print(f"树高度: {large_tree.get_height()}")
    print(f"节点数: {large_tree.get_stats()['n_nodes']}")
    
    # 搜索性能测试
    start = time.time()
    for _ in range(1000):
        key = random.randint(1, 1000000)
        large_tree.search(key)
    search_time = time.time() - start
    
    print(f"1000次搜索耗时: {search_time:.3f}秒")
    
    # 范围查询测试
    start = time.time()
    for _ in range(100):
        start_key = random.randint(1, 500000)
        end_key = start_key + 1000
        large_tree.range_search(start_key, end_key)
    range_time = time.time() - start
    
    print(f"100次范围查询耗时: {range_time:.3f}秒")
    
    # 删除测试
    print("\n--- 删除测试 ---")
    
    small_tree = BPlusTree(degree=4)
    for i in range(1, 11):
        small_tree.insert(i * 10, f"v{i}")
    
    print(f"删除前: {[small_tree.search(i*10) for i in range(1, 11)]}")
    
    for i in [30, 50, 10]:
        small_tree.delete(i)
        print(f"删除 key={i} 后搜索: {small_tree.search(i)}")
