# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / skiplist_probability



本文件实现 skiplist_probability 相关的算法功能。

"""



import random

import math

import numpy as np





class SkipListAnalysis:

    """跳表概率分析"""



    def __init__(self, p=0.5, max_level=16):

        """

        初始化分析器

        

        参数:

            p: 晋升概率

            max_level: 最大层数

        """

        self.p = p

        self.max_level = max_level



    def height_distribution(self, n):

        """

        计算 n 个元素的高度分布

        

        参数:

            n: 元素数量

        返回:

            distribution: {level: count} 字典

        """

        distribution = {i: 0 for i in range(self.max_level + 1)}

        

        for _ in range(n):

            level = self._random_height()

            distribution[level] += 1

        

        return distribution



    def _random_height(self):

        """生成随机高度"""

        level = 0

        while random.random() < self.p and level < self.max_level:

            level += 1

        return level



    def expected_height(self):

        """期望高度"""

        return 1 / (1 - self.p)



    def expected_layers(self, n):

        """

        期望的层数（最上层索引 + 1）

        

        参数:

            n: 元素数量

        返回:

            expected_layers: 期望层数

        """

        # 最上层索引 k 满足 n * p^k < 1

        # k < log(n) / log(1/p)

        return math.log(n) / math.log(1 / self.p) + 1



    def probability_of_height(self, k):

        """

        计算高度恰好为 k 的概率

        

        P(height = k) = (1-p) * p^k

        

        参数:

            k: 高度

        返回:

            prob: 概率

        """

        return (1 - self.p) * (self.p ** k)



    def probability_of_level_containing(self, level, n):

        """

        计算第 level 层至少有一个元素的概率

        

        P(level k has elements) = 1 - (1 - p^k)^n

        

        参数:

            level: 层索引

            n: 元素数量

        返回:

            prob: 概率

        """

        return 1 - (1 - self.p ** level) ** n



    def search_cost_expected(self, n):

        """

        期望搜索代价

        

        E[cost] = (1/(1-p)) * log_{1/p}(n)

        

        参数:

            n: 元素数量

        返回:

            cost: 期望比较次数

        """

        return self.expected_height() * math.log(n) / math.log(1 / self.p)



    def search_cost_worst(self, n, delta=0.01):

        """

        最坏情况搜索代价（高概率）

        

        使用 Chernoff bound

        

        参数:

            n: 元素数量

            delta: 允许的失败概率

        返回:

            cost: 高概率下的最坏代价

        """

        # 高度超过 E[height] + ln(1/delta) 的概率 < delta

        height_bound = self.expected_height() + math.log(1 / delta)

        

        # 每层搜索 O(log n) 个元素

        layers = math.log(n) / math.log(1 / self.p) + height_bound

        

        return layers * math.log(n)



    def space_expected(self, n):

        """

        期望空间复杂度

        

        E[space] = n / (1-p)

        

        参数:

            n: 元素数量

        返回:

            space: 期望指针数

        """

        return n / (1 - self.p)



    def insert_success_probability(self, n, max_attempts=1):

        """

        单次插入成功的概率

        

        参数:

            n: 当前元素数量

            max_attempts: 最大尝试次数

        返回:

            prob: 成功概率

        """

        # 高度至少为 1 的概率

        p_height_1 = self.p

        

        # 需要在第 0 层插入

        # 每层搜索元素数 ~ n / (1-p)^level

        # 插入失败发生在所有层都满了

        

        # 简化：假设第 0 层空间无限

        return 1 - (1 - p_height_1) ** max_attempts





class SkipListSimulator:

    """跳表模拟器（用于验证理论）"""



    def __init__(self, p=0.5, max_level=16):

        self.p = p

        self.max_level = max_level

        self.nodes = []



    def insert_random(self, key, value):

        """插入随机高度的节点"""

        # 生成随机高度

        level = 0

        while random.random() < self.p and level < self.max_level:

            level += 1

        

        node = {

            'key': key,

            'value': value,

            'level': level,

            'forward': [None] * (level + 1)

        }

        self.nodes.append(node)

        return node



    def get_height_distribution(self):

        """获取高度分布"""

        if not self.nodes:

            return {}

        

        dist = {}

        for node in self.nodes:

            l = node['level']

            dist[l] = dist.get(l, 0) + 1

        return dist



    def get_max_height(self):

        """获取最大高度"""

        if not self.nodes:

            return 0

        return max(n['level'] for n in self.nodes)



    def get_avg_height(self):

        """获取平均高度"""

        if not self.nodes:

            return 0

        return sum(n['level'] for n in self.nodes) / len(self.nodes)





class SkipListBounds:

    """跳表性能边界证明辅助"""



    @staticmethod

    def chernoff_bound(n, delta):

        """

        Chernoff bound for height distribution

        

        P(X > (1+delta)E[X]) < exp(-delta^2 E[X] / 3)

        

        参数:

            n: 元素数

            delta: 偏离参数

        返回:

            bound: 上界概率

        """

        expected_height = 1 / 0.5  # p=0.5

        return math.exp(-delta**2 * expected_height / 3)



    @staticmethod

    def union_bound(prob_list):

        """

        Union bound for multiple events

        

        P(A1 U A2 U ...) <= sum P(Ai)

        

        参数:

            prob_list: 概率列表

        返回:

            bound: 上界

        """

        return sum(prob_list)



    @staticmethod

    def concentration_bound(n, epsilon):

        """

        集中不等式边界

        

        证明搜索时间以高概率在 O(log n) 内

        

        参数:

            n: 元素数

            epsilon: 相对误差

        返回:

            bound: 失败概率上界

        """

        # 每层高度超过 (1+epsilon)log_{1/p}(n) 的概率

        # 使用 Chernoff

        log_n = math.log(n) / math.log(2)  # p=0.5

        delta = epsilon

        

        return 2 * math.exp(-epsilon**2 * log_n / 3)





class ProbabilityCalculator:

    """概率计算器"""



    @staticmethod

    def geometric_pmf(k, p):

        """

        几何分布概率质量函数

        

        P(X = k) = (1-p) * p^k

        

        参数:

            k: 值 (k >= 0)

            p: 成功概率

        返回:

            prob: 概率

        """

        return (1 - p) * (p ** k)



    @staticmethod

    def geometric_cdf(k, p):

        """

        几何分布累积分布函数

        

        P(X <= k) = 1 - p^{k+1}

        

        参数:

            k: 值

            p: 成功概率

        返回:

            prob: 累积概率

        """

        return 1 - (p ** (k + 1))



    @staticmethod

    def negative_binomial_mean(r, p):

        """

        负二项分布均值

        

        E[X] = r * (1-p) / p

        

        参数:

            r: 成功次数

            p: 每次成功概率

        返回:

            mean: 均值

        """

        return r * (1 - p) / p



    @staticmethod

    def simulate_height(n, p, trials=10000):

        """

        模拟高度分布

        

        参数:

            n: 元素数

            p: 晋升概率

            trials: 模拟次数

        返回:

            heights: 高度列表

        """

        heights = []

        for _ in range(trials):

            level = 0

            while random.random() < p and level < 32:

                level += 1

            heights.append(level)

        return heights





if __name__ == "__main__":

    print("=== Skip List 概率分析 ===\n")



    # 分析器

    analysis = SkipListAnalysis(p=0.5)



    # 理论值

    print("--- 理论分析 ---")

    print(f"  期望高度: {analysis.expected_height():.2f}")

    

    for n in [100, 1000, 10000]:

        layers = analysis.expected_layers(n)

        search_cost = analysis.search_cost_expected(n)

        space = analysis.space_expected(n)

        print(f"\n  n = {n}:")

        print(f"    期望层数: {layers:.1f}")

        print(f"    期望搜索代价: {search_cost:.1f}")

        print(f"    期望空间: {space:.0f}")



    # 概率计算

    print("\n--- 概率计算 ---")

    for level in range(6):

        prob = analysis.probability_of_height(level)

        print(f"  P(height = {level}) = {prob:.4f}")

    

    print("\n  第 3 层有元素的概率:")

    for n in [100, 1000, 10000]:

        prob = analysis.probability_of_level_containing(3, n)

        print(f"    n = {n}: {prob:.4f}")



    # 模拟验证

    print("\n--- 模拟验证 ---")

    simulator = SkipListSimulator(p=0.5)

    

    for n in [100, 1000, 5000]:

        simulator.nodes = []  # 重置

        for i in range(n):

            simulator.insert_random(i, i)

        

        dist = simulator.get_height_distribution()

        print(f"\n  n = {n}:")

        print(f"    模拟最大高度: {simulator.get_max_height()}")

        print(f"    模拟平均高度: {simulator.get_avg_height():.2f}")

        print(f"    理论期望高度: {analysis.expected_height():.2f}")

        print(f"    高度分布: {dict(sorted(dist.items()))}")



    # 边界证明

    print("\n--- 边界证明 ---")

    bounds = SkipListBounds()

    

    for n in [1000, 10000, 100000]:

        for epsilon in [0.1, 0.5, 1.0]:

            bound = bounds.concentration_bound(n, epsilon)

            print(f"  n = {n}, epsilon = {epsilon}: P(|error| > epsilon) < {bound:.2e}")



    # 概率计算器

    print("\n--- 概率计算器 ---")

    calc = ProbabilityCalculator()

    

    print("  几何分布 (p=0.5):")

    for k in range(5):

        pmf = calc.geometric_pmf(k, 0.5)

        cdf = calc.geometric_cdf(k, 0.5)

        print(f"    k={k}: PMF={pmf:.4f}, CDF={cdf:.4f}")



    # 模拟高度

    print("\n--- 模拟高度分布 ---")

    heights = calc.simulate_height(10000, 0.5, trials=10000)

    

    # 统计

    print(f"  样本数: {len(heights)}")

    print(f"  最小: {min(heights)}, 最大: {max(heights)}")

    print(f"  平均: {np.mean(heights):.2f}")

    print(f"  标准差: {np.std(heights):.2f}")

    

    # 分布

    from collections import Counter

    dist = Counter(heights)

    print("  高度分布:")

    for level in sorted(dist.keys()):

        print(f"    level {level}: {dist[level]} ({dist[level]/len(heights)*100:.1f}%)")



    # 比较 p 值

    print("\n--- 不同 p 值的比较 ---")

    for p in [0.25, 0.5, 0.75]:

        analysis = SkipListAnalysis(p=p)

        print(f"\n  p = {p}:")

        print(f"    期望高度: {analysis.expected_height():.2f}")

        print(f"    n=1000 期望层数: {analysis.expected_layers(1000):.1f}")

        print(f"    n=1000 期望搜索: {analysis.search_cost_expected(1000):.1f}")

        print(f"    n=1000 期望空间: {analysis.space_expected(1000):.0f}")

