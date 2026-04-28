"""
Leftist Heap（左倾堆）
==========================================

【原理】
 leftist性质：左子树的零路径长度 ≥ 右子树
 使得合并操作O(log n)

【时间复杂度】
- 合并: O(log n)
- 插入: O(log n)
- 查找min: O(1)
"""

from typing import Optional


class LeftistNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.npl = 0  # 零路径长度


class LeftistHeap:
    """左倾堆"""

    def __init__(self):
        self.root = None

    def merge(self, h1, h2):
        """合并两个左倾堆"""
        if not h1:
            return h2
        if not h2:
            return h1
        if h1.key > h2.key:
            h1, h2 = h2, h1
        h1.right = self.merge(h1.right, h2)
        if not h1.left or h1.left.npl < h1.right.npl:
            h1.left, h1.right = h1.right, h1.left
        h1.npl = (h1.right.npl if h1.right else 0) + 1
        return h1

    def insert(self, key):
        """插入"""
        node = LeftistNode(key)
        self.root = self.merge(self.root, node)

    def find_min(self):
        """找最小"""
        return self.root.key if self.root else None

    def delete_min(self):
        """删除最小"""
        if not self.root:
            return None
        min_val = self.root.key
        self.root = self.merge(self.root.left, self.root.right)
        return min_val


if __name__ == "__main__":
    print("Leftist Heap测试")
    heap = LeftistHeap()
    for x in [5, 3, 8, 1, 9, 2]:
        heap.insert(x)
    print(f"min: {heap.find_min()}")
    print(f"delete_min: {heap.delete_min()}")
    print(f"min after: {heap.find_min()}")
