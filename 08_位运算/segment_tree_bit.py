# -*- coding: utf-8 -*-

"""

算法实现：08_位运算 / segment_tree_bit



本文件实现 segment_tree_bit 相关的算法功能。

"""



class FenwickTree:

    """树状数组：单点更新+前缀和 / 区间求和"""



    def __init__(self, n: int):

        self.n = n

        self.tree = [0] * (n + 1)  # 1-indexed



    def _lowbit(self, i: int) -> int:

        """获取最低位的1：i & (-i)"""

        return i & (-i)



    def update(self, idx: int, delta: int):

        """在位置idx增加delta（idx为1-indexed）"""

        while idx <= self.n:

            self.tree[idx] += delta

            idx += self._lowbit(idx)



    def prefix_sum(self, idx: int) -> int:

        """前缀和[1..idx]"""

        result = 0

        while idx > 0:

            result += self.tree[idx]

            idx -= self._lowbit(idx)

        return result



    def range_sum(self, left: int, right: int) -> int:

        """区间和[left..right]（1-indexed inclusive）"""

        return self.prefix_sum(right) - self.prefix_sum(left - 1)



    def point_query(self, idx: int) -> int:

        """单点查询（转换为前缀和差值）"""

        return self.range_sum(idx, idx)



    def build_from_array(self, arr: list[int]):

        """从数组直接构建（O(N)建树）"""

        self.tree[1:] = arr[:]

        for i in range(1, self.n + 1):

            j = i + self._lowbit(i)

            if j <= self.n:

                self.tree[j] += self.tree[i]





class BITRangeAdd:

    """支持区间加法+单点查询的BIT"""



    def __init__(self, n: int):

        self.n = n

        self.bit = [0] * (n + 1)



    def _lowbit(self, i: int) -> int:

        return i & (-i)



    def range_add(self, left: int, right: int, delta: int):

        """区间[left, right]加delta"""

        self._add(left, delta)

        self._add(right + 1, -delta)  # 差分思想



    def _add(self, idx: int, delta: int):

        while idx <= self.n:

            self.bit[idx] += delta

            idx += self._lowbit(idx)



    def point_query(self, idx: int) -> int:

        """前缀和即为当前值"""

        result = 0

        while idx > 0:

            result += self.bit[idx]

            idx -= self._lowbit(idx)

        return result





if __name__ == "__main__":

    # 测试1：基础前缀和

    arr = [0, 2, 3, 5, 1, 4, 7, 3, 8]  # 1-indexed，第0位忽略

    bit = FenwickTree(8)

    bit.build_from_array(arr)



    print("原始数组:", arr[1:])

    print(f"前缀和[1..5]: {bit.prefix_sum(5)}")

    print(f"区间和[3..7]: {bit.range_sum(3, 7)}")



    bit.update(4, 10)  # arr[4] += 10

    print(f"\n更新后 arr[4]+=10")

    print(f"区间和[3..7]: {bit.range_sum(3, 7)}")



    # 测试2：区间加法BIT

    print("\n=== 区间加法BIT ===")

    bit2 = BITRangeAdd(10)

    bit2.range_add(2, 5, 3)  # [2,5]加3

    bit2.range_add(5, 8, -2)  # [5,8]减2

    for i in range(1, 11):

        print(f"位置{i}的值: {bit2.point_query(i)}")

