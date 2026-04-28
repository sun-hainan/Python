"""
Segment Tree（线段树）
==========================================

【算法原理】
线段树是一种二叉树结构，用于高效处理区间查询和更新。
每个节点代表一个区间[root, end]，存储该区间的聚合信息。

【时间复杂度】
- 构建: O(n)
- 区间查询: O(log n)
- 单点更新: O(log n)
- 区间更新: O(log n)（懒传播后可做到）

【空间复杂度】O(4n)

【应用场景】
- 区间求和/最小值/最大值
- 区间染色问题
- 区间合并问题
- 动态RMQ
"""

import math
from typing import List, Callable, Optional


class SegmentTree:
    """
    线段树

    【模板参数】
    - data: 原始数组
    - merge: 合并函数（如 min, max, sum, gcd）
    - default: 单位元（如 inf, 0, -inf）

    【存储方式】
    - 使用数组模拟树
    - 父节点索引 i -> 左子 2i, 右子 2i+1
    """

    def __init__(self, data: List, merge: Callable, default: any):
        """
        初始化线段树

        【参数】
        - data: 原始数组（1-indexed或0-indexed）
        - merge: 区间合并函数
        - default: 区间为空时的默认值
        """
        self.n = len(data)
        self.data = data
        self.merge = merge
        self.default = default

        # 树的大小（4n足够）
        self.size = 4 * self.n + 5
        self.tree = [default] * self.size

        # 构建
        if self.n > 0:
            self._build(1, 0, self.n - 1)

    def _build(self, node: int, start: int, end: int) -> None:
        """
        构建线段树（递归）

        【思路】
        - 如果区间只有一个元素，直接赋值
        - 否则递归构建左右子树，再合并
        """
        if start == end:
            # 叶子节点
            self.tree[node] = self.data[start]
        else:
            mid = (start + end) // 2
            left = node * 2
            right = node * 2 + 1

            # 递归构建左右子树
            self._build(left, start, mid)
            self._build(right, mid + 1, end)

            # 合并左右子树的区间信息
            self.tree[node] = self.merge(self.tree[left], self.tree[right])

    def query(self, query_start: int, query_end: int) -> any:
        """
        区间查询 [l, r]

        【思路】
        - 完全包含：返回节点值
        - 无交集：返回默认值
        - 部分交集：递归查询后合并
        """
        return self._query(1, 0, self.n - 1, query_start, query_end)

    def _query(self, node: int, start: int, end: int,
               query_start: int, query_end: int) -> any:
        """
        递归区间查询

        【情况分析】
        1. 查询区间完全覆盖当前节点区间 -> 直接返回
        2. 查询区间与当前节点无交集 -> 返回default
        3. 查询区间部分覆盖 -> 递归左右，取合并
        """
        # 情况1：完全覆盖
        if query_start <= start and end <= query_end:
            return self.tree[node]

        # 情况2：无交集
        if query_end < start or query_start > end:
            return self.default

        # 情况3：部分交集
        mid = (start + end) // 2
        left_result = self._query(node * 2, start, mid, query_start, query_end)
        right_result = self._query(node * 2 + 1, mid + 1, end,
                                  query_start, query_end)

        return self.merge(left_result, right_result)

    def update(self, index: int, value: any) -> None:
        """单点更新"""
        self._update(1, 0, self.n - 1, index, value)

    def _update(self, node: int, start: int, end: int,
                index: int, value: any) -> None:
        """递归单点更新"""
        if start == end:
            self.tree[node] = value
            self.data[start] = value
            return

        mid = (start + end) // 2
        if index <= mid:
            self._update(node * 2, start, mid, index, value)
        else:
            self._update(node * 2 + 1, mid + 1, end, index, value)

        self.tree[node] = self.merge(self.tree[node * 2], self.tree[node * 2 + 1])


# ========================================
# 懒传播线段树（支持区间更新）
# ========================================

