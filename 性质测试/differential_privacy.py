# -*- coding: utf-8 -*-
"""
算法实现：性质测试 / differential_privacy

本文件实现 differential_privacy 相关的算法功能。
"""

import random
import numpy as np
from typing import Callable, List


class LaplaceMechanism:
    """Laplace机制"""

    def __init__(self, epsilon: float):
        """
        参数：
            epsilon: 隐私预算
        """
        self.epsilon = epsilon

    def add_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """
        添加Laplace噪声

        参数：
            value: 真实值
            sensitivity: 敏感度

        返回：扰动后的值
        """
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return value + noise

    def sensitivity(self, f: Callable, d1: List, d2: List) -> float:
        """
        计算函数敏感度

        返回：L1敏感度
        """
        return abs(f(d1) - f(d2))


class ExponentialMechanism:
    """指数机制"""

    def __init__(self, epsilon: float):
        """
        参数：
            epsilon: 隐私预算
        """
        self.epsilon = epsilon

    def sample(self, scores: List[float]) -> int:
        """
        从指数分布中采样

        参数：
            scores: 每个输出的分数

        返回：选中的输出索引
        """
        # 计算概率权重
        weights = np.exp(scores * self.epsilon / 2)

        # 归一化
        probs = weights / weights.sum()

        # 采样
        return np.random.choice(len(scores), p=probs)


class GaussianMechanism:
    """高斯机制"""

    def __init__(self, epsilon: float, delta: float):
        """
        参数：
            epsilon, delta: 隐私参数
        """
        self.epsilon = epsilon
        self.delta = delta

    def add_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """
        添加高斯噪声

        参数：
            value: 真实值
            sensitivity: 敏感度

        返回：扰动后的值
        """
        # 计算标准差
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon

        noise = np.random.normal(0, sigma)
        return value + noise


def privacy_accounting():
    """隐私账户"""
    print("=== 隐私账户 ===")
    print()
    print("组合定理：")
    print("  - 序列组合：ε 求和")
    print("  - 并行组合：取最大ε")
    print()
    print("交易（Trade-off）：")
    print("  - ε小 → 更多隐私，更少效用")
    print("  - ε大 → 更少隐私，更多效用")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 差分隐私机制测试 ===\n")

    epsilon = 1.0

    # Laplace机制
    laplace = LaplaceMechanism(epsilon)
    true_value = 100.0

    noisy_values = [laplace.add_noise(true_value) for _ in range(100)]
    mean_noisy = np.mean(noisy_values)
    std_noisy = np.std(noisy_values)

    print(f"Laplace机制 (ε={epsilon}):")
    print(f"  真实值: {true_value}")
    print(f"  扰动均值: {mean_noisy:.2f}")
    print(f"  扰动标准差: {std_noisy:.2f}")
    print()

    # 指数机制
    exponential = ExponentialMechanism(epsilon)
    scores = [0.5, 0.8, 0.3, 0.9, 0.6]

    counts = [0] * len(scores)
    for _ in range(1000):
        selected = exponential.sample(scores)
        counts[selected] += 1

    print("指数机制:")
    print(f"  分数: {scores}")
    print(f"  选择次数: {counts}")
    print()

    # 高斯机制
    delta = 1e-5
    gaussian = GaussianMechanism(epsilon, delta)

    noisy_gaussian = [gaussian.add_noise(true_value) for _ in range(100)]
    mean_gaussian = np.mean(noisy_gaussian)
    std_gaussian = np.std(noisy_gaussian)

    print(f"高斯机制 (ε={epsilon}, δ={delta}):")
    print(f"  真实值: {true_value}")
    print(f"  扰动均值: {mean_gaussian:.2f}")
    print(f"  扰动标准差: {std_gaussian:.2f}")

    print()
    privacy_accounting()

    print()
    print("说明：")
    print("  - 差分隐私保护数据隐私")
    print("  - Laplace适合数值查询")
    print("  - 指数机制适合离散选择")
