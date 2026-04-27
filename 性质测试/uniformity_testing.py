# -*- coding: utf-8 -*-
"""
算法实现：性质测试 / uniformity_testing

本文件实现 uniformity_testing 相关的算法功能。
"""

import random
from collections import Counter
from typing import List


class UniformityTester:
    """均匀性测试器"""

    def __init__(self, epsilon: float = 0.1):
        """
        参数：
            epsilon: 距离参数
        """
        self.epsilon = epsilon

    def test_uniformity(self, samples: List[int],
                       n_categories: int) -> Tuple[bool, float]:
        """
        测试均匀性

        参数：
            samples: 样本列表
            n_categories: 类别数

        返回：(是否均匀, p值)
        """
        n = len(samples)
        expected = n / n_categories

        # 计数
        counts = Counter(samples)

        # 计算χ²统计量
        chi_sq = 0
        for i in range(n_categories):
            observed = counts.get(i, 0)
            chi_sq += (observed - expected) ** 2 / expected

        # 自由度 = n_categories - 1
        df = n_categories - 1

        # 简化p值
        p_value = 1.0 - self._chi_sq_cdf(chi_sq, df)

        # 如果p值大于ε，接受均匀
        return p_value >= self.epsilon, p_value

    def _chi_sq_cdf(self, x: float, df: int) -> float:
        """χ²分布CDF近似"""
        import math

        if df <= 0:
            return 0.0

        # 简化近似
        return math.exp(-x / 2)


def uniformity_sample_complexity():
    """均匀性测试样本复杂度"""
    print("=== 均匀性测试复杂度 ===")
    print()
    print("样本复杂度：")
    print("  - O(√n / ε²)")
    print("  - 需要 Ω(n / ε²) 下界")
    print()
    print("算法：")
    print("  1. χ²检验")
    print("  2. 基于碰撞的检验")
    print("  3. 距离估计")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 一致均匀性测试 ===\n")

    random.seed(42)

    tester = UniformityTester(epsilon=0.1)

    # 测试1：真正均匀
    uniform_samples = [random.randint(0, 9) for _ in range(1000)]
    is_uniform, p1 = tester.test_uniformity(uniform_samples, n_categories=10)
    print(f"均匀分布样本: 均匀={is_uniform}, p={p1:.4f}")

    # 测试2：偏斜分布
    skewed_samples = [0] * 300 + [random.randint(1, 9) for _ in range(700)]
    is_skewed, p2 = tester.test_uniformity(skewed_samples, n_categories=10)
    print(f"偏斜分布样本: 均匀={is_skewed}, p={p2:.4f}")

    print()
    uniformity_sample_complexity()

    print()
    print("说明：")
    print("  - 均匀性测试是分布测试的基础")
    print("  - 常用于数据质量评估")
    print("  - 骰子、硬币、随机数生成器测试")
