"""
B+ Tree（B+树）
==========================================

【算法原理】
B+树是B树的变体，所有数据都存在叶子节点，
叶子节点之间用链表相连，便于范围查询。

【与B树的区别】
- B树：所有节点都存储数据
- B+树：内部节点只存索引，数据只在叶子
- B+树：叶子链表相连，支持范围查询更高效

【时间复杂度】
- 查找: O(log n)
- 插入: O(log n)
- 删除: O(log n)
- 范围查询: O(log n + k)

【应用场景】
- 数据库索引
- 文件系统索引
- 磁盘数据结构
"""

from typing import List, Optional, Tuple


class BPlusNode:
    """B+树节点"""
    def __init__(self, leaf: bool = False):
        # 是否为叶子节点
        self.leaf = leaf
        # 键（索引）
        self.keys = []
        # 子节点指针（非叶子）或数据指针（叶子）
        self.children = []
        # 指向下一个叶子（叶子节点用）
        self.next = None
        # 是否为根节点
        self.is_root = False


class BPlusTree:
    """
    B+树

    【参数】
    - degree: B+树的度（每个节点最多有degree个子节点）
    - 节点键数: degree-1 到 2*degree-1
    """

    def __init__(self, degree: int = 3):
        if degree < 2:
            raise ValueError("degree must be >= 2")
        self.degree = degree
        self.min_keys = degree - 1  # 最少键数（非根）
        self.max_keys = 2 * degree - 1  # 最大键数
        self.root = BPlusNode(leaf=True)
        self.root.is_root = True
        self.root.keys = []
        self.root.children = []  # 叶子节点用children存数据

    def search(self, key) -> Optional[any]:
        """查找key对应的数据"""
        return self._search(self.root, key)

    def _search(self, node: BPlusNode, key) -> Optional[any]:
        """递归查找"""
        i = 0
        # 找到第一个 >= key 的位置
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if node.leaf:
            # 叶子节点
            if i < len(node.keys) and node.keys[i] == key:
                return node.children[i]  # 返回数据
            return None
        else:
            # 非叶子节点，递归到子节点
            return self._search(node.children[i], key)

    def insert(self, key, value) -> None:
        """
        插入键值对

        【步骤】
        1. 查找合适的叶子节点
        2. 插入到叶子节点
        3. 如果叶子节点溢出，分裂
        4. 如果根节点溢出，树高度+1
        """
        root = self.root

        # 如果根节点已满，需要分裂
        if len(root.keys) == self.max_keys:
            # 创建新根
            new_root = BPlusNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0, self.root)
            self.root = new_root
            self.root.is_root = True

        self._insert_non_full(self.root, key, value)

    def _insert_non_full(self, node: BPlusNode, key, value) -> None:
        """向非满节点插入"""
        if node.leaf:
            # 叶子节点：直接插入
            i = len(node.keys) - 1
            # 找到插入位置（保持有序）
            while i >= 0 and node.keys[i] > key:
                i -= 1

            node.keys.insert(i + 1, key)
            node.children.insert(i + 1, value)
        else:
            # 非叶子节点
            i = len(node.keys) - 1
            while i >= 0 and node.keys[i] > key:
                i -= 1
            i += 1

            child = node.children[i]
            if len(child.keys) == self.max_keys:
                self._split_child(node, i, child)

                # 分裂后，中间键上移到node
                # 判断应该插到哪个子节点
                if key > node.keys[i]:
                    i += 1

            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: BPlusNode, index: int, child: BPlusNode) -> None:
        """
        分裂满子节点

        【分裂规则】
        - 度为d的B+树，每个节点最多2d-1个键
        - 分裂后：左节点d-1个键，右节点d个键
        - 中间键上移到父节点
        """
        new_child = BPlusNode(leaf=child.leaf)

        # 分裂点
        mid = self.degree - 1  # 中间键索引

        # 新节点获得右半部分键和数据
        new_child.keys = child.keys[mid + 1:]
        new_child.children = child.children[mid + 1:]

        # 原节点保留左半部分
        child.keys = child.keys[:mid]
        child.children = child.children[:mid]

        # 如果是叶子，新节点需要连接链表
        if child.leaf:
            new_child.next = child.next
            child.next = new_child

        # 中间键上移到父节点
        parent.keys.insert(index, child.keys.pop())

        # 子节点指针后移，插入新节点
        parent.children.insert(index + 1, new_child)

    def range_query(self, start_key, end_key) -> List[any]:
        """
        范围查询 [start_key, end_key]

        【优势】B+树叶子链表，范围查询只需：
        1. 找到起始叶子
        2. 沿链表遍历到结束
        """
        results = []

        # 找到起始叶子
        node = self.root
        while not node.leaf:
            i = 0
            while i < len(node.keys) and start_key > node.keys[i]:
                i += 1
            node = node.children[i]

        # 沿链表遍历
        while node is not None:
            for i, key in enumerate(node.keys):
                if key < start_key:
                    continue
                if key > end_key:
                    return results
                results.append(node.children[i])
            node = node.next

        return results

    def delete(self, key) -> bool:
        """删除键"""
        return self._delete(self.root, key)

    def _delete(self, node: BPlusNode, key) -> bool:
        """递归删除"""
        if node.leaf:
            if key in node.keys:
                idx = node.keys.index(key)
                node.keys.pop(idx)
                node.children.pop(idx)
                return True
            return False
        else:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1

            if i < len(node.keys) and node.keys[i] == key:
                # 找到要删除的键
                # 用后继节点替换
                successor = node.children[i + 1]
                # 找到后继节点的最左叶子
                while not successor.leaf:
                    successor = successor.children[0]
                # 用后继的键替换
                node.keys[i] = successor.keys[0]
                # 删除后继的键
                return self._delete(node.children[i + 1], successor.keys[0])
            else:
                return self._delete(node.children[i], key)

    def display(self) -> List[Tuple[int, List, List]]:
        """返回树的层级结构（用于调试）"""
        result = []

        def traverse(node: BPlusNode, level: int):
            result.append((level, node.keys,
                         ['data' if node.leaf else len(node.children)]))
            if not node.leaf:
                for child in node.children:
                    traverse(child, level + 1)

        traverse(self.root, 0)
        return result

    def count(self) -> int:
        """返回树的节点数"""
        def traverse(node: BPlusNode) -> int:
            if node.leaf:
                return len(node.keys)
            return sum(traverse(child) for child in node.children)

        return traverse(self.root)


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("B+树 - 测试")
    print("=" * 50)

    tree = BPlusTree(degree=3)

    # 测试插入
    print("\n【测试1】插入")
    data = [(5, "five"), (3, "three"), (7, "seven"),
            (1, "one"), (9, "nine"), (2, "two")]
    for k, v in data:
        tree.insert(k, v)
        print(f"  插入 ({k}, '{v}')")

    print(f"  树中键数: {tree.count()}")

    # 测试查找
    print("\n【测试2】精确查找")
    for k in [3, 5, 10]:
        result = tree.search(k)
        print(f"  查找 {k}: {result}")

    # 测试范围查询
    print("\n【测试3】范围查询 [2, 7]")
    results = tree.range_query(2, 7)
    print(f"  结果: {results}")

    # 测试删除
    print("\n【测试4】删除")
    tree.delete(5)
    print(f"  删除 5 后查找 5: {tree.search(5)}")
    print(f"  删除 5 后查找 7: {tree.search(7)}")

    # 测试树的遍历
    print("\n【测试5】树的层级结构")
    for level, keys, info in tree.display():
        print(f"  Level {level}: keys={keys}, info={info}")

    print("\n" + "=" * 50)
    print("B+树测试完成！")
    print("=" * 50)
