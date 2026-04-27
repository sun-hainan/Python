# -*- coding: utf-8 -*-
"""
算法实现：差分隐私 / dp_machine_learning

本文件实现 dp_machine_learning 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class DPGradientDescent:
    """差分隐私梯度下降"""

    def __init__(self, epsilon: float, delta: float, clip_bound: float = 1.0):
        """
        参数：
            epsilon: 隐私预算
            delta: 隐私参数
            clip_bound: 梯度裁剪界限
        """
        self.epsilon = epsilon
        self.delta = delta
        self.clip_bound = clip_bound

    def compute_gradient(self, X: np.ndarray, y: np.ndarray,
                        weights: np.ndarray) -> np.ndarray:
        """
        计算梯度

        返回：梯度
        """
        # 线性回归梯度
        predictions = X @ weights
        error = predictions - y

        gradient = X.T @ error / len(y)

        return gradient

    def clip_gradient(self, gradient: np.ndarray) -> np.ndarray:
        """
        梯度裁剪

        返回：裁剪后的梯度
        """
        norm = np.linalg.norm(gradient)

        if norm > self.clip_bound:
            gradient = gradient * (self.clip_bound / norm)

        return gradient

    def add_noise(self, gradient: np.ndarray, sensitivity: float) -> np.ndarray:
        """
        添加高斯噪声

        返回：扰动后的梯度
        """
        std = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon

        noise = np.random.normal(0, std, gradient.shape)

        return gradient + noise

    def train_step(self, X: np.ndarray, y: np.ndarray,
                  weights: np.ndarray, learning_rate: float) -> np.ndarray:
        """
        单步训练

        返回：更新后的权重
        """
        # 计算梯度
        gradient = self.compute_gradient(X, y, weights)

        # 裁剪
        clipped_gradient = self.clip_gradient(gradient)

        # 添加噪声
        noisy_gradient = self.add_noise(clipped_gradient, self.clip_bound)

        # 更新
        weights = weights - learning_rate * noisy_gradient

        return weights


def privacy_utility_tradeoff():
    """隐私-效用权衡"""
    print("=== 隐私-效用权衡 ===")
    print()
    print("ε 的影响：")
    print("  - ε小 → 更私有，梯度噪声大")
    print("  - ε大 → 噪声小，效用高")
    print()
    print("实际建议：")
    print("  - ε = 8 适用于研究")
    print("  - ε = 1 适用于产品")
    print("  - ε < 1 需要专业隐私团队")
    print()
    print("噪声放大：")
    print("  - 批量越大，噪声影响越小")
    print("  - 梯度平均减少噪声")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 差分隐私机器学习测试 ===\n")

    np.random.seed(42)

    # 参数
    epsilon = 1.0
    delta = 1e-5

    dp_sgd = DPGradientDescent(epsilon, delta)

    # 简单数据
    X = np.random.randn(100, 5)
    y = X @ np.array([1, -2, 0.5, 3, -1]) + np.random.randn(100) * 0.1

    # 初始权重
    weights = np.zeros(5)

    print(f"数据: {X.shape}")
    print(f"隐私: ε={epsilon}, δ={delta}")
    print()

    # 训练几步
    learning_rate = 0.01

    for epoch in range(3):
        weights = dp_sgd.train_step(X, y, weights, learning_rate)

        # 计算损失
        predictions = X @ weights
        loss = np.mean((predictions - y) ** 2)

        print(f"Epoch {epoch+1}: 损失={loss:.4f}")

    print()
    print("隐私保护ML：")
    print("  - DP-SGD是主要方法")
    print("  - 裁剪和噪声注入是核心")
    print("  - 隐私预算有限，需要仔细分配")

    print()
    privacy_utility_tradeoff()

    print()
    print("说明：")
    print("  - 差分隐私保护训练数据")
    print("  - 隐私预算消耗是累积的")
    print("  - 需要在隐私和效用间权衡")
