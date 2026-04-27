# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 06_dp_mechanisms



本文件实现 06_dp_mechanisms 相关的算法功能。

"""



import numpy as np

from typing import Callable, List, Tuple, Dict





class SensitivityAnalyzer:

    """

    敏感度分析器



    计算查询函数的敏感度

    """



    def __init__(self):

        """初始化敏感度分析器"""

        pass



    def global_l1_sensitivity(

        self,

        query_func: Callable,

        max_diff: float = 1.0

    ) -> float:

        """

        计算L1全局敏感度



        L1敏感度: 改变一个元素时,函数输出的L1范数最大变化



        适用于拉普拉斯机制



        Args:

            query_func: 查询函数

            max_diff: 单个元素最大差异



        Returns:

            全局L1敏感度

        """

        # 对于简单的计数/求和查询,敏感度是常量

        # 实际需要遍历所有可能的邻近数据集

        # 这里返回上界

        return max_diff



    def global_l2_sensitivity(

        self,

        query_func: Callable,

        max_diff: float = 1.0

    ) -> float:

        """

        计算L2全局敏感度



        L2敏感度: 改变一个元素时,函数输出的L2范数最大变化



        适用于高斯机制



        Args:

            query_func: 查询函数

            max_diff: 单个元素最大差异



        Returns:

            全局L2敏感度

        """

        return max_diff



    def adjacent_datasets(self, dataset: List, max_size: int = 100) -> List[List]:

        """

        生成邻近数据集(用于测试)



        邻近数据集: 只差一个元素的两个数据集



        Args:

            dataset: 原始数据集

            max_size: 测试样本数



        Returns:

            邻近数据集列表

        """

        adjacent = []

        n = min(len(dataset), max_size)



        for i in range(n):

            # 删除第i个元素

            adj = dataset[:i] + dataset[i+1:]

            adjacent.append(adj)



        return adjacent





class LaplaceMechanism:

    """

    拉普拉斯机制



    适用于数值型查询的差分隐私



    添加的噪声服从拉普拉斯分布:

    f(x) = (1/2b) * exp(-|x|/b)



    其中 b = Δf / ε (敏感度/隐私预算)



    特性:

    - 提供ε-差分隐私

    - 对异常值敏感

    - 适合计数和求和查询

    """



    def __init__(self, epsilon: float = 1.0):

        """

        初始化拉普拉斯机制



        Args:

            epsilon: 隐私预算,越小隐私保护越强

        """

        self.epsilon = epsilon



    def add_noise(self, value: float, sensitivity: float) -> float:

        """

        添加拉普拉斯噪声



        Args:

            value: 真实查询值

            sensitivity: 查询的L1敏感度



        Returns:

            加噪后的值

        """

        # 拉普拉斯噪声尺度 b = sensitivity / epsilon

        scale = sensitivity / self.epsilon



        # 生成拉普拉斯噪声

        noise = np.random.laplace(0, scale)



        return value + noise



    def privacy_loss(self, sensitivity: float) -> float:

        """

        计算隐私损失



        Args:

            sensitivity: 敏感度



        Returns:

            隐私损失上界

        """

        return self.epsilon * sensitivity



    def compose(self, other: "LaplaceMechanism") -> "LaplaceMechanism":

        """

        组合多个拉普拉斯机制



        使用序列组合定理:

        ε_total = ε1 + ε2 + ...



        Args:

            other: 另一个拉普拉斯机制



        Returns:

            组合后的机制

        """

        combined_epsilon = self.epsilon + other.epsilon

        return LaplaceMechanism(combined_epsilon)





class GaussianMechanism:

    """

    高斯机制



    适用于复合查询和更复杂的隐私保证



    添加的噪声服从高斯分布:

    N(0, σ²)



    其中 σ ≥ √(2ln(1.25/δ)) * Δ2 / ε



    特性:

    - 提供(ε, δ)-差分隐私

    - 对异常值更鲁棒

    - 适合连续查询

    """



    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):

        """

        初始化高斯机制



        Args:

            epsilon: 隐私预算

            delta: 失败概率上界

        """

        self.epsilon = epsilon

        self.delta = delta



    def compute_sigma(self, sensitivity: float) -> float:

        """

        计算所需噪声标准差



        使用高斯机制的理论保证:

        σ ≥ √(2ln(1.25/δ)) * Δ2 / ε



        Args:

            sensitivity: L2敏感度



        Returns:

            噪声标准差

        """

        # σ = √(2 * ln(1.25/δ)) * sensitivity / ε

        import math

        coefficient = math.sqrt(2 * math.log(1.25 / self.delta))

        sigma = coefficient * sensitivity / self.epsilon

        return sigma



    def add_noise(self, value: float, sensitivity: float) -> float:

        """

        添加高斯噪声



        Args:

            value: 真实查询值

            sensitivity: 查询的L2敏感度



        Returns:

            加噪后的值

        """

        sigma = self.compute_sigma(sensitivity)

        noise = np.random.normal(0, sigma)

        return value + noise



    def privacy_loss(self) -> Tuple[float, float]:

        """

        获取隐私损失参数



        Returns:

            (ε, δ) 元组

        """

        return (self.epsilon, self.delta)





class ExponentialMechanism:

    """

    指数机制



    适用于非数值输出的差分隐私



    选择输出o的概率与 exp(ε * q(D,o) / (2 * Δq)) 成正比



    其中q是评分函数,Δq是敏感度



    特性:

    - 提供ε-差分隐私

    - 适用于离散选择

    - 常用于推荐系统、排名等

    """



    def __init__(self, epsilon: float = 1.0):

        """

        初始化指数机制



        Args:

            epsilon: 隐私预算

        """

        self.epsilon = epsilon



    def select(

        self,

        candidates: List,

        score_func: Callable[[any, List], float],

        sensitivity: float,

        dataset: List = None

    ) -> any:

        """

        从候选中选择



        Args:

            candidates: 候选列表

            score_func: 评分函数 score(candidate, dataset)

            sensitivity: 评分函数的敏感度

            dataset: 数据集



        Returns:

            选中的候选

        """

        # 计算每个候选的分数

        scores = []

        for candidate in candidates:

            score = score_func(candidate, dataset)

            scores.append(score)



        # 转换为概率权重

        max_score = max(scores)

        adjusted_scores = [s - max_score for s in scores]  # 数值稳定性



        weights = [np.exp(self.epsilon * s / (2 * sensitivity)) for s in adjusted_scores]

        total_weight = sum(weights)



        # 归一化为概率

        probabilities = [w / total_weight for w in weights]



        # 随机选择

        return np.random.choice(candidates, p=probabilities)





class DifferentialPrivacyAccountant:

    """

    差分隐私会计



    追踪累积的隐私消耗

    """



    def __init__(self, initial_epsilon: float = float('inf'), delta: float = 0):

        """

        初始化隐私会计



        Args:

            initial_epsilon: 初始ε预算

            delta: δ参数

        """

        self.initial_epsilon = initial_epsilon

        self.delta = delta

        self.epsilon_spent = 0.0

        self.query_count = 0



    def add_query(self, epsilon: float, sensitivity: float = 1.0):

        """

        添加一次查询消耗



        Args:

            epsilon: 本次查询的ε消耗

            sensitivity: 敏感度(用于计算实际消耗)

        """

        self.epsilon_spent += epsilon

        self.query_count += 1



    def get_remaining_budget(self) -> float:

        """

        获取剩余隐私预算



        Returns:

            剩余ε

        """

        if self.initial_epsilon == float('inf'):

            return float('inf')

        return max(0, self.initial_epsilon - self.epsilon_spent)



    def is_within_budget(self, epsilon: float) -> bool:

        """

        检查是否在预算内



        Args:

            epsilon: 要查询的ε



        Returns:

            是否可以执行

        """

        return self.get_remaining_budget() >= epsilon





def demonstrate_mechanisms():

    """

    演示差分隐私机制

    """



    print("差分隐私机制演示")

    print("=" * 50)



    np.random.seed(42)



    # 示例数据集

    dataset = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]



    # 1. 拉普拉斯机制

    print("\n1. 拉普拉斯机制 (ε = 1.0)")

    laplace = LaplaceMechanism(epsilon=1.0)



    # 计数查询的敏感度为1

    count = len(dataset)

    sensitivity = 1.0



    noisy_counts = [laplace.add_noise(count, sensitivity) for _ in range(1000)]

    print(f"   真实计数: {count}")

    print(f"   加噪计数均值: {np.mean(noisy_counts):.2f}")

    print(f"   加噪计数标准差: {np.std(noisy_counts):.2f}")

    print(f"   理论标准差 (b=sensitivity/ε): {sensitivity / 1.0:.2f}")



    # 2. 高斯机制

    print("\n2. 高斯机制 (ε = 1.0, δ = 1e-5)")

    gaussian = GaussianMechanism(epsilon=1.0, delta=1e-5)



    sigma = gaussian.compute_sigma(sensitivity)

    print(f"   噪声标准差: {sigma:.4f}")



    noisy_counts_gaussian = [gaussian.add_noise(count, sensitivity) for _ in range(1000)]

    print(f"   加噪计数均值: {np.mean(noisy_counts_gaussian):.2f}")

    print(f"   加噪计数标准差: {np.std(noisy_counts_gaussian):.4f}")



    # 3. 指数机制

    print("\n3. 指数机制 (选择最佳餐厅)")

    exponential = ExponentialMechanism(epsilon=1.0)



    restaurants = ["A", "B", "C", "D", "E"]

    ratings = {"A": 4.5, "B": 4.8, "C": 4.2, "D": 4.6, "E": 4.4}



    def rating_score(restaurant, data):

        return ratings[restaurant]



    sensitivity = 1.0



    selections = [exponential.select(restaurants, rating_score, sensitivity, dataset)

                   for _ in range(100)]



    # 统计选择分布

    from collections import Counter

    selection_counts = Counter(selections)

    print(f"   餐厅评分: {ratings}")

    print(f"   选择分布: {dict(selection_counts)}")



    # 4. 隐私会计

    print("\n4. 隐私会计")

    accountant = DifferentialPrivacyAccountant(initial_epsilon=10.0)



    for i in range(5):

        if accountant.is_within_budget(1.0):

            accountant.add_query(1.0, sensitivity)

            print(f"   查询 {i+1}: ε消耗1.0, 剩余预算: {accountant.get_remaining_budget():.1f}")

        else:

            print(f"   查询 {i+1}: 超出预算!")





if __name__ == "__main__":

    demonstrate_mechanisms()



    print("\n" + "=" * 60)

    print("差分隐私机制演示完成!")

    print("=" * 60)

