"""
Fenwick Tree / Binary Indexed Tree（树状数组）
==========================================

【算法原理】
利用二进制表示，将数组索引的二进制展开，利用lowbit运算，
实现 O(log n) 的前缀和查询和单点更新。

【时间复杂度】
- 单点更新: O(log n)
- 前缀和查询: O(log n)
- 区间和查询: O(log n)
- 构建: O(n log n) 或 O(n)

【空间复杂度】O(n)

【应用场景】
- 动态前缀和
- 逆序对计数
- 频率统计
- 插入顺序统计
"""

from typing import List


class FenwickTree:
    """
    树状数组 / BIT

    【核心思想】
    - tree[i] 保存以 i 为结尾、长度为 lowbit(i) 的区间和
    - lowbit(i) = i & (-i)，得到最低位的1

    【关键操作】
    - add(i, delta): 在位置i加上delta（1-indexed）
    - sum(i): 求前i个元素的和 [1, i]
    - range_sum(l, r): 求区间和 [l, r]
    """

    def __init__(self, data: List = None, size: int = 0):
        """
        初始化

        【参数】
        - data: 初始数组（可选）
        - size: 数组大小（如果不提供data）
        """
        if data is not None:
            self.n = len(data)
            # tree[0]不用，从1开始
            self.tree = [0] * (self.n + 1)
            # O(n)构建：从data[i]更新tree[i+1]
            for i in range(self.n):
                self._add_internal(i + 1, data[i])
        else:
            self.n = size
            self.tree = [0] * (self.n + 1)

    def _lowbit(self, x: int) -> int:
        """
        lowbit(x) = x & (-x)

        【含义】
        - 获取x二进制表示中最低位的1及其后面的0
        - 例如: lowbit(12) = lowbit(1100) = 4
        """
        return x & (-x)

    def _add_internal(self, index: int, delta: int) -> None:
        """
        内部更新（1-indexed）

        【原理】
        更新index后，需要更新所有管辖index的父节点
        index += lowbit(index) 即跳到下一个父节点
        """
        while index <= self.n:
            self.tree[index] += delta
            index += self._lowbit(index)

    def add(self, index: int, delta: int) -> None:
        """
        在位置index增加delta（0-indexed转换为1-indexed）
        """
        self._add_internal(index + 1, delta)

    def _prefix_sum_internal(self, index: int) -> int:
        """
        内部前缀和（1-indexed）

        【原理】
        sum(i) = tree[i] + tree[i - lowbit(i)] + tree[i - lowbit(i) - lowbit(...)]
        """
        result = 0
        while index > 0:
            result += self.tree[index]
            index -= self._lowbit(index)
        return result

    def sum(self, index: int) -> int:
        """
        求前index个元素的和 [0, index]（0-indexed）
        """
        return self._prefix_sum_internal(index + 1)

    def range_sum(self, left: int, right: int) -> int:
        """
        求区间和 [left, right]（0-indexed）

        【公式】sum[0,r] - sum[0,l-1]
        """
        if left == 0:
            return self.sum(right)
        return self.sum(right) - self.sum(left - 1)

    def update(self, index: int, value: int) -> None:
        """
        将位置index的值设置为value（需要计算delta）
        """
        current = self.sum(index) - self.sum(index - 1) if index > 0 else self.sum(0)
        self.add(index, value - current)

    def find_kth(self, k: int) -> int:
        """
        查找第k小的元素（1-indexed k）

        【原理】利用二叉搜索，从高位到低位逼近
        【条件】树中所有元素之和 >= k
        """
        if k <= 0:
            return -1

        # 找到最大的2的幂 >= n
        log_n = (self.n).bit_length()
        idx = 0
        bit_mask = 1 << log_n

        while bit_mask != 0:
            next_idx = idx + bit_mask
            if next_idx <= self.n and self.tree[next_idx] < k:
                k -= self.tree[next_idx]
                idx = next_idx
            bit_mask >>= 1

        return idx  # 返回的是0-indexed位置（差1）


