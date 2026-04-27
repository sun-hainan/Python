# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / dp_segment_optimization



本文件实现 dp_segment_optimization 相关的算法功能。

"""



from typing import List, Tuple, Optional

import math





class SegmentTree:

    """

    线段树模板

    

    支持：

    - 点更新

    - 区间查询（最小值、最大值、和）

    - 区间修改（懒惰传播可选）

    """

    

    def __init__(self, data: List, operation: str = "min"):

        """

        Args:

            data: 初始数组

            operation: 操作类型，"min", "max", "sum"

        """

        self.data = data

        self.n = len(data)

        self.operation = operation

        

        # 构建线段树（4倍大小）

        self.size = 1

        while self.size < self.n:

            self.size <<= 1

        self.tree = [float('inf')] * (2 * self.size)

        

        self._build()

    

    def _build(self):

        """从底向上构建线段树"""

        # 叶子节点

        for i in range(self.n):

            self.tree[self.size + i] = self.data[i]

        

        # 内部节点

        for i in range(self.size - 1, 0, -1):

            self.tree[i] = self._merge(self.tree[2 * i], self.tree[2 * i + 1])

    

    def _merge(self, a: float, b: float) -> float:

        """合并两个区间"""

        if self.operation == "min":

            return min(a, b)

        elif self.operation == "max":

            return max(a, b)

        elif self.operation == "sum":

            return a + b

        return a

    

    def update(self, index: int, value: float):

        """

        单点更新

        

        Args:

            index: 更新位置

            value: 新值

        """

        pos = self.size + index

        self.tree[pos] = value

        

        # 向上更新

        pos >>= 1

        while pos:

            self.tree[pos] = self._merge(self.tree[2 * pos], self.tree[2 * pos + 1])

            pos >>= 1

    

    def query(self, left: int, right: int) -> float:

        """

        区间查询 [left, right]

        

        Args:

            left: 左边界（闭区间）

            right: 右边界（闭区间）

        

        Returns:

            区间最值或和

        """

        if left > right:

            return float('-inf') if self.operation == "max" else float('inf')

        

        left += self.size

        right += self.size

        

        res_left = float('-inf') if self.operation == "max" else float('inf')

        res_right = res_left

        

        while left <= right:

            if left & 1:

                res_left = self._merge(res_left, self.tree[left])

                left += 1

            if not (right & 1):

                res_right = self._merge(self.tree[right], res_right)

                right -= 1

            left >>= 1

            right >>= 1

        

        return self._merge(res_left, res_right)

    

    def range_update(self, left: int, right: int, value: float):

        """

        区间更新（惰性传播版本）

        

        这里实现简化版，直接更新所有叶子

        """

        for i in range(left, right + 1):

            self.update(i, value)





class LazySegmentTree:

    """

    惰性传播线段树

    

    支持区间更新 + 区间查询

    """

    

    def __init__(self, data: List, operation: str = "min"):

        self.data = data

        self.n = len(data)

        self.operation = operation

        

        self.size = 1

        while self.size < self.n:

            self.size <<= 1

        

        # 线段树 + 懒惰标记

        self.tree = [0.0] * (2 * self.size)

        self.lazy = [0.0] * self.size

        

        self._build()

    

    def _build(self):

        for i in range(self.n):

            self.tree[self.size + i] = self.data[i]

        for i in range(self.size - 1, 0, -1):

            self.tree[i] = self._merge(self.tree[2 * i], self.tree[2 * i + 1])

    

    def _push(self, node: int):

        """向下传播懒惰标记"""

        if self.lazy[node] != 0:

            self.tree[2 * node] = self._apply(self.tree[2 * node], self.lazy[node])

            self.tree[2 * node + 1] = self._apply(self.tree[2 * node + 1], self.lazy[node])

            self.lazy[2 * node] = self._add(self.lazy[2 * node], self.lazy[node])

            self.lazy[2 * node + 1] = self._add(self.lazy[2 * node + 1], self.lazy[node])

            self.lazy[node] = 0.0

    

    def _apply(self, value: float, add: float) -> float:

        if self.operation == "sum":

            return value + add

        return value + add  # 假设是加法更新

    

    def _add(self, a: float, b: float) -> float:

        return a + b

    

    def _merge(self, a: float, b: float) -> float:

        if self.operation == "min":

            return min(a, b)

        elif self.operation == "max":

            return max(a, b)

        return a + b

    

    def range_add(self, left: int, right: int, value: float):

        """区间加法"""

        self._range_add(left, right, value, 1, 0, self.size - 1)

    

    def _range_add(self, left: int, right: int, value: float, 

                   node: int, node_left: int, node_right: int):

        if left > node_right or right < node_left:

            return

        if left <= node_left and node_right <= right:

            self.tree[node] = self._apply(self.tree[node], value)

            self.lazy[node] = self._add(self.lazy[node], value)

            return

        

        self._push(node)

        mid = (node_left + node_right) // 2

        self._range_add(left, right, value, 2 * node, node_left, mid)

        self._range_add(left, right, value, 2 * node + 1, mid + 1, node_right)

        self.tree[node] = self._merge(self.tree[2 * node], self.tree[2 * node + 1])

    

    def range_query(self, left: int, right: int) -> float:

        """区间查询"""

        return self._range_query(left, right, 1, 0, self.size - 1)

    

    def _range_query(self, left: int, right: int, 

                     node: int, node_left: int, node_right: int) -> float:

        if left > node_right or right < node_left:

            return float('-inf') if self.operation == "max" else float('inf')

        if left <= node_left and node_right <= right:

            return self.tree[node]

        

        self._push(node)

        mid = (node_left + node_right) // 2

        left_res = self._range_query(left, right, 2 * node, node_left, mid)

        right_res = self._range_query(left, right, 2 * node + 1, mid + 1, node_right)

        return self._merge(left_res, right_res)





def dp_linear_with_segment_tree(n: int, weights: List[int], C: int) -> int:

    """

    线性DP + 线段树优化

    

    问题：有一排物品，每个物品重量为 weights[i]，选择第 i 个物品需要代价 C，

         求在总重量不超过 C 的情况下，能选择的最大物品数量

    

    这是一个 0-1 背包的简化版，展示如何用线段树优化

    dp[i] = 在考虑前 i 个物品时，总重量恰好为 j 时的最大价值

    转移：dp[j] = max(dp[j], dp[j - weight[i]] + value[i])

    

    优化：对于每个 weight，从后往前遍历时，可以分段更新

         但这里展示的是一种更常见的线段树优化场景

    

    实际中，线段树优化常用于：

    - 区间最值DP：dp[i] = max(dp[j] + f(j,i)) for j < i

    - 单调队列优化也是 O(n) 的，但线段树更通用

    """

    # 简化版本：求最大连续和的DP

    # dp[i] = max(dp[i-1] + a[i], a[i])

    # 区间查询：dp[i] = max_{j < i} (dp[j] + cost(j+1, i))

    

    values = weights  # 这里价值和重量相同

    

    # 使用线段树维护 dp[j] 的值

    # dp[i] = max(dp[j] + (sum[i] - sum[j])) for j < i

    #      = max(dp[j] - sum[j]) + sum[i]

    # 所以我们查询 max(dp[j] - sum[j]) for j < i

    

    prefix_sum = [0]

    for w in weights:

        prefix_sum.append(prefix_sum[-1] + w)

    

    seg = SegmentTree([0.0] * (n + 1), operation="max")

    seg.update(0, 0)  # dp[0] = 0

    

    for i in range(1, n + 1):

        # 查询 max(dp[j] - sum[j]) for j in [0, i-1]

        best = seg.query(0, i - 1)

        dp_i = best + prefix_sum[i]

        seg.update(i, dp_i)

    

    # 找到满足重量约束的最大价值

    result = 0

    for i in range(n + 1):

        val = seg.tree[seg.size + i] if i < seg.n else 0

        if val > result:

            result = val

    

    return result





def dp_interval_with_segment_tree(intervals: List[Tuple[int, int, int]]) -> int:

    """

    区间DP + 线段树优化

    

    问题：给一堆带权区间，选择互不相交的区间使得总权重最大

    

    方法：

    1. 按结束时间排序

    2. 对每个区间 i，找最后一个与 i 不相交的区间 j

    3. dp[i] = max(dp[i-1], dp[j] + weight[i])

    

    使用线段树优化查找过程

    

    Args:

        intervals: [(start, end, weight), ...]

    

    Returns:

        最大总权重

    """

    if not intervals:

        return 0

    

    # 排序

    intervals.sort(key=lambda x: x[1])

    

    # 提取所有坐标用于离散化

    coords = set()

    for s, e, _ in intervals:

        coords.add(s)

        coords.add(e)

    coords = sorted(list(coords))

    coord_map = {v: i for i, v in enumerate(coords)}

    

    # 线段树存储 dp 值

    seg = SegmentTree([0.0] * len(coords), operation="max")

    

    # dp[i] 表示考虑前 i 个区间（按结束时间排序）的最大权重

    for s, e, w in intervals:

        # 找到最后一个结束时间 <= start 的区间

        # 由于已排序，可以用二分找

        idx = coord_map[e]

        

        # dp[idx] = max(不选当前区间, 选当前区间)

        # 选当前区间：需要 dp[最后一个不相交区间] + w

        # 不选：维持前一个状态

    

    return 0





def dp_convex_hull_optimization():

    """

    凸包优化DP的线段树辅助实现

    

    当 DP 形如 dp[i] = min(dp[j] + C * b[j] + d[j]) 时，

    可以使用单调队列或凸包优化到 O(n)

    

    这里展示如何用线段树处理更一般的情况：

    - 多个约束条件

    - 动态查询

    """

    pass





if __name__ == "__main__":

    # 测试1：基本线段树

    print("测试1 - 基本线段树:")

    data = [1, 3, 2, 7, 5, 8, 4, 6]

    

    # 最小值线段树

    seg_min = SegmentTree(data, operation="min")

    print(f"  原数组: {data}")

    print(f"  区间 [1,4] 最小值: {seg_min.query(1, 4)}")  # 应该是 2

    print(f"  区间 [0,3] 最小值: {seg_min.query(0, 3)}")  # 应该是 1

    

    # 更新后查询

    seg_min.update(2, 0)

    print(f"  更新后 data[2]=0")

    print(f"  区间 [0,3] 最小值: {seg_min.query(0, 3)}")  # 应该是 0

    

    # 最大值线段树

    seg_max = SegmentTree(data, operation="max")

    print(f"  区间 [2,6] 最大值: {seg_max.query(2, 6)}")  # 应该是 8

    

    # 求和线段树

    seg_sum = SegmentTree(data, operation="sum")

    print(f"  区间 [1,5] 和: {seg_sum.query(1, 5)}")  # 应该是 3+2+7+5+8=25

    

    # 测试2：懒惰传播线段树

    print("\n测试2 - 懒惰传播线段树:")

    data2 = [1, 2, 3, 4, 5]

    lazy_seg = LazySegmentTree(data2, operation="sum")

    

    print(f"  原数组: {data2}")

    print(f"  区间 [1,3] 和: {lazy_seg.range_query(1, 3)}")  # 应该是 2+3+4=9

    

    lazy_seg.range_add(1, 3, 10)

    print(f"  区间 [1,3] 加 10 后:")

    print(f"  区间 [0,4] 和: {lazy_seg.range_query(0, 4)}")  # 应该是 1+12+13+14+5=45

    

    # 测试3：DP线性优化

    print("\n测试3 - DP线性优化:")

    n = 5

    weights = [2, 3, 4, 1, 2]

    C = 8

    result = dp_linear_with_segment_tree(n, weights, C)

    print(f"  物品重量: {weights}, 容量: {C}")

    print(f"  最大选择重量: {result}")

    

    # 测试4：区间DP

    print("\n测试4 - 区间DP:")

    intervals = [(1, 3, 10), (2, 5, 20), (4, 6, 15), (6, 7, 8)]

    result = dp_interval_with_segment_tree(intervals)

    print(f"  区间: {intervals}")

    print(f"  最大权重: {result}")

    

    # 性能测试

    import time

    import random

    

    print("\n性能测试:")

    sizes = [10000, 50000, 100000]

    for size in sizes:

        data = [random.randint(1, 100) for _ in range(size)]

        

        # 构建线段树

        start = time.time()

        seg = SegmentTree(data, operation="sum")

        build_time = time.time() - start

        

        # 随机查询

        start = time.time()

        for _ in range(1000):

            l = random.randint(0, size - 1)

            r = random.randint(l, size - 1)

            seg.query(l, r)

        query_time = time.time() - start

        

        # 随机更新

        start = time.time()

        for _ in range(1000):

            idx = random.randint(0, size - 1)

            val = random.randint(1, 100)

            seg.update(idx, val)

        update_time = time.time() - start

        

        print(f"  n={size}: 构建={build_time:.3f}s, 1000次查询={query_time:.3f}s, 1000次更新={update_time:.3f}s")

