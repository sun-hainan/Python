# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / gittins_index

本文件实现 gittins_index 相关的算法功能。
"""

import numpy as np
import torch
import math
from typing import List, Tuple, Optional


class GittinsIndexCalculator:
    """
    Gittins指数计算器

    Gittins指数用于折扣随机老虎机问题
    """

    def __init__(self, num_arms: int, discount: float = 0.9, device: str = 'cpu'):
        """
        参数:
            discount: 折扣因子 (0 < discount < 1)
        """
        self.num_arms = num_arms
        self.discount = discount
        self.device = device

        # Beta先验参数
        self.alpha = torch.ones(num_arms, device=device)
        self.beta = torch.ones(num_arms, device=device)

    def compute_index(self, arm: int) -> float:
        """
        计算单个臂的Gittins指数

        使用Beta-Bernoulli模型的闭式解

        参数:
            arm: 臂索引

        返回:
            index: Gittins指数值
        """
        a = self.alpha[arm].item()
        b = self.beta[arm].item()

        # Gittins指数 = (a - 1) / (a + b - 2) 当 discount -> 1
        # 对于折扣问题，使用迭代方法

        if a <= 1 or b <= 1:
            return float('inf')

        # 简化：使用后验均值作为索引
        # 完整的Gittins指数需要更复杂的计算
        return (a - 1) / (a + b - 2)

    def compute_all_indices(self) -> np.ndarray:
        """计算所有臂的Gittins指数"""
        indices = []
        for arm in range(self.num_arms):
            indices.append(self.compute_index(arm))

        return np.array(indices)

    def select_arm(self) -> int:
        """选择Gittins指数最高的臂"""
        indices = self.compute_all_indices()
        return int(np.argmax(indices))

    def update(self, arm: int, reward: float):
        """更新后验"""
        self.alpha[arm] += reward
        self.beta[arm] += (1 - reward)


class DiscountedMAB:
    """
    折扣多臂老虎机

    折扣因子gamma使未来的奖励贬值
    """

    def __init__(self, num_arms: int, gamma: float = 0.9, device: str = 'cpu'):
        self.num_arms = num_arms
        self.gamma = gamma
        self.device = device

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.total_discounted_counts = torch.zeros(num_arms, device=device)

    def select_arm(self) -> int:
        """选择臂"""
        return torch.argmax(self.Q).item()

    def update(self, arm: int, reward: float, step: int):
        """折扣更新"""
        self.counts[arm] += 1
        self.total_discounted_counts[arm] = self.gamma * self.total_discounted_counts[arm] + 1

        # 折扣更新
        discount_factor = self.gamma ** step
        self.Q[arm] = (self.Q[arm] * (self.counts[arm] - 1) + reward * discount_factor) / self.counts[arm]


class DiscountedThompsonSampling:
    """
    折扣Thompson Sampling
    """

    def __init__(self, num_arms: int, gamma: float = 0.9, device: str = 'cpu'):
        self.num_arms = num_arms
        self.gamma = gamma
        self.device = device

        self.alpha = torch.ones(num_arms, device=device)
        self.beta = torch.ones(num_arms, device=device)

    def select_arm(self) -> int:
        """采样并选择"""
        samples = torch.distributions.Beta(self.alpha, self.beta).sample()
        return torch.argmax(samples).item()

    def update(self, arm: int, reward: float, step: int):
        """折扣更新"""
        discount = self.gamma ** step

        self.alpha[arm] *= discount
        self.beta[arm] *= discount

        self.alpha[arm] += reward
        self.beta[arm] += (1 - reward)


class DiscountedUCB:
    """
    折扣UCB
    """

    def __init__(self, num_arms: int, gamma: float = 0.9, device: str = 'cpu'):
        self.num_arms = num_arms
        self.gamma = gamma
        self.device = device

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

    def select_arm(self) -> int:
        """选择臂"""
        # 初始化阶段
        for arm in range(self.num_arms):
            if self.counts[arm] == 0:
                return arm

        # UCB
        t = self.counts.sum().item() + 1
        ucb_values = self.Q + torch.sqrt(
            2 * torch.log(t) / self.counts
        )

        return torch.argmax(ucb_values).item()

    def update(self, arm: int, reward: float, step: int):
        """更新"""
        self.counts[arm] += 1

        n = self.counts[arm]
        discount_factor = self.gamma ** step

        self.Q[arm] = (self.Q[arm] * (n - 1) + reward * discount_factor) / n


def compute_gittins_index(a: int, b: int, discount: float, precision: float = 1e-6) -> float:
    """
    计算Beta-Bernoulli模型的Gittins指数（数值方法）

    参数:
        a: Beta先验alpha
        b: Beta先验beta
        discount: 折扣因子
        precision: 精度

    返回:
        Gittins指数
    """
    if a <= 1 or b <= 1:
        return float('inf')

    # 二分搜索
    low, high = 0.0, 1.0

    while high - low > precision:
        mid = (low + high) / 2

        # 计算在指数=mid时的预期折扣回报
        # 简化计算
        expected_return = (a - 1) / (a + b - 2)

        if expected_return > mid:
            low = mid
        else:
            high = mid

    return (low + high) / 2


def run_discounted_comparison(num_arms: int = 5, horizon: int = 1000,
                             gamma: float = 0.95, seed: int = 42):
    """
    折扣老虎机算法比较
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    true_probs = np.random.rand(num_arms)

    print(f"折扣因子: {gamma}")
    print(f"真实概率: {true_probs}")

    algorithms = {
        'Gittins': GittinsIndexCalculator(num_arms, gamma),
        'Discounted-UCB': DiscountedUCB(num_arms, gamma),
        'Discounted-TS': DiscountedThompsonSampling(num_arms, gamma)
    }

    results = {}

    for name, algo in algorithms.items():
        total_discounted_reward = 0.0

        for step in range(horizon):
            arm = algo.select_arm()
            reward = 1.0 if np.random.rand() < true_probs[arm] else 0.0

            if hasattr(algo, 'update'):
                if 'Gittins' in name:
                    algo.update(arm, reward)
                else:
                    algo.update(arm, reward, step)

            # 计算折扣奖励
            discounted = reward * (gamma ** step)
            total_discounted_reward += discounted

        results[name] = {
            'total_discounted_reward': total_discounted_reward,
            'total_undiscounted': 0  # 后续计算
        }

        print(f"{name}: 折扣奖励={total_discounted_reward:.4f}")

    return results


if __name__ == "__main__":
    print("=" * 50)
    print("随机老虎机测试（Gittins指数）")
    print("=" * 50)

    # Gittins指数测试
    print("\n--- Gittins指数 ---")
    gittins = GittinsIndexCalculator(num_arms=5, discount=0.9)

    print(f"初始后验: alpha={gittins.alpha.numpy()}, beta={gittins.beta.numpy()}")
    print(f"初始指数: {gittins.compute_all_indices()}")

    # 更新一些臂
    for arm in range(5):
        for _ in range(10):
            reward = 1.0 if np.random.rand() < 0.3 + arm * 0.1 else 0.0
            gittins.update(arm, reward)

    print(f"更新后后验: alpha={gittins.alpha.numpy()}, beta={gittins.beta.numpy()}")
    print(f"更新后指数: {gittins.compute_all_indices()}")

    # 折扣算法比较
    print("\n--- 折扣老虎机比较 ---")
    run_discounted_comparison(num_arms=5, horizon=500, gamma=0.95)

    print("\n测试完成！")
