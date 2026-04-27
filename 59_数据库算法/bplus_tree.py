# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / bplus_tree



本文件实现 bplus_tree 相关的算法功能。

"""



from typing import List, Optional, Tuple, Generic, TypeVar

from dataclasses import dataclass



T = TypeVar('T')





@dataclass

class BPlusTreeNode:

    """B+树节点"""

    keys: List[int]                    # 键列表（有序）

    is_leaf: bool                      # 是否为叶子节点

    n: int                             # 当前键的数量

    order: int                         # B+树的阶



    # 链表指针（仅叶子节点使用）

    next_leaf: Optional['BPlusTreeNode'] = None





@dataclass

class BPlusTreeLeafNode(BPlusTreeNode):

    """B+树叶子节点"""

    values: List[T] = None              # 值列表

    next_leaf: Optional['BPlusTreeLeafNode'] = None



    def __post_init__(self):

        if self.values is None:

            self.values = []

        self.is_leaf = True





class BPlusTree:

    """B+树实现"""



    def __init__(self, order: int = 3):

        """

        初始化B+树

        

        Args:

            order: 阶数，每个节点最多有order个子节点

                  叶子节点最多存储order-1个值

        """

        self.order = order

        self.root: BPlusTreeNode = BPlusTreeLeafNode(order=order)

        self.size = 0                   # 总键值对数

        self._leaf_head: Optional[BPlusTreeLeafNode] = None  # 叶子链表头



    def search(self, key: int) -> Optional[List[T]]:

        """

        搜索键对应的所有值

        

        Args:

            key: 搜索的键

            

        Returns:

            值列表（一个键可能对应多个值）

        """

        leaf = self._find_leaf(key)

        if leaf is None:

            return None

        

        for i in range(leaf.n):

            if leaf.keys[i] == key:

                return leaf.values[i]

        

        return None



    def _find_leaf(self, key: int) -> Optional[BPlusTreeLeafNode]:

        """找到键应该所在的叶子节点"""

        if self.root is None:

            return None

        

        current = self.root

        

        while not isinstance(current, BPlusTreeLeafNode):

            i = 0

            while i < current.n and key >= current.keys[i]:

                i += 1

            current = current.children[i]  # type: ignore

        

        return current



    def insert(self, key: int, value: T):

        """

        插入键值对

        

        Args:

            key: 键

            value: 值

        """

        leaf = self._find_leaf(key)

        

        # 检查键是否已存在

        for i in range(leaf.n):

            if leaf.keys[i] == key:

                # 键已存在，追加到值列表

                leaf.values[i].append(value)  # type: ignore

                return

        

        # 叶子节点未满，直接插入

        if leaf.n < self.order - 1:

            self._insert_into_leaf(leaf, key, [value])

        else:

            # 叶子节点已满，需要分裂

            self._insert_into_leaf_with_split(leaf, key, [value])



        self.size += 1



    def _insert_into_leaf(self, leaf: BPlusTreeLeafNode, key: int, value: List[T]):

        """插入到叶子节点（不分裂）"""

        i = leaf.n - 1

        

        # 找到插入位置

        while i >= 0 and key < leaf.keys[i]:

            i -= 1

        

        leaf.keys.insert(i + 1, key)

        leaf.values.insert(i + 1, value)

        leaf.n += 1



    def _insert_into_leaf_with_split(self, leaf: BPlusTreeLeafNode, key: int, value: List[T]):

        """

        插入到叶子节点并分裂

        

        Args:

            leaf: 叶子节点（已满）

            key: 要插入的键

            value: 要插入的值

        """

        # 创建新叶子节点

        new_leaf = BPlusTreeLeafNode(order=self.order)

        

        # 临时合并所有键值对并排序

        all_keys = leaf.keys + [key]

        all_values = leaf.values + [value]

        

        # 按键排序

        combined = list(zip(all_keys, all_values))

        combined.sort(key=lambda x: x[0])

        all_keys = [c[0] for c in combined]

        all_values = [c[1] for c in combined]

        

        # 分裂点

        split_point = (self.order - 1) // 2

        

        # 更新原叶子节点

        leaf.keys = all_keys[:split_point]

        leaf.values = all_values[:split_point]

        leaf.n = len(leaf.keys)

        

        # 初始化新叶子节点

        new_leaf.keys = all_keys[split_point:]

        new_leaf.values = all_values[split_point:]

        new_leaf.n = len(new_leaf.keys)

        

        # 更新链表指针

        new_leaf.next_leaf = leaf.next_leaf

        leaf.next_leaf = new_leaf

        

        # 如果是根节点，需要创建新的内部节点

        if leaf == self.root:  # type: ignore

            new_root = BPlusTreeNode(keys=[new_leaf.keys[0]], is_leaf=False, n=1, order=self.order)

            new_root.children = [leaf, new_leaf]

            self.root = new_root  # type: ignore

        else:

            # 父节点需要更新

            self._insert_into_parent(leaf, new_leaf.keys[0], new_leaf)



    def _insert_into_parent(self, left: BPlusTreeNode, key: int, right: BPlusTreeNode):

        """

        向父节点插入键和指针

        

        Args:

            left: 左子节点

            key: 要插入的键（right的第一个键）

            right: 右子节点

        """

        parent = self._find_parent(self.root, left)  # type: ignore

        

        if parent is None:

            # 需要创建新的根节点

            new_root = BPlusTreeNode(keys=[key], is_leaf=False, n=1, order=self.order)

            new_root.children = [left, right]

            self.root = new_root

            return

        

        # 检查父节点是否有空间

        if parent.n < self.order - 1:

            self._insert_into_parent_node(parent, key, right)

        else:

            # 父节点已满，需要分裂

            self._split_parent(parent, key, right)



    def _find_parent(self, current: BPlusTreeNode, target: BPlusTreeNode) -> Optional[BPlusTreeNode]:

        """找到target节点的父节点"""

        if current.is_leaf:

            return None

        

        for child in current.children:

            if child == target:

                return current

            result = self._find_parent(child, target)

            if result is not None:

                return result

        

        return None



    def _insert_into_parent_node(self, parent: BPlusTreeNode, key: int, right: BPlusTreeNode):

        """向父节点内部插入键（不分裂）"""

        i = parent.n - 1

        while i >= 0 and key < parent.keys[i]:

            i -= 1

        i += 1

        

        parent.keys.insert(i, key)

        parent.children.insert(i + 1, right)

        parent.n += 1



    def _split_parent(self, parent: BPlusTreeNode, key: int, right: BPlusTreeNode):

        """

        分裂已满的父节点

        """

        # 模拟创建临时数组

        temp_keys = parent.keys[:]

        temp_children = parent.children[:]

        

        # 找到插入位置

        i = 0

        while i < len(temp_keys) and key > temp_keys[i]:

            i += 1

        

        temp_keys.insert(i, key)

        temp_children.insert(i + 1, right)

        

        split_point = len(temp_keys) // 2

        

        # 左半部分保留

        left_keys = temp_keys[:split_point]

        left_children = temp_children[:split_point + 1]

        

        # 右半部分

        right_keys_temp = temp_keys[split_point:]

        right_children = temp_children[split_point + 1:]

        

        mid_key = left_keys.pop()

        

        # 创建分裂后的节点

        parent.keys = left_keys

        parent.children = left_children

        parent.n = len(parent.keys)

        

        new_node = BPlusTreeNode(keys=right_keys_temp, is_leaf=False, n=len(right_keys_temp), order=self.order)

        new_node.children = right_children

        

        # 如果父节点是根

        if parent == self.root:

            new_root = BPlusTreeNode(keys=[mid_key], is_leaf=False, n=1, order=self.order)

            new_root.children = [parent, new_node]

            self.root = new_root

        else:

            self._insert_into_parent(parent, mid_key, new_node)



    def delete(self, key: int) -> bool:

        """

        删除键

        

        Args:

            key: 要删除的键

            

        Returns:

            是否成功删除

        """

        leaf = self._find_leaf(key)

        if leaf is None:

            return False

        

        for i in range(leaf.n):

            if leaf.keys[i] == key:

                # 找到键，删除

                leaf.keys.pop(i)

                leaf.values.pop(i)  # type: ignore

                leaf.n -= 1

                self.size -= 1

                

                # 如果叶子节点键数量不足，需要重新平衡

                if leaf.n < (self.order - 1) // 2 and leaf != self.root:

                    self._rebalance_leaf(leaf)

                

                return True

        

        return False



    def _rebalance_leaf(self, leaf: BPlusTreeLeafNode):

        """重新平衡叶子节点"""

        # 找到父节点

        parent = self._find_parent(self.root, leaf)

        if parent is None:

            return

        

        # 找到leaf在父节点中的位置

        idx = 0

        for i, child in enumerate(parent.children):

            if child == leaf:

                idx = i

                break

        

        # 尝试从左兄弟借

        if idx > 0:

            left_sibling = parent.children[idx - 1]

            if left_sibling.n > (self.order - 1) // 2:

                # 借一个键

                leaf.keys.insert(0, left_sibling.keys.pop())

                leaf.values.insert(0, left_sibling.values.pop())  # type: ignore

                left_sibling.n -= 1

                leaf.n += 1

                

                # 更新父节点的键

                parent.keys[idx - 1] = leaf.keys[0]

                return

        

        # 尝试从右兄弟借

        if idx < parent.n:

            right_sibling = parent.children[idx + 1]

            if right_sibling.n > (self.order - 1) // 2:

                # 借一个键

                leaf.keys.append(right_sibling.keys.pop(0))

                leaf.values.append(right_sibling.values.pop(0))  # type: ignore

                right_sibling.n -= 1

                leaf.n += 1

                

                # 更新父节点的键

                parent.keys[idx] = right_sibling.keys[0]

                return

        

        # 无法借，需要合并

        if idx > 0:

            self._merge_leaves(parent, idx - 1)

        else:

            self._merge_leaves(parent, idx)



    def _merge_leaves(self, parent: BPlusTreeNode, idx: int):

        """合并两个叶子节点"""

        left = parent.children[idx]

        right = parent.children[idx + 1]

        

        # 左叶子追加右叶子的键值

        left.keys.extend(right.keys)

        left.values.extend(right.values)  # type: ignore

        left.n = len(left.keys)

        

        # 更新链表

        left.next_leaf = right.next_leaf  # type: ignore

        

        # 从父节点删除

        parent.keys.pop(idx)

        parent.children.pop(idx + 1)

        parent.n -= 1



    def range_query(self, low: int, high: int) -> List[Tuple[int, T]]:

        """

        范围查询（利用叶子节点链表高效实现）

        

        Args:

            low: 下界

            high: 上界

            

        Returns:

            范围内的所有 (key, value) 对

        """

        results = []

        

        # 找到起始叶子节点

        leaf = self._find_leaf(low)

        

        while leaf is not None:

            for i in range(leaf.n):

                if leaf.keys[i] >= low:

                    if leaf.keys[i] <= high:

                        # 注意：值可能是一个列表

                        for v in leaf.values[i]:

                            results.append((leaf.keys[i], v))

                    elif leaf.keys[i] > high:

                        return results

            

            leaf = leaf.next_leaf

        

        return results



    def traverse_leaves(self) -> List[Tuple[int, T]]:

        """

        遍历所有叶子节点（利用链表）

        

        Returns:

            所有键值对

        """

        results = []

        leaf = self._find_leftmost_leaf()

        

        while leaf is not None:

            for i in range(leaf.n):

                for v in leaf.values[i]:

                    results.append((leaf.keys[i], v))

            leaf = leaf.next_leaf

        

        return results



    def _find_leftmost_leaf(self) -> Optional[BPlusTreeLeafNode]:

        """找到最左边的叶子节点"""

        if self.root is None:

            return None

        

        current = self.root

        while not isinstance(current, BPlusTreeLeafNode):

            current = current.children[0]  # type: ignore

        

        return current





# ==================== 测试代码 ====================

if __name__ == "__main__":

    print("=" * 60)

    print("B+树索引测试")

    print("=" * 60)



    # 创建一棵3阶B+树

    btree = BPlusTree(order=3)

    

    # 插入测试

    print("\n--- 插入测试 ---")

    test_data = [

        (10, "Alice"),

        (20, "Bob"),

        (5, "Charlie"),

        (15, "David"),

        (25, "Eve"),

        (30, "Frank"),

        (7, "Grace"),

        (35, "Heidi"),

        (40, "Ivan"),

        (50, "Judy"),

    ]

    

    for key, value in test_data:

        btree.insert(key, value)

    

    print(f"插入完成，总共 {btree.size} 个键值对")

    

    # 遍历（利用链表）

    print(f"\n有序遍历: {btree.traverse_leaves()}")



    # 搜索测试

    print("\n--- 搜索测试 ---")

    search_keys = [15, 25, 100]

    for key in search_keys:

        result = btree.search(key)

        if result:

            print(f"  搜索 {key}: {result}")

        else:

            print(f"  搜索 {key}: 未找到")



    # 范围查询（高效）

    print("\n--- 范围查询 [10, 30] ---")

    results = btree.range_query(10, 30)

    for key, value in results:

        print(f"  {key}: '{value}'")



    # 删除测试

    print("\n--- 删除测试 ---")

    delete_keys = [15, 25, 10]

    for key in delete_keys:

        result = btree.delete(key)

        status = "成功" if result else "失败"

        print(f"  删除 {key}: {status}, 剩余 {btree.size} 个")

    

    print(f"\n删除后遍历: {btree.traverse_leaves()}")



    # 性能对比演示

    print("\n--- B+树 vs B树 范围查询对比 ---")

    print("  B+树: O(log N + K) - 利用叶子链表，只需定位起点后顺序扫描")

    print("  B树:  O(log N + K) - 需要在每个节点递归查找")

    print("  实际B+树更快，因为减少了树的遍历次数")



    print("\n" + "=" * 60)

    print("复杂度: 查找/插入/删除 O(log_m N)，范围查询 O(log N + K)")

    print("=" * 60)

