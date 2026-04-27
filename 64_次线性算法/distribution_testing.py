# -*- coding: utf-8 -*-

"""

算法实现：次线性算法 / distribution_testing



本文件实现 distribution_testing 相关的算法功能。

"""



import random

from typing import List, Tuple

from collections import Counter





class DistributionTester:

    """分布测试器"""



    def __init__(self, epsilon: float = 0.1):

        self.epsilon = epsilon



    def chi_squared_test(self, observed: List[int],

                        expected_probs: List[float]) -> Tuple[bool, float]:

        """

        卡方检验



        参数：

            observed: 观察到的频数

            expected_probs: 期望概率分布



        返回：(是否通过, p值)

        """

        n = sum(observed)

        expected = [n * p for p in expected_probs]



        chi_sq = sum((o - e) ** 2 / e for o, e in zip(observed, expected)

                     if e > 0)



        # 自由度 = k - 1 - r（k类别数，r估计参数数）

        df = len(observed) - 1



        # 简化p值计算

        p_value = self._chi_sq_cdf(chi_sq, df)



        # 如果p值 < ε，拒绝原假设

        return p_value >= self.epsilon, p_value



    def _chi_sq_cdf(self, x: float, df: int) -> float:

        """卡方分布CDF的近似"""

        import math

        # 简化近似

        if df <= 0:

            return 0.0



        # 使用不完全伽马函数近似

        return math.exp(-x / 2) if df == 2 else 0.5





class UniformityTester:

    """均匀性测试"""



    def test_uniformity(self, samples: List[int], n_categories: int) -> bool:

        """

        测试是否均匀分布



        参数：

            samples: 样本列表

            n_categories: 类别数



        返回：是否均匀

        """

        n = len(samples)

        expected = n / n_categories



        counts = Counter(samples)

        observed = [counts.get(i, 0) for i in range(n_categories)]



        # 计算与均匀分布的距离

        total_variation = sum(abs(c - expected) for c in observed) / 2



        # 如果距离 > εn，则不均匀

        return total_variation <= self.epsilon * n





class IdentityTester:

    """分布同一性测试"""



    def test_identity(self, samples1: List[int], samples2: List[int]) -> bool:

        """

        测试两个分布是否相同



        参数：

            samples1: 样本1

            samples2: 样本2



        返回：是否相同

        """

        n1, n2 = len(samples1), len(samples2)

        total_n = n1 + n2



        # 合并样本

        all_samples = samples1 + samples2



        # 计算Kolmogorov-Smirnov统计量

        # 简化版本

        max_diff = 0.0



        # 使用频率向量

        combined_counts = Counter(all_samples)

        unique_vals = list(combined_counts.keys())



        for val in unique_vals:

            f1 = samples1.count(val) / n1 if n1 > 0 else 0

            f2 = samples2.count(val) / n2 if n2 > 0 else 0

            diff = abs(f1 - f2)

            max_diff = max(max_diff, diff)



        return max_diff <= self.epsilon





def distribution_testing_framework():

    """分布测试框架"""

    print("=== 分布测试框架 ===")

    print()

    print("模型：")

    print("  - 样本访问：只能看到独立同分布样本")

    print("  - 测试目标：判断样本是否来自某分布")

    print()

    print("核心算法：")

    print("  1. 卡方检验：测试类别分布")

    print("  2. Kolmogorov-Smirnov：测试连续分布")

    print("  3. Wasserstein距离：测量分布差异")

    print()

    print("样本复杂度：")

    print("  - 类别分布：O(√n / ε²)")

    print("  - 连续分布：O(1 / ε²)")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 分布测试测试 ===\n")



    random.seed(42)



    # 测试均匀性

    print("均匀性测试：")

    tester = DistributionTester(epsilon=0.1)



    # 均匀分布样本

    uniform_samples = [random.randint(0, 4) for _ in range(1000)]

    ut = UniformityTester()

    is_uniform = ut.test_uniformity(uniform_samples, n_categories=5)

    print(f"  均匀分布样本: {'均匀' if is_uniform else '不均匀'}")



    # 非均匀样本

    biased_samples = [0] * 300 + [1] * 200 + [2] * 150 + [3] * 150 + [4] * 200

    is_biased = ut.test_uniformity(biased_samples, n_categories=5)

    print(f"  偏斜分布样本: {'均匀' if is_biased else '不均匀'}")



    print()



    # 测试同一性

    print("分布同一性测试：")

    samples1 = [random.randint(0, 3) for _ in range(500)]

    samples2 = [random.randint(0, 3) for _ in range(500)]



    it = IdentityTester()

    same = it.test_identity(samples1, samples2)

    print(f"  两个相同分布: {'相同' if same else '不同'}")



    print()

    distribution_testing_framework()



    print()

    print("说明：")

    print("  - 分布测试是统计学习的重要工具")

    print("  - 常用于异常检测、数据质量评估")

    print("  - 在大数据时代用于采样验证")