class LazySegmentTree:
    """
    懒传播线段树

    【核心思想】
    - 对区间更新，不立即下推到叶子
    - 记录"懒标记"，下次访问时再下推
    - 大大提高区间更新效率
    """

    def __init__(self, data: List, merge: Callable, default: any):
        self.n = len(data)
        self.data = data
        self.merge = merge
        self.default = default

        self.size = 4 * self.n + 5
        self.tree = [default] * self.size
        self.lazy = [None] * self.size  # 懒标记

        if self.n > 0:
            self._build(1, 0, self.n - 1)

    def _build(self, node: int, start: int, end: int) -> None:
        if start == end:
            self.tree[node] = self.data[start]
        else:
            mid = (start + end) // 2
            self._build(node * 2, start, mid)
            self._build(node * 2 + 1, mid + 1, end)
            self.tree[node] = self.merge(self.tree[node * 2],
                                        self.tree[node * 2 + 1])

    def _push_down(self, node: int, start: int, end: int) -> None:
        """下推懒标记到子节点"""
        if self.lazy[node] is not None:
            mid = (start + end) // 2
            left, right = node * 2, node * 2 + 1

            # 应用到左子节点
            self._apply(left, self.lazy[node], start, mid)
            # 应用到右子节点
            self._apply(right, self.lazy[node], mid + 1, end)

            # 清除当前懒标记
            self.lazy[node] = None

    def _apply(self, node: int, value: any, start: int, end: int) -> None:
        """应用更新到节点"""
        self.tree[node] = self.merge(self.tree[node], value)
        self.lazy[node] = value if self.lazy[node] is None else self.merge(
            self.lazy[node], value)

    def range_update(self, update_start: int, update_end: int, value: any) -> None:
        """区间更新 [l, r]"""
        self._range_update(1, 0, self.n - 1, update_start, update_end, value)

    def _range_update(self, node: int, start: int, end: int,
                     update_start: int, update_end: int, value: any) -> None:
        """递归区间更新"""
        # 完全覆盖
        if update_start <= start and end <= update_end:
            self._apply(node, value, start, end)
            return

        # 下推懒标记
        self._push_down(node, start, end)

        mid = (start + end) // 2
        if update_start <= mid:
            self._range_update(node * 2, start, mid,
                             update_start, update_end, value)
        if update_end > mid:
            self._range_update(node * 2 + 1, mid + 1, end,
                             update_start, update_end, value)

        self.tree[node] = self.merge(self.tree[node * 2], self.tree[node * 2 + 1])

    def range_query(self, query_start: int, query_end: int) -> any:
        """区间查询 [l, r]"""
        return self._range_query(1, 0, self.n - 1, query_start, query_end)

    def _range_query(self, node: int, start: int, end: int,
                    query_start: int, query_end: int) -> any:
        """递归区间查询"""
        if query_start <= start and end <= query_end:
            return self.tree[node]

        self._push_down(node, start, end)

        mid = (start + end) // 2
        result = self.default

        if query_start <= mid:
            result = self.merge(result,
                self._range_query(node * 2, start, mid, query_start, query_end))
        if query_end > mid:
            result = self.merge(result,
                self._range_query(node * 2 + 1, mid + 1, end,
                                query_start, query_end))

        return result


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("线段树 - 测试")
    print("=" * 50)

    # 数据
    arr = [1, 3, 5, 7, 9, 11]

    # 区间求和线段树
    print("\n【测试1】区间求和线段树")
    seg_sum = SegmentTree(arr, merge=lambda a, b: a + b, default=0)
    print(f"  数组: {arr}")
    print(f"  查询 [1,3]: {seg_sum.query(1, 3)}")  # 3+5+7=15
    print(f"  查询 [0,5]: {seg_sum.query(0, 5)}")  # 36
    print(f"  查询 [2,2]: {seg_sum.query(2, 2)}")  # 5

    # 单点更新
    seg_sum.update(2, 10)
    print(f"  更新 arr[2]=10 后查询 [0,2]: {seg_sum.query(0, 2)}")

    # 区间最小值线段树
    print("\n【测试2】区间最小值线段树")
    seg_min = SegmentTree(arr, merge=lambda a, b: min(a, b), default=float('inf'))
    print(f"  数组: {arr}")
    print(f"  查询 [0,3]: {seg_min.query(0, 3)}")  # min(1,3,10,7)=1
    print(f"  查询 [2,5]: {seg_min.query(2, 5)}")  # min(10,7,9,11)=7

    # 懒传播线段树（区间更新）
    print("\n【测试3】懒传播线段树 - 区间加法")
    lazy_seg = LazySegmentTree(arr, merge=lambda a, b: a + b, default=0)
    print(f"  原数组: {arr}")

    # 区间 [1,4] 都加 10
    lazy_seg.range_update(1, 4, 10)
    print(f"  区间[1,4]加10后: {[lazy_seg.range_query(i,i) for i in range(6)]}")

    # 查询区间和
    print(f"  查询[0,5]和: {lazy_seg.range_query(0, 5)}")
    print(f"  查询[1,3]和: {lazy_seg.range_query(1, 3)}")

    # 区间更新为赋值操作（覆盖）
    print("\n【测试4】区间赋值")
    # 先重建（简化）
    lazy_seg2 = LazySegmentTree(arr[:], merge=lambda a, b: a + b, default=0)

    print(f"  原数组: {arr}")
    print(f"  注意：当前merge是加法，赋值需要特殊处理")

    print("\n" + "=" * 50)
    print("线段树测试完成！")
    print("=" * 50)
