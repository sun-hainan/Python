"""
Pairing Heap（配对堆）
==========================================

【原理】
简化的堆结构，比Fibonacci堆更简单但性能接近。
支持O(1)合并，摊销O(log n)。

【时间复杂度】
- 合并: O(1) 摊销
- 插入: O(1) 摊销
- 删除min: O(log n) 摊销

【应用场景】
- 图算法（Prim/Dijkstra）
- 优先队列实现
"""


class PairingNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.next = None
        self.prev = None


class PairingHeap:
    """配对堆"""

    def __init__(self):
        self.root = None

    def merge(self, h1, h2):
        """合并两个堆"""
        if not h1:
            return h2
        if not h2:
            return h1
        if h1.key < h2.key:
            h1.next = h2
            h2.prev = h1
            return h1
        else:
            h2.next = h1
            h1.prev = h2
            return h2

    def insert(self, key):
        """插入"""
        node = PairingNode(key)
        self.root = self.merge(self.root, node)
        return node

    def find_min(self):
        """找最小"""
        return self.root.key if self.root else None

    def delete_min(self):
        """删除最小"""
        if not self.root:
            return None
        min_val = self.root.key
        self.root = self._merge_pairs(self.root.left)
        return min_val

    def _merge_pairs(self, head):
        """合并兄弟对"""
        if not head:
            return None
        if not head.next:
            return head

        first = head
        second = head.next
        rest = second.next

        first.next = second.next = None
        merged = self.merge(first, second)

        return self.merge(merged, self._merge_pairs(rest))


if __name__ == "__main__":
    print("Pairing Heap测试")
    heap = PairingHeap()
    for x in [5, 3, 8, 1, 9, 2, 7]:
        heap.insert(x)
    print(f"min: {heap.find_min()}")
    print(f"delete_min: {heap.delete_min()}")
    print(f"min after: {heap.find_min()}")
