"""
Treap（树堆）
==========================================

【算法原理】
Treap = BST + Heap
- 键值key满足BST性质（左<根<右）
- 优先级priority满足堆性质（父节点的优先级>子节点）
- 优先级随机生成，保证期望平衡

【时间复杂度】
- 期望 O(log n) 的插入、删除、查找

【空间复杂度】O(n)

【应用场景】
- 快速插入/删除的有序容器
- 实现动态集合
- 作为更复杂数据结构的基础
"""

import random
from typing import Optional, List


class TreapNode:
    """Treap节点"""
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.priority = random.random()
        self.left = None
        self.right = None


class Treap:
    """
    Treap（随机化BST）

    【核心操作】
    - 插入：按key找到位置，按priority旋转维护堆性质
    - 删除：旋转到叶子删除
    - 查找：普通BST查找
    - 旋转：左旋/右旋
    """

    def __init__(self):
        self.root = None

    # ==================== 旋转操作 ====================

    def _right_rotate(self, y: TreapNode) -> TreapNode:
        """
        右旋

            y               x
           / \             / \
          x   T3   -->    T1   y
         / \                 / \
        T1  T2               T2  T3
        """
        x = y.left
        y.left = x.right
        x.right = y
        return x

    def _left_rotate(self, x: TreapNode) -> TreapNode:
        """
        左旋

          x                 y
         / \               / \
        T1  y     -->     x   T3
           / \           / \
          T2  T3        T1  T2
        """
        y = x.right
        x.right = y.left
        y.left = x
        return y

    # ==================== 插入 ====================

    def insert(self, key, value=None) -> None:
        """插入键值对"""
        if self.root is None:
            self.root = TreapNode(key, value)
        else:
            self.root = self._insert(self.root, key, value)

    def _insert(self, node: TreapNode, key, value) -> TreapNode:
        """
        递归插入

        【情况】
        1. key < node.key: 插入左子树，可能触发右旋
        2. key > node.key: 插入右子树，可能触发左旋
        3. key == node.key: 更新value
        """
        if node is None:
            return TreapNode(key, value)

        if key < node.key:
            node.left = self._insert(node.left, key, value)
            # 如果左子节点优先级更高（右旋）
            if node.left and node.left.priority > node.priority:
                node = self._right_rotate(node)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
            if node.right and node.right.priority > node.priority:
                node = self._left_rotate(node)
        else:
            # key已存在，更新value
            node.value = value

        return node

    def insert_iterative(self, key, value=None) -> None:
        """迭代插入（更高效）"""
        if self.root is None:
            self.root = TreapNode(key, value)
            return

        path = []  # 记录路径
        node = self.root

        # 找到插入位置
        while True:
            path.append(node)
            if key < node.key:
                if node.left is None:
                    node.left = TreapNode(key, value)
                    break
                node = node.left
            elif key > node.key:
                if node.right is None:
                    node.right = TreapNode(key, value)
                    break
                node = node.right
            else:
                node.value = value
                return

        # 从插入点向上回溯，维护堆性质
        for i in range(len(path) - 1, -1, -1):
            child = path[i].left if i == len(path) - 1 else (
                path[i + 1] if path[i].left == path[i + 1] else None)

            if child is None:
                child = path[i].right if i == len(path) - 1 else None

            parent = path[i - 1] if i > 0 else None

            # 比较优先级，决定是否旋转
            if path[i].left and path[i].left.priority > path[i].priority:
                new_subtree = self._right_rotate(path[i])
            elif path[i].right and path[i].right.priority > path[i].priority:
                new_subtree = self._left_rotate(path[i])
            else:
                continue

            if parent is None:
                self.root = new_subtree
            elif parent.left == path[i]:
                parent.left = new_subtree
            else:
                parent.right = new_subtree

    # ==================== 查找 ====================

    def search(self, key) -> Optional[any]:
        """查找键对应的值"""
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return node.value
        return None

    def contains(self, key) -> bool:
        """判断键是否存在"""
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return True
        return False

    # ==================== 删除 ====================

    def delete(self, key) -> bool:
        """删除键"""
        self.root = self._delete(self.root, key)
        return True

    def _delete(self, node: TreapNode, key) -> Optional[TreapNode]:
        """
        递归删除

        【删除策略】
        - 找到要删除的节点
        - 如果是叶子，直接删除
        - 如果只有一个子节点，用子节点替换
        - 如果有两个子节点，旋转优先级低的子节点上来，直到变成上述情况
        """
        if node is None:
            return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # 找到要删除的节点
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            else:
                # 两个子节点都存在，旋转优先级更高的上来
                if node.left.priority > node.right.priority:
                    node = self._right_rotate(node)
                    node.right = self._delete(node.right, key)
                else:
                    node = self._left_rotate(node)
                    node.left = self._delete(node.left, key)

        return node

    # ==================== 中序遍历 ====================

    def inorder(self) -> List:
        """中序遍历（获得有序序列）"""
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node: TreapNode, result: List) -> None:
        if node:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)

    # ==================== 其他操作 ====================

    def min(self) -> Optional[TreapNode]:
        """找最小键"""
        node = self.root
        while node and node.left:
            node = node.left
        return node

    def max(self) -> Optional[TreapNode]:
        """找最大键"""
        node = self.root
        while node and node.right:
            node = node.right
        return node

    def floor(self, key) -> Optional[TreapNode]:
        """找小于等于key的最大节点"""
        result = None
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                result = node
                node = node.right
            else:
                return node
        return result

    def ceil(self, key) -> Optional[TreapNode]:
        """找大于等于key的最小节点"""
        result = None
        node = self.root
        while node:
            if key > node.key:
                node = node.right
            elif key < node.key:
                result = node
                node = node.left
            else:
                return node
        return result

    def rank(self, key) -> int:
        """返回key的排名（从小到大）第k小"""
        return self._rank(self.root, key)

    def _rank(self, node: TreapNode, key) -> int:
        """计算key的排名"""
        if node is None:
            return 0
        if key < node.key:
            return self._rank(node.left, key)
        elif key > node.key:
            left_size = self._size(node.left)
            return left_size + 1 + self._rank(node.right, key)
        else:
            return self._size(node.left) + 1

    def _size(self, node: TreapNode) -> int:
        """计算子树大小"""
        if node is None:
            return 0
        return 1 + self._size(node.left) + self._size(node.right)


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Treap（树堆） - 测试")
    print("=" * 50)

    random.seed(42)  # 固定随机种子以便复现

    treap = Treap()

    # 测试插入
    print("\n【测试1】插入")
    keys = [5, 3, 7, 2, 4, 6, 8]
    for k in keys:
        treap.insert(k, f"value_{k}")
        print(f"  插入 {k}")

    # 中序遍历（有序）
    print(f"\n  中序遍历: {treap.inorder()}")

    # 测试查找
    print("\n【测试2】查找")
    for k in [4, 10]:
        value = treap.search(k)
        print(f"  查找 {k}: {value}")

    # 测试contains
    print("\n【测试3】contains")
    for k in [3, 9]:
        print(f"  contains({k}): {treap.contains(k)}")

    # 测试min/max
    print("\n【测试4】min/max")
    min_node = treap.min()
    max_node = treap.max()
    print(f"  min: ({min_node.key}, {min_node.value})")
    print(f"  max: ({max_node.key}, {max_node.value})")

    # 测试floor/ceil
    print("\n【测试5】floor/ceil")
    for k in [5, 4, 9]:
        floor_node = treap.floor(k)
        ceil_node = treap.ceil(k)
        print(f"  floor({k}): {floor_node.key if floor_node else None}")
        print(f"  ceil({k}): {ceil_node.key if ceil_node else None}")

    # 测试rank
    print("\n【测试6】排名")
    for k in [3, 5, 8]:
        print(f"  rank({k}): {treap.rank(k)}")

    # 测试删除
    print("\n【测试7】删除")
    for k in [3, 5]:
        treap.delete(k)
        print(f"  删除 {k}: 中序 = {[k for k,v in treap.inorder()]}")
        print(f"    contains({k}): {treap.contains(k)}")

    print("\n" + "=" * 50)
    print("Treap测试完成！")
    print("=" * 50)
