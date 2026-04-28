"""
Sparse Table（稀疏表）
==========================================

【算法原理】
预处理O(n log n)，查询O(1)的区间数据结构。
利用幂次表存储区间的合并结果，支持静态RMQ（区间最小/最大值）。

【时间复杂度】
- 构建: O(n log n)
- 查询: O(1)

【空间复杂度】O(n log n)

【限制】仅支持满足幂等性的操作（如min, max, gcd）

【应用场景】
- 静态区间最小值/最大值查询
- 静态RMQ问题
- 区间gcd/lcm查询
"""

import math
from typing import List, Callable


class SparseTable:
    """
    稀疏表

    【核心思想】
    - st[k][i] = 从位置i开始，长度为2^k的区间的合并结果
    - 查询[l, r]: 取k = floor(log2(r-l+1))
      答案 = merge(st[k][l], st[k][r-2^k+1])
    """

    def __init__(self, data: List, merge: Callable):
        """
        初始化并构建稀疏表

        【参数】
        - data: 输入数组
        - merge: 合并函数（必须满足幂等性，如min, max, gcd）
        """
        self.data = data
        self.n = len(data)
        self.merge = merge

        # log2预处理
        self.log = [0] * (self.n + 1)
        for i in range(2, self.n + 1):
            self.log[i] = self.log[i // 2] + 1

        # 最大层数
        self.k_max = self.log[self.n] + 1

        # 构建稀疏表
        # st[k][i] = 位置i开始，长度2^k的区间
        self.st = [[0] * self.n for _ in range(self.k_max)]

        # 第0层：长度为1的区间
        for i in range(self.n):
            self.st[0][i] = data[i]

        # 第k层：从第0层递推
        k = 1
        while (1 << k) <= self.n:
            for i in range(self.n - (1 << k) + 1):
                # st[k][i] = merge(st[k-1][i], st[k-1][i+2^(k-1)])
                self.st[k][i] = self.merge(
                    self.st[k - 1][i],
                    self.st[k - 1][i + (1 << (k - 1))]
                )
            k += 1

    def query(self, left: int, right: int) -> any:
        """
        区间查询 [left, right]

        【原理】
        - k = floor(log2(right - left + 1))
        - 区间长度 2^k <= (right-left+1)
        - 两段可能有重叠，但取merge后仍是正确答案（幂等性保证）
        """
        if left > right:
            raise ValueError("left > right")
        if left < 0 or right >= self.n:
            raise IndexError("Index out of range")

        k = self.log[right - left + 1]
        return self.merge(
            self.st[k][left],
            self.st[k][right - (1 << k) + 1]
        )


class RMQSparseTable(SparseTable):
    """区间最小值查询的稀疏表（便捷类）"""

    def __init__(self, data: List):
        super().__init__(data, merge=min)

    def query_min(self, left: int, right: int) -> int:
        """区间最小值"""
        return self.query(left, right)

    def query_max(self, left: int, right: int) -> int:
        """区间最大值（需要重新构建）"""
        st_max = SparseTable(self.data, merge=max)
        return st_max.query(left, right)


class GCDSparseTable(SparseTable):
    """区间GCD查询的稀疏表"""

    def __init__(self, data: List):
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        super().__init__(data, merge=gcd)

    def query_gcd(self, left: int, right: int) -> int:
        """区间GCD"""
        return self.query(left, right)


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Sparse Table（稀疏表） - 测试")
    print("=" * 50)

    # 测试数据
    arr = [1, 3, 5, 7, 9, 11, 2, 4, 6, 8]
    print(f"\n数组: {arr}")

    # 测试区间最小值
    print("\n【测试1】区间最小值")
    rmq = RMQSparseTable(arr)
    tests = [(0, 3), (2, 6), (5, 9), (0, 9)]
    for l, r in tests:
        print(f"  RMQ({l},{r}) = {rmq.query_min(l, r)}")

    # 测试区间最大值
    print("\n【测试2】区间最大值")
    for l, r in tests:
        print(f"  max({l},{r}) = {rmq.query_max(l, r)}")

    # 测试GCD
    print("\n【测试3】区间GCD")
    gcd_st = GCDSparseTable(arr)
    for l, r in tests:
        print(f"  GCD({l},{r}) = {gcd_st.query_gcd(l, r)}")

    # 测试手动构建的稀疏表
    print("\n【测试4】手动构建稀疏表（自定义merge）")
    custom_st = SparseTable(arr, merge=lambda a, b: a + b)
    for l, r in [(0, 2), (3, 7)]:
        print(f"  Sum({l},{r}) = {custom_st.query(l, r)}")

    # 对比SparseTable查询和暴力查询
    print("\n【测试5】正确性验证")
    import random
    random.seed(42)
    errors = 0
    for _ in range(1000):
        l = random.randint(0, len(arr) - 1)
        r = random.randint(l, len(arr) - 1)
        expected = min(arr[l:r + 1])
        got = rmq.query_min(l, r)
        if expected != got:
            errors += 1
            print(f"  错误: [{l},{r}] expected {expected}, got {got}")

    print(f"  1000次随机测试，错误数: {errors}")

    # 测试边界情况
    print("\n【测试6】边界情况")
    print(f"  RMQ(0,0) = {rmq.query_min(0, 0)} (应为 {arr[0]})")
    print(f"  RMQ(9,9) = {rmq.query_min(9, 9)} (应为 {arr[9]})")

    print("\n" + "=" * 50)
    print("Sparse Table测试完成！")
    print("=" * 50)
