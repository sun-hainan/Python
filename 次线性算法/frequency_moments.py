# -*- coding: utf-8 -*-

"""

算法实现：次线性算法 / frequency_moments



本文件实现 frequency_moments 相关的算法功能。

"""



import random

from collections import Counter

from typing import List, Tuple





class AMSSketch:

    """AMS Sketch（二阶矩估计）"""



    def __init__(self, width: int, depth: int):

        """

        参数：

            width: 计数器数组宽度

            depth: 哈希函数数量

        """

        self.w = width

        self.d = depth

        self.counters = [[0] * width for _ in range(depth)]



    def _hash(self, item: int, seed: int) -> int:

        """哈希函数"""

        import hashlib

        h = hashlib.md5(f"{item}_{seed}".encode())

        return int(h.hexdigest(), 16) % self.w



    def add(self, item: int, count: int = 1) -> None:

        """添加元素"""

        for i in range(self.d):

            idx = self._hash(item, i)

            # 随机化符号

            sign = 1 if random.random() < 0.5 else -1

            self.counters[i][idx] += sign * count



    def estimate_f2(self) -> float:

        """

        估计二阶矩 F2 = Σ f_i²



        返回：估计的F2值

        """

        estimates = []

        for i in range(self.d):

            # 计算平方和

            sum_sq = sum(c * c for c in self.counters[i])

            estimates.append(sum_sq)



        # 取中位数

        estimates.sort()

        return estimates[self.d // 2]



    def estimate_fk(self, k: int, stream: List[int]) -> float:

        """

        估计k阶矩



        参数：

            k: 矩的阶数

            stream: 数据流



        返回：估计的Fk值

        """

        if k == 0:

            # F0：不同元素数

            return len(set(stream))

        elif k == 1:

            # F1：流长度

            return len(stream)

        elif k == 2:

            return self.estimate_f2()

        else:

            # 一般情况：使用Counter

            freq = Counter(stream)

            return sum(f ** k for f in freq.values())





class FlajoletMartin:

    """Flajolet-Martin算法（基数估计）"""



    def __init__(self, num_hash: int = 10):

        self.num_hash = num_hash



    def count_trailing_zeros(self, x: int) -> int:

        """计算二进制表示中尾随0的数量"""

        if x == 0:

            return 32  # 假设32位



        count = 0

        while (x & 1) == 0:

            count += 1

            x >>= 1

        return count



    def estimate_cardinality(self, stream: List[int]) -> int:

        """

        估计不同元素的数量



        返回：基数估计

        """

        max_zeros = [0] * self.num_hash



        for item in stream:

            for i in range(self.num_hash):

                h = hash(f"{item}_{i}") % (1 << 31)

                zeros = self.count_trailing_zeros(h)

                max_zeros[i] = max(max_zeros[i], zeros)



        # 2^R 估计

        # 取中位数

        max_zeros.sort()

        R = max_zeros[self.num_hash // 2]



        return 2 ** R





def frequency_moments_analysis():

    """频率矩分析"""

    print("=== 频率矩分析 ===")

    print()

    print("F0: 不同元素数（基数）")

    print("F1: 流长度（L1范数）")

    print("F2: Σ f_i²（二阶矩，热门度）")

    print("Fk: Σ f_i^k（k阶矩）")

    print()

    print("应用：")

    print("  - 网络流量监控")

    print("  - 数据库查询优化")

    print("  - 数据质量评估")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 频率矩测试 ===\n")



    # 测试AMS Sketch

    print("AMS Sketch测试：")

    stream = [1, 2, 1, 3, 1, 2, 4, 1, 2, 1]

    print(f"流: {stream}")

    print(f"真实频率: {Counter(stream)}")



    # F2估计

    ams = AMSSketch(width=10, depth=5)

    for item in stream:

        ams.add(item)



    f2_estimate = ams.estimate_f2()

    print(f"估计F2: {f2_estimate:.2f}")



    # 真实F2

    freq = Counter(stream).values()

    real_f2 = sum(f ** 2 for f in freq)

    print(f"真实F2: {real_f2}")



    print()



    # Flajolet-Martin

    print("Flajolet-Martin基数估计：")

    fm = FlajoletMartin()

    unique_stream = [1, 2, 3, 2, 1, 4, 5, 3, 2, 1]

    estimate = fm.estimate_cardinality(unique_stream)

    print(f"流: {unique_stream}")

    print(f"估计不同元素数: {estimate}")

    print(f"真实不同元素数: {len(set(unique_stream))}")



    print()

    frequency_moments_analysis()



    print()

    print("说明：")

    print("  - F2用于检测"热门"元素")

    print("  - F0用于估计基数（去重计数）")

    print("  - AMS Sketch是处理大数据流的标准方法")

