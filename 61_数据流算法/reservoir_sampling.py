# -*- coding: utf-8 -*-

"""

算法实现：数据流算法 / reservoir_sampling



本文件实现 reservoir_sampling 相关的算法功能。

"""



import random

from typing import List





class ReservoirSampler:

    """水库采样器"""



    def __init__(self, k: int):

        """

        参数：

            k: 水库大小（保留的样本数）

        """

        self.k = k

        self.reservoir = []

        self.n_seen = 0



    def add(self, item) -> None:

        """

        添加元素



        参数：

            item: 新元素

        """

        self.n_seen += 1



        if len(self.reservoir) < self.k:

            # 水库未满，直接添加

            self.reservoir.append(item)

        else:

            # 以 k/n 概率替换

            j = random.randint(1, self.n_seen)

            if j <= self.k:

                # 替换位置 j-1

                self.reservoir[j - 1] = item



    def get_sample(self) -> List:

        """

        获取当前样本



        返回：样本列表

        """

        return self.reservoir.copy()



    def estimate_diversity(self) -> float:

        """

        估计多样性（样本熵）



        返回：熵估计

        """

        if not self.reservoir:

            return 0.0



        # 简化：计算样本的熵

        from collections import Counter



        counts = Counter(self.reservoir)

        total = len(self.reservoir)



        entropy = 0.0

        for count in counts.values():

            p = count / total

            if p > 0:

                entropy -= p * (p ** 0.5)  # 简化熵



        return entropy





class WeightedReservoirSampler:

    """加权水库采样"""



    def __init__(self, k: int):

        """

        参数：

            k: 水库大小

        """

        self.k = k

        self.reservoir = []

        self.weights = []

        self.total_weight = 0



    def add(self, item, weight: float) -> None:

        """

        添加带权重的元素



        参数：

            item: 元素

            weight: 权重

        """

        self.total_weight += weight



        if len(self.reservoir) < self.k:

            self.reservoir.append(item)

            self.weights.append(weight)

        else:

            # 以 weight/total 的概率替换

            if random.random() < weight / self.total_weight:

                # 替换随机位置

                idx = random.randint(0, self.k - 1)

                self.reservoir[idx] = item

                self.weights[idx] = weight





def reservoir_sampling_applications():

    """水库采样应用"""

    print("=== 水库采样应用 ===")

    print()

    print("1. 数据流分析")

    print("   - 统计流中元素分布")

    print("   - 估计分位数")

    print()

    print("2. 搜索引擎")

    print("   - 随机选择搜索结果")

    print("   - 均匀采样保证公平性")

    print()

    print("3. 机器学习")

    print("   - 从大数据集中采样")

    print("   - 在线学习中的经验回放")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 水库采样测试 ===\n")



    k = 5

    sampler = ReservoirSampler(k)



    print(f"水库大小: {k}")

    print()



    # 模拟数据流

    stream = list(range(1, 101))



    print("处理100个元素...")

    for item in stream:

        sampler.add(item)



    # 获取样本

    sample = sampler.get_sample()



    print(f"\n采样结果 ({len(sample)} 个):")

    print(f"  {sample}")



    # 检查均匀性

    print("\n均匀性检查：")

    expected_prob = k / 100

    print(f"  每个元素被选中的期望概率: {expected_prob:.4f}")

    print(f"  样本大小: {len(sample)}")



    # 多次运行看分布

    print("\n100次运行的统计：")

    counts = {i: 0 for i in range(1, 101)}



    for _ in range(100):

        sampler = ReservoirSampler(k)

        for item in stream:

            sampler.add(item)

        for s in sampler.get_sample():

            counts[s] += 1



    # 统计哪些元素经常被选中

    top_elements = sorted(counts.items(), key=lambda x: -x[1])[:5]

    print(f"  最常被选中的元素: {[e[0] for e in top_elements]}")



    print()

    reservoir_sampling_applications()



    print()

    print("说明：")

    print("  - 水库采样是流数据处理的基础")

    print("  - 每滴水被选中的概率相等")

    print("  - 复杂度 O(1) 每元素")