class FenwickTree2D:
    """
    二维树状数组

    【原理】对每个维度都用BIT
    【操作】O((log n)²) 的二维前缀和
    """

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.tree = [[0] * (cols + 1) for _ in range(rows + 1)]

    def _lowbit(self, x: int) -> int:
        return x & (-x)

    def add(self, row: int, col: int, delta: int) -> None:
        """二维单点增加"""
        r = row + 1
        while r <= self.rows:
            c = col + 1
            while c <= self.cols:
                self.tree[r][c] += delta
                c += self._lowbit(c)
            r += self._lowbit(r)

    def prefix_sum(self, row: int, col: int) -> int:
        """二维前缀和 [0,0] 到 [row,col]"""
        r = row + 1
        result = 0
        while r > 0:
            c = col + 1
            while c > 0:
                result += self.tree[r][c]
                c -= self._lowbit(c)
            r -= self._lowbit(r)
        return result

    def range_sum(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """二维区间和"""
        return (self.prefix_sum(r2, c2)
                - self.prefix_sum(r1 - 1, c2)
                - self.prefix_sum(r2, c1 - 1)
                + self.prefix_sum(r1 - 1, c1 - 1))


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Fenwick Tree（树状数组） - 测试")
    print("=" * 50)

    arr = [1, 3, 5, 7, 9, 11]

    # 测试1：基本操作
    print("\n【测试1】基本操作")
    bit = FenwickTree(arr)
    print(f"  数组: {arr}")

    print(f"  前缀和 sum(0) = {bit.sum(0)}")      # 1
    print(f"  前缀和 sum(2) = {bit.sum(2)}")      # 1+3+5=9
    print(f"  前缀和 sum(5) = {bit.sum(5)}")      # 36
    print(f"  区间和 [1,3] = {bit.range_sum(1,3)}")  # 3+5+7=15
    print(f"  区间和 [0,5] = {bit.range_sum(0,5)}")  # 36

    # 测试2：单点更新
    print("\n【测试2】单点更新")
    bit.add(2, 10)  # arr[2]从5变成15
    print(f"  arr[2]+=10后，区间[0,2]={bit.sum(2)}")  # 1+3+15=19

    # 测试3：查找第k小
    print("\n【测试3】查找第k小")
    bit2 = FenwickTree([1, 2, 3, 4, 5])
    print(f"  数组: [1,2,3,4,5]")
    for k in [1, 3, 5, 6]:
        idx = bit2.find_kth(k)
        print(f"  第{k}小的索引: {idx}")

    # 测试4：逆序对计数
    print("\n【测试4】逆序对计数")
    arr4 = [2, 4, 1, 3, 5]
    bit4 = FenwickTree(size=max(arr4) + 1)
    inversions = 0

    for i, val in enumerate(arr4):
        # 当前数之前有多少数比它大
        greater_before = bit4.sum(max(arr4)) - bit4.sum(val)
        inversions += greater_before
        bit4.add(val, 1)

    print(f"  数组: {arr4}")
    print(f"  逆序对数: {inversions}")  # (2,1),(4,1),(4,3) = 3

    # 测试5：二维树状数组
    print("\n【测试5】二维树状数组")
    bit2d = FenwickTree2D(3, 3)

    # 添加几个值
    points = [(0,0,1), (1,1,2), (2,2,3), (1,0,4)]
    for r, c, v in points:
        bit2d.add(r, c, v)

    print(f"  添加点: {points}")
    print(f"  前缀和 [0,0] = {bit2d.prefix_sum(0,0)}")  # 1
    print(f"  前缀和 [1,1] = {bit2d.prefix_sum(1,1)}")  # 1+2=3
    print(f"  区间和 [0,0]到[2,2] = {bit2d.range_sum(0,0,2,2)}")  # 1+2+3+4=10

    print("\n" + "=" * 50)
    print("Fenwick Tree测试完成！")
    print("=" * 50)
