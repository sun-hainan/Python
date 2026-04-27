# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / index_structures



本文件实现 index_structures 相关的算法功能。

"""



from typing import Optional, List, Tuple, Any, Callable

from dataclasses import dataclass

import bisect



@dataclass

class BPlusNode:

    """B+树节点"""

    is_leaf: bool = True          # 是否叶子节点

    keys: List[Any] = []          # 键列表

    children: List['BPlusNode'] = []  # 子节点指针（内部节点）

    values: List[Any] = []        # 值列表（叶子节点）

    next_leaf: Optional['BPlusNode'] = None  # 叶子节点链表指针

    parent: Optional['BPlusNode'] = None

    

    def __repr__(self):

        if self.is_leaf:

            return f"Leaf(keys={self.keys[:5]}...{len(self.keys)})"

        return f"Internal(keys={self.keys[:5]}...{len(self.keys)})"





class BPlusTree:

    """

    B+树实现

    所有数据存储在叶子节点，叶子节点之间有链表连接

    """

    

    def __init__(self, order: int = 4):

        self.order = order          # B+树的阶（每个节点最多有order个子节点）

        self.min_keys = (order - 1) // 2  # 最少键数

        self.root: Optional[BPlusNode] = None

        self.size = 0              # 键值对数量

    

    def insert(self, key: Any, value: Any):

        """插入键值对"""

        if self.root is None:

            self.root = BPlusNode(is_leaf=True)

            self.root.keys.append(key)

            self.root.values.append(value)

            self.size += 1

            return

        

        # 查找应该插入的叶子节点

        leaf = self._find_leaf(key)

        

        # 检查是否已存在键

        if key in leaf.keys:

            idx = leaf.keys.index(key)

            leaf.values[idx] = value

            return

        

        # 插入到叶子节点

        idx = bisect.bisect_left(leaf.keys, key)

        leaf.keys.insert(idx, key)

        leaf.values.insert(idx, value)

        self.size += 1

        

        # 如果叶子节点溢出，需要分裂

        if len(leaf.keys) > self.order:

            self._split_leaf(leaf)

    

    def _find_leaf(self, key: Any) -> BPlusNode:

        """查找包含键的叶子节点"""

        node = self.root

        while not node.is_leaf:

            idx = bisect.bisect_right(node.keys, key) - 1

            idx = max(0, min(idx, len(node.children) - 1))

            node = node.children[idx]

        return node

    

    def _split_leaf(self, leaf: BPlusNode):

        """分裂叶子节点"""

        mid = len(leaf.keys) // 2

        

        # 创建新叶子节点

        new_leaf = BPlusNode(is_leaf=True)

        new_leaf.keys = leaf.keys[mid:]

        new_leaf.values = leaf.values[mid:]

        new_leaf.next_leaf = leaf.next_leaf

        leaf.next_leaf = new_leaf

        

        # 更新原叶子节点

        leaf.keys = leaf.keys[:mid]

        leaf.values = leaf.values[:mid]

        

        # 如果叶子是根节点，需要创建新的根

        if leaf.parent is None:

            leaf.parent = BPlusNode(is_leaf=False)

            self.root = leaf.parent

            self.root.children.append(leaf)

        

        # 将分裂产生的键提升到父节点

        self._insert_into_parent(leaf, new_leaf.keys[0], new_leaf)

    

    def _insert_into_parent(self, left: BPlusNode, key: Any, right: BPlusNode):

        """将键和指针插入父节点"""

        parent = left.parent

        

        # 找到left在父节点中的位置

        idx = parent.children.index(left) if left in parent.children else 0

        

        parent.keys.insert(idx, key)

        parent.children.insert(idx + 1, right)

        right.parent = parent

        

        # 如果父节点溢出，分裂

        if len(parent.keys) > self.order:

            self._split_internal(parent)

    

    def _split_internal(self, node: BPlusNode):

        """分裂内部节点"""

        mid = len(node.keys) // 2

        promoted_key = node.keys[mid]

        

        new_node = BPlusNode(is_leaf=False)

        new_node.keys = node.keys[mid + 1:]

        new_node.children = node.children[mid + 1:]

        

        for child in new_node.children:

            child.parent = new_node

        

        node.keys = node.keys[:mid]

        node.children = node.children[:mid + 1]

        

        # 更新父节点

        if node.parent is None:

            node.parent = BPlusNode(is_leaf=False)

            self.root = node.parent

            self.root.children.append(node)

        

        self._insert_into_parent(node, promoted_key, new_node)

    

    def search(self, key: Any) -> Optional[Any]:

        """搜索键对应的值"""

        if self.root is None:

            return None

        

        leaf = self._find_leaf(key)

        

        idx = bisect.bisect_left(leaf.keys, key)

        if idx < len(leaf.keys) and leaf.keys[idx] == key:

            return leaf.values[idx]

        

        return None

    

    def range_search(self, start_key: Any, end_key: Any) -> List[Any]:

        """范围搜索"""

        results = []

        

        if self.root is None:

            return results

        

        # 找到起始叶子节点

        leaf = self._find_leaf(start_key)

        

        while leaf:

            for i, key in enumerate(leaf.keys):

                if start_key <= key <= end_key:

                    results.append(leaf.values[i])

                elif key > end_key:

                    return results

            

            leaf = leaf.next_leaf

        

        return results

    

    def delete(self, key: Any) -> bool:

        """删除键"""

        leaf = self._find_leaf(key)

        

        if key not in leaf.keys:

            return False

        

        idx = leaf.keys.index(key)

        leaf.keys.pop(idx)

        leaf.values.pop(idx)

        self.size -= 1

        

        # 如果叶子节点键数过少，需要合并或借用

        if len(leaf.keys) < self.min_keys and leaf.parent:

            self._rebalance_leaf(leaf)

        

        return True

    

    def _rebalance_leaf(self, leaf: BPlusNode):

        """重平衡叶子节点（借用或合并）"""

        # 简化处理：不做详细的合并/借用操作

        pass

    

    def inorder_traversal(self) -> List[Tuple[Any, Any]]:

        """中序遍历（按顺序返回所有键值对）"""

        results = []

        

        if self.root is None:

            return results

        

        # 找到最左叶子节点

        node = self.root

        while not node.is_leaf:

            node = node.children[0]

        

        # 遍历叶子节点链表

        while node:

            for k, v in zip(node.keys, node.values):

                results.append((k, v))

            node = node.next_leaf

        

        return results





class BlinkTree(BPlusTree):

    """

    Blink树 - B+树的变体，带有高指针

    特点：允许非递归查找，简化并发控制

    """

    

    def __init__(self, order: int = 4):

        super().__init__(order)

        self.high_key: Optional[Any] = None  # 树的最大键

    

    def _find_leaf_with_high(self, key: Any) -> Tuple[BPlusNode, bool]:

        """

        查找叶子节点，返回是否到达高指针

        高指针用于标识已超过所有键的搜索

        """

        node = self.root

        

        while not node.is_leaf:

            idx = bisect.bisect_right(node.keys, key) - 1

            

            # 高指针检查：key >= 所有键

            if idx == len(node.keys) - 1 and self.high_key and key >= self.high_key:

                return node.children[-1], True

            

            idx = max(0, min(idx, len(node.children) - 1))

            node = node.children[idx]

        

        return node, False





class SkipListIndex:

    """

    跳表索引

    平均O(log n)查找， 实现简单，并发友好

    """

    

    MAX_LEVEL = 16  # 最大层数

    

    @dataclass

    class Node:

        key: Any

        value: Any

        forward: List['SkipListIndex.Node']  # 每层的前向指针

    

    def __init__(self):

        self.header = self.Node(key=None, value=None, 

                               forward=[None] * (self.MAX_LEVEL + 1))

        self.level = 0  # 当前最大层数

        self.size = 0

    

    def _random_level(self) -> int:

        """随机层数（概率减半）"""

        level = 0

        import random

        while random.random() < 0.5 and level < self.MAX_LEVEL:

            level += 1

        return level

    

    def insert(self, key: Any, value: Any):

        """插入键值对"""

        update = [None] * (self.MAX_LEVEL + 1)

        node = self.header

        

        # 找到插入位置

        for i in range(self.level, -1, -1):

            while node.forward[i] and node.forward[i].key < key:

                node = node.forward[i]

            update[i] = node

        

        node = node.forward[0]

        

        if node and node.key == key:

            node.value = value

            return

        

        # 创建新节点

        new_level = self._random_level()

        

        if new_level > self.level:

            for i in range(self.level + 1, new_level + 1):

                update[i] = self.header

            self.level = new_level

        

        new_node = self.Node(key=key, value=value, 

                           forward=[None] * (new_level + 1))

        

        for i in range(new_level + 1):

            new_node.forward[i] = update[i].forward[i]

            update[i].forward[i] = new_node

        

        self.size += 1

    

    def search(self, key: Any) -> Optional[Any]:

        """搜索键"""

        node = self.header

        

        for i in range(self.level, -1, -1):

            while node.forward[i] and node.forward[i].key < key:

                node = node.forward[i]

        

        node = node.forward[0]

        

        if node and node.key == key:

            return node.value

        

        return None

    

    def delete(self, key: Any) -> bool:

        """删除键"""

        update = [None] * (self.MAX_LEVEL + 1)

        node = self.header

        

        for i in range(self.level, -1, -1):

            while node.forward[i] and node.forward[i].key < key:

                node = node.forward[i]

            update[i] = node

        

        node = node.forward[0]

        

        if node is None or node.key != key:

            return False

        

        for i in range(self.level + 1):

            if update[i].forward[i] == node:

                update[i].forward[i] = node.forward[i]

        

        self.size -= 1

        

        # 降低层数

        while self.level > 0 and self.header.forward[self.level] is None:

            self.level -= 1

        

        return True





@dataclass

class IndexEntry:

    """索引条目（用于稀疏/稠密索引）"""

    key: Any          # 索引键

    page_id: int      # 数据页ID

    offset: int = 0   # 页内偏移量





class SparseIndex:

    """

    稀疏索引

    只索引部分键值（如每个数据页的第一个键）

    节省空间，但查找可能需要扫描

    """

    

    def __init__(self):

        self.entries: List[IndexEntry] = []  # 有序索引条目

        self.indexed_ratio = 0.1  # 索引的键占总键的比例

    

    def build_index(self, data_keys: List[Any], page_func: Callable[[Any], int]):

        """

        构建稀疏索引

        data_keys: 所有数据键（有序）

        page_func: 键 -> 页ID 的映射函数

        """

        # 每隔N个键索引一个

        step = max(1, int(1 / self.indexed_ratio) if self.indexed_ratio > 0 else 10)

        

        for i in range(0, len(data_keys), step):

            key = data_keys[i]

            page_id = page_func(key)

            self.entries.append(IndexEntry(key=key, page_id=page_id))

    

    def search(self, key: Any) -> Optional[int]:

        """二分查找，找到可能包含key的页"""

        # 找到小于等于key的最大索引条目的页

        left, right = 0, len(self.entries) - 1

        result = None

        

        while left <= right:

            mid = (left + right) // 2

            

            if self.entries[mid].key <= key:

                result = self.entries[mid].page_id

                left = mid + 1

            else:

                right = mid - 1

        

        return result





class DenseIndex:

    """

    稠密索引

    每个键都有一个索引条目

    查找更精确，但占用更多空间

    """

    

    def __init__(self):

        self.entries: List[IndexEntry] = []

    

    def build_index(self, data_keys: List[Any], 

                    page_func: Callable[[Any], int], offset_func: Callable[[Any], int]):

        """

        构建稠密索引

        offset_func: 键 -> 页内偏移量的映射函数

        """

        for key in data_keys:

            page_id = page_func(key)

            offset = offset_func(key)

            self.entries.append(IndexEntry(key=key, page_id=page_id, offset=offset))

    

    def search(self, key: Any) -> Optional[Tuple[int, int]]:

        """精确查找，返回(页ID, 偏移量)"""

        left, right = 0, len(self.entries) - 1

        

        while left <= right:

            mid = (left + right) // 2

            

            if self.entries[mid].key == key:

                entry = self.entries[mid]

                return (entry.page_id, entry.offset)

            elif self.entries[mid].key < key:

                left = mid + 1

            else:

                right = mid - 1

        

        return None





if __name__ == "__main__":

    print("=" * 60)

    print("索引结构演示")

    print("=" * 60)

    

    # B+树测试

    print("\n--- B+树 ---")

    bpt = BPlusTree(order=4)

    

    for i in range(20):

        bpt.insert(i, f"value_{i}")

    

    print(f"B+树大小: {bpt.size}")

    print(f"搜索 key=10: {bpt.search(10)}")

    print(f"范围搜索 [5, 15]: {bpt.range_search(5, 15)}")

    print(f"中序遍历前5个: {bpt.inorder_traversal()[:5]}")

    

    # 跳表测试

    print("\n--- 跳表索引 ---")

    sl = SkipListIndex()

    

    for i in range(20):

        sl.insert(i, f"value_{i}")

    

    print(f"跳表大小: {sl.size}")

    print(f"搜索 key=15: {sl.search(15)}")

    print(f"删除 key=15: {sl.delete(15)}")

    print(f"删除后搜索: {sl.search(15)}")

    

    # 稀疏索引 vs 稠密索引

    print("\n--- 稀疏索引 vs 稠密索引 ---")

    

    data_keys = list(range(0, 1000, 10))  # 每10个值一个页

    

    sparse_idx = SparseIndex()

    sparse_idx.indexed_ratio = 0.1

    sparse_idx.build_index(data_keys, lambda k: k // 100)

    

    dense_idx = DenseIndex()

    dense_idx.build_index(data_keys, 

                         lambda k: k // 10,

                         lambda k: 0)

    

    print(f"稀疏索引条目数: {len(sparse_idx.entries)}")

    print(f"稠密索引条目数: {len(dense_idx.entries)}")

    print(f"稀疏索引查找 key=550: page_id={sparse_idx.search(550)}")

    print(f"稠密索引查找 key=550: {dense_idx.search(550)}")

