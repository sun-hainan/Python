# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / exponential_histogram



本文件实现 exponential_histogram 相关的算法功能。

"""



import math

import time

from collections import deque

from dataclasses import dataclass

from typing import List, Optional





@dataclass

class Bucket:

    """直方图桶"""

    count: int  # 包含的元素数量

    timestamp: float  # 创建时间

    

    def __repr__(self):

        return f"B({self.count})"





class ExponentialHistogram:

    """

    指数直方图

    

    用于估计流数据的分位数

    桶的大小呈指数增长

    """

    

    def __init__(self, epsilon: float = 0.01):

        """

        初始化

        

        Args:

            epsilon: 近似误差参数

        """

        self.epsilon = epsilon

        self.buckets = deque()  # 桶列表

        self.total_count = 0

        

        # 桶级别阈值

        self.max_level = int(math.ceil(math.log(1 / epsilon, 2)))

    

    def _level_size(self, level: int) -> int:

        """

        第level级桶的大小

        

        Args:

            level: 级别 (0, 1, 2, ...)

        

        Returns:

            桶大小 = 2^level

        """

        return 2 ** level

    

    def add(self, value: float, timestamp: float = None):

        """

        添加元素

        

        Args:

            value: 元素值（用于排序）

            timestamp: 时间戳

        """

        if timestamp is None:

            timestamp = time.time()

        

        # 每个元素初始为一个大小为1的桶

        self.buckets.append(Bucket(1, timestamp))

        self.total_count += 1

        

        # 合并桶

        self._merge()

    

    def _merge(self):

        """合并相邻的同大小桶"""

        level_counts = {}  # level -> count

        

        while self.buckets:

            bucket = self.buckets.popleft()

            

            # 计算桶的级别

            level = int(math.log2(bucket.count))

            

            if level in level_counts:

                # 与已有桶合并

                level_counts[level] += bucket.count

            else:

                level_counts[level] = bucket.count

            

            # 尝试合并

            while level_counts[level] >= 2 * self._level_size(level):

                # 创建更高级别的桶

                new_level = level + 1

                level_counts[new_level] = level_counts.get(new_level, 0) + self._level_size(new_level)

                level_counts[level] -= self._level_size(new_level)

                

                if level_counts[level] == 0:

                    del level_counts[level]

                

                level = new_level

        

        # 重建桶列表

        for level in sorted(level_counts.keys()):

            count = level_counts[level]

            size = self._level_size(level)

            

            while count >= size:

                self.buckets.append(Bucket(size, time.time()))

                count -= size

    

    def quantile(self, q: float) -> float:

        """

        估计分位数

        

        Args:

            q: 分位数 (0-1)

        

        Returns:

            估计的分位数值

        """

        if not self.buckets:

            return 0.0

        

        target_rank = int(q * self.total_count)

        

        # 简化实现：返回桶的索引作为近似

        cumsum = 0

        for bucket in self.buckets:

            cumsum += bucket.count

            if cumsum >= target_rank:

                # 返回一个估计值（实际应存储元素值）

                return cumsum

        

        return cumsum

    

    def rank(self, value: float) -> float:

        """

        估计给定值的秩

        

        Args:

            value: 查询值

        

        Returns:

            估计的秩百分比 (0-1)

        """

        # 简化实现

        return min(value / self.total_count, 1.0)





class QuantileEstimator:

    """

    分位数估计器

    

    使用多个指数直方图估计不同分位数

    """

    

    def __init__(self, epsilon: float = 0.01):

        self.epsilon = epsilon

        self.histogram = ExponentialHistogram(epsilon)

        

        # 要估计的分位数

        self.quantiles = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]

    

    def add(self, value: float):

        """添加值"""

        self.histogram.add(value)

    

    def get_quantiles(self) -> dict:

        """获取所有分位数估计"""

        result = {}

        for q in self.quantiles:

            result[q] = self.histogram.quantile(q)

        return result

    

    def summary(self) -> str:

        """获取统计摘要"""

        qs = self.get_quantiles()

        return (f"min={qs.get(0.01, 0):.2f}, "

                f"p25={qs.get(0.25, 0):.2f}, "

                f"p50={qs.get(0.5, 0):.2f}, "

                f"p75={qs.get(0.75, 0):.2f}, "

                f"max={qs.get(0.99, 0):.2f}")





class GKQuantile:

    """

    Greenwald-Khanna 分位数算法

    

    空间高效的分位数估计

    """

    

    def __init__(self, epsilon: float = 0.01):

        self.epsilon = epsilon

        self.samples = []  # [(value, rank_min, rank_max), ...]

        self.n = 0  # 观察总数

    

    def add(self, value: float):

        """添加值"""

        self.n += 1

        

        # 初始化

        if not self.samples:

            self.samples.append((value, 0, self.n - 1))

            return

        

        # 找到插入位置

        i = 0

        while i < len(self.samples) and self.samples[i][0] < value:

            i += 1

        

        # 计算新的rank范围

        rank_min = self.samples[i-1][2] + 1 if i > 0 else 0

        rank_max = rank_min  # 初始为1

        

        # 插入

        self.samples.insert(i, (value, rank_min, rank_max))

        

        # 合并（保持压缩）

        self._compress()

    

    def _compress(self):

        """压缩样本"""

        i = 0

        while i < len(self.samples) - 1:

            curr = self.samples[i]

            next_s = self.samples[i + 1]

            

            # 计算合并后的最大rank

            new_max = curr[2] + next_s[2] - curr[1]

            

            if new_max - curr[1] <= int(2 * self.epsilon * self.n):

                # 合并

                self.samples[i] = (curr[0], curr[1], new_max)

                self.samples.pop(i + 1)

            else:

                i += 1

    

    def quantile(self, q: float) -> float:

        """估计分位数"""

        if not self.samples:

            return 0.0

        

        rank = int(q * self.n)

        

        for i, (value, rank_min, rank_max) in enumerate(self.samples):

            if rank_min <= rank <= rank_max:

                return value

        

        return self.samples[-1][0]





def demo_exponential_histogram():

    """演示指数直方图"""

    print("=== 指数直方图演示 ===\n")

    

    import random

    random.seed(42)

    

    eh = ExponentialHistogram(epsilon=0.01)

    

    print("添加1000个随机值:")

    for i in range(1000):

        value = random.gauss(50, 10)

        eh.add(value)

    

    print(f"  总元素数: {eh.total_count}")

    print(f"  桶数量: {len(eh.buckets)}")

    print(f"  级别分布: ", end="")

    

    # 统计级别

    level_counts = {}

    for b in eh.buckets:

        level = int(math.log2(b.count))

        level_counts[level] = level_counts.get(level, 0) + 1

    

    for level in sorted(level_counts.keys()):

        print(f"L{level}={level_counts[level]}", end=" ")

    print()

    

    # 分位数估计

    print("\n分位数估计:")

    for q in [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]:

        est = eh.quantile(q)

        print(f"  p{int(q*100)}: {est:.2f}")





def demo_gk_quantile():

    """演示GK分位数算法"""

    print("\n=== GK分位数算法演示 ===\n")

    

    import random

    random.seed(42)

    

    gk = GKQuantile(epsilon=0.01)

    

    print("添加1000个随机值:")

    for i in range(1000):

        value = random.gauss(50, 10)

        gk.add(value)

    

    print(f"  总元素数: {gk.n}")

    print(f"  样本数: {len(gk.samples)}")

    print(f"  压缩比: {gk.n / len(gk.samples):.1f}x")

    

    print("\n分位数估计:")

    for q in [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]:

        est = gk.quantile(q)

        print(f"  p{int(q*100)}: {est:.2f}")





def demo_accuracy():

    """演示准确性"""

    print("\n=== 准确性分析 ===\n")

    

    import random

    random.seed(42)

    

    # 生成均匀分布的数据

    values = [random.uniform(0, 100) for _ in range(10000)]

    sorted_values = sorted(values)

    

    print("均匀分布 [0, 100], n=10000:")

    print("| 分位数 | 实际值 | GK估计 | 误差 |")

    

    gk = GKQuantile(epsilon=0.01)

    for v in values:

        gk.add(v)

    

    for q in [0.25, 0.5, 0.75]:

        actual = sorted_values[int(q * 10000)]

        estimated = gk.quantile(q)

        error = abs(estimated - actual)

        print(f"| {int(q*100):3d}%   | {actual:6.2f} | {estimated:6.2f} | {error:5.2f} |")





def demo_comparison():

    """对比不同实现"""

    print("\n=== 实现对比 ===\n")

    

    import random

    import time

    random.seed(42)

    

    n = 100000

    

    # 生成数据

    values = [random.gauss(50, 10) for _ in range(n)]

    

    # GK Quantile

    gk = GKQuantile(epsilon=0.01)

    start = time.time()

    for v in values:

        gk.add(v)

    gk_time = time.time() - start

    

    # 简单直方图

    histogram = {}

    start = time.time()

    for v in values:

        bucket = int(v / 5) * 5  # 5为单位的桶

        histogram[bucket] = histogram.get(bucket, 0) + 1

    hist_time = time.time() - start

    

    print(f"添加 {n} 个元素:")

    print(f"  GK Quantile: {gk_time:.3f}s")

    print(f"  简单直方图: {hist_time:.3f}s")

    print()

    

    print(f"空间使用:")

    print(f"  GK Quantile: {len(gk.samples)} 个样本")

    print(f"  简单直方图: {len(histogram)} 个桶")





def demo_streaming_quantiles():

    """演示流式分位数"""

    print("\n=== 流式分位数估计 ===\n")

    

    import random

    random.seed(42)

    

    # 模拟时变分布

    gk = GKQuantile(epsilon=0.01)

    

    print("模拟分布变化:")

    print("| 阶段 | 分布 | p50估计 |")

    

    # 阶段1: 高斯(50, 5)

    for _ in range(1000):

        gk.add(random.gauss(50, 5))

    print(f"| 1    | N(50,5) | {gk.quantile(0.5):.2f} |")

    

    # 阶段2: 高斯(70, 5)

    for _ in range(1000):

        gk.add(random.gauss(70, 5))

    print(f"| 2    | N(70,5) | {gk.quantile(0.5):.2f} |")

    

    # 阶段3: 高斯(60, 10)

    for _ in range(1000):

        gk.add(random.gauss(60, 10))

    print(f"| 3    | N(60,10)| {gk.quantile(0.5):.2f} |")

    

    print("\n注：GK保持所有样本，但压缩旧样本以节省空间")





if __name__ == "__main__":

    print("=" * 60)

    print("指数直方图算法")

    print("=" * 60)

    

    # 指数直方图

    demo_exponential_histogram()

    

    # GK分位数

    demo_gk_quantile()

    

    # 准确性

    demo_accuracy()

    

    # 对比

    demo_comparison()

    

    # 流式分位数

    demo_streaming_quantiles()

    

    print("\n" + "=" * 60)

    print("核心原理:")

    print("=" * 60)

    print("""

1. 指数直方图:

   - 桶大小呈指数增长: 1, 2, 4, 8, ...

   - 相同大小的相邻桶合并

   - O(1) 插入和查询



2. GK Quantile:

   - 维护有序样本

   - 每个样本有 rank_min 和 rank_max

   - 合并稀疏样本

   - O(n) 空间但压缩率高



3. 误差分析:

   - ε 控制近似误差

   - 分位数估计误差 ≤ ε

   - 空间 O(1/ε)



4. 应用:

   - 网络监控 (p95, p99延迟)

   - 数据库查询优化

   - 实时分析

""")

