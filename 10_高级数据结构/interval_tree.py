"""
Interval Tree（区间树）
==========================================

【算法原理】
用于高效查询与给定区间重叠的所有区间。
基于红黑树，按区间起点排序。

【时间复杂度】
- 插入: O(log n)
- 查询: O(log n + k) k为重叠区间数

【应用场景】
- 会议室预约
- CPU调度
- 内存管理
"""

from typing import List, Optional


class IntervalNode:
    def __init__(self, interval):
        self.interval = interval  # (low, high)
        self.max_high = interval[1]
        self.left = None
        self.right = None
        self.color = 'red'


class IntervalTree:
    """区间树"""

    def __init__(self):
        self.root = None

    def insert(self, interval):
        """插入区间"""
        node = IntervalNode(interval)
        self.root = self._insert(self.root, node)
        self.root.color = 'black'

    def _insert(self, root, node):
        if not root:
            return node
        if interval[0] < root.interval[0]:
            root.left = self._insert(root.left, node)
        else:
            root.right = self._insert(root.right, node)
        self._update_max(root)
        return root

    def _update_max(self, node):
        if node:
            node.max_high = max(node.interval[1],
                             node.left.max_high if node.left else 0,
                             node.right.max_high if node.right else 0)

    def overlap(self, interval, node_interval):
        """检查两个区间是否重叠"""
        return interval[0] <= node_interval[1] and node_interval[0] <= interval[1]

    def query(self, interval) -> List:
        """查询与给定区间重叠的所有区间"""
        results = []
        self._query(self.root, interval, results)
        return results

    def _query(self, node, interval, results):
        if not node:
            return
        if self.overlap(interval, node.interval):
            results.append(node.interval)
        if node.left and node.left.max_high >= interval[0]:
            self._query(node.left, interval, results)
        self._query(node.right, interval, results)


if __name__ == "__main__":
    print("Interval Tree测试")
    tree = IntervalTree()
    intervals = [(1, 5), (3, 8), (6, 10), (15, 20), (18, 25)]
    for i in intervals:
        tree.insert(i)
    results = tree.query((4, 9))
    print(f"与[4,9]重叠: {results}")
