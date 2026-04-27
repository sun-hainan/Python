# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / ucb_algorithms

本文件实现 ucb_algorithms 相关的算法功能。
"""

import numpy as np
import torch
import math
from typing import List, Optional


class UCB1:
    """
    UCB1算法

    经典UCB算法，理论遗憾度O(sqrt(KT log T))
    """

    def __init__(self, num_arms, c=2.0, device='cpu'):
        """
        参数:
            num_arms: 臂数
            c: 探索常数（通常为2）
            device: 计算设备
        """
        self.num_arms = num_arms
        self.c = c
        self.device = device

        # Q值估计
        self.Q = torch.zeros(num_arms, device=device)
        # 计数
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.total_counts = 0

    def select_arm(self) -> int:
        """
        选择臂

        公式: argmax [ Q(a) + c * sqrt(log(t) / N(a)) ]
        """
        # 初始化阶段：确保每个臂都被选择
        if self.total_counts < self.num_arms:
            return self.total_counts

        # 计算UCB
        ucb_values = torch.zeros(self.num_arms, device=self.device)

        for arm in range(self.num_arms):
            if self.counts[arm] > 0:
                exploration = self.c * math.sqrt(
                    math.log(self.total_counts) / self.counts[arm]
                )
                ucb_values[arm] = self.Q[arm] + exploration
            else:
                # 未选择的臂给予极大值
                ucb_values[arm] = float('inf')

        return torch.argmax(ucb_values).item()

    def update(self, arm: int, reward: float):
        """
        更新Q值

        参数:
            arm: 选择的臂索引
            reward: 获得的奖励
        """
        self.counts[arm] += 1
        self.total_counts += 1

        # 增量更新
        n = self.counts[arm]
        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n

    def get_estimated_values(self) -> np.ndarray:
        """获取估计值"""
        return self.Q.cpu().numpy()

    def get_confidence_bounds(self) -> tuple:
        """
        获取置信边界

        返回:
            (lower_bounds, upper_bounds)
        """
        lower = torch.zeros(self.num_arms)
        upper = torch.zeros(self.num_arms)

        for arm in range(self.num_arms):
            if self.counts[arm] > 0:
                exploration = self.c * math.sqrt(
                    math.log(self.total_counts) / self.counts[arm]
                )
                lower[arm] = self.Q[arm] - exploration
                upper[arm] = self.Q[arm] + exploration

        return lower.cpu().numpy(), upper.cpu().numpy()


class UCB2:
    """
    UCB2算法

    UCB的改进版本，通过控制选择间隔来减少方差
    """

    def __init__(self, num_arms, alpha=0.5, device='cpu'):
        """
        参数:
            alpha: 间隔控制参数 (0 < alpha < 1)
        """
        self.num_arms = num_arms
        self.alpha = alpha
        self.device = device

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.r = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.total_counts = 0

    def select_arm(self) -> int:
        """选择臂"""
        if self.total_counts < self.num_arms:
            return self.total_counts

        ucb_values = torch.zeros(self.num_arms, device=self.device)

        for arm in range(self.num_arms):
            if self.counts[arm] > 0:
                tau = self._compute_tau(arm)
                exploration = math.sqrt(
                    (1 + self.alpha) * math.log(math.e * self.total_counts / tau) / tau
                )
                ucb_values[arm] = self.Q[arm] + exploration
            else:
                ucb_values[arm] = float('inf')

        return torch.argmax(ucb_values).item()

    def _compute_tau(self, arm: int) -> int:
        """计算选择间隔"""
        r = self.r[arm].item()
        return math.ceil((1 + self.alpha) ** r)

    def update(self, arm: int, reward: float):
        """更新"""
        self.counts[arm] += 1
        self.total_counts += 1

        n = self.counts[arm]
        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n

        # 更新r
        expected_counts = math.ceil((1 + self.alpha) ** (self.r[arm] + 1))
        if self.counts[arm] >= expected_counts:
            self.r[arm] += 1


class UCBV:
    """
    UCB-V算法

    使用经验方差估计的UCB变体
    """

    def __init__(self, num_arms, c=1.0, device='cpu'):
        self.num_arms = num_arms
        self.c = c
        self.device = device

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.total_counts = 0

        # 方差估计
        self.variance = torch.zeros(num_arms, device=device)

    def select_arm(self) -> int:
        """选择臂"""
        if self.total_counts < self.num_arms:
            return self.total_counts

        ucb_values = torch.zeros(self.num_arms, device=self.device)

        for arm in range(self.num_arms):
            if self.counts[arm] > 0:
                log_term = math.log(self.total_counts) / self.counts[arm]
                var_term = self.variance[arm] + 2 * self.c * log_term
                exploration = math.sqrt(var_term * log_term)
                ucb_values[arm] = self.q[arm] + exploration

        return torch.argmax(ucb_values).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.counts[arm] += 1
        self.total_counts += 1

        n = self.counts[arm]

        # 更新均值
        old_Q = self.Q[arm].item()
        self.Q[arm] = old_Q + (reward - old_Q) / n

        # 更新方差（增量形式）
        self.variance[arm] = ((n - 1) * self.variance[arm] + (reward - old_Q) * (reward - self.Q[arm])) / n


class MOSS:
    """
    MOSS (Minimax Optimal Strategy in the Stochastic regime)

    专为有限臂老虎机设计的最优UCB变体
    """

    def __init__(self, num_arms, horizon=None, device='cpu'):
        """
        参数:
            horizon: 时间范围T（用于计算常数）
        """
        self.num_arms = num_arms
        self.horizon = horizon
        self.device = device

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.total_counts = 0

    def select_arm(self) -> int:
        """选择臂"""
        if self.total_counts < self.num_arms:
            return self.total_counts

        ucb_values = torch.zeros(self.num_arms, device=self.device)

        if self.horizon:
            log_term = math.log(self.horizon / self.num_arms)
        else:
            log_term = math.log(self.total_counts)

        for arm in range(self.num_arms):
            exploration = math.sqrt(log_term / self.counts[arm])
            ucb_values[arm] = self.Q[arm] + exploration

        return torch.argmax(ucb_values).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.counts[arm] += 1
        self.total_counts += 1

        n = self.counts[arm]
        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n


class KLUCB:
    """
    KL-UCB算法

    使用KL散度代替均方误差作为置信度量
    """

    def __init__(self, num_arms, device='cpu', max_iter=100):
        self.num_arms = num_arms
        self.device = device
        self.max_iter = max_iter

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.total_counts = 0

    def _kl_divergence(self, p: float, q: float) -> float:
        """计算伯努利分布的KL散度"""
        if p == 0:
            return (1 - p) * math.log((1 - p) / (1 - q + 1e-10))
        elif p == 1:
            return p * math.log(p / (q + 1e-10))
        else:
            return p * math.log(p / (q + 1e-10)) + (1 - p) * math.log((1 - p) / (1 - q + 1e-10))

    def _find_ucb_limit(self, arm: int, target: float) -> float:
        """
        找到满足KL(q_hat, q) = target的最大q

        使用二分搜索
        """
        q_hat = self.Q[arm].item()
        low = q_hat
        high = 1.0

        for _ in range(self.max_iter):
            mid = (low + high) / 2
            kl = self._kl_divergence(q_hat, mid)

            if kl < target:
                low = mid
            else:
                high = mid

        return (low + high) / 2

    def select_arm(self) -> int:
        """选择臂"""
        if self.total_counts < self.num_arms:
            return self.total_counts

        ucb_values = torch.zeros(self.num_arms, device=self.device)
        target = math.log(self.total_counts) + 3 * math.log(math.log(self.total_counts) + 1e-10)

        for arm in range(self.num_arms):
            ucb_values[arm] = self._find_ucb_limit(arm, target / self.counts[arm])

        return torch.argmax(ucb_values).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.counts[arm] += 1
        self.total_counts += 1

        n = self.counts[arm]
        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n


def run_ucb_comparison(num_arms=5, num_steps=1000, bandit_probs=None, seed=42):
    """
    比较不同UCB变体

    参数:
        bandit_probs: 真实概率
        seed: 随机种子
    """
    np.random.seed(seed)
    random.seed(seed)

    if bandit_probs is None:
        bandit_probs = np.random.rand(num_arms)

    print(f"真实概率: {bandit_probs}")

    results = {}

    # UCB1
    agent1 = UCB1(num_arms, c=2.0)
    rewards_ucb1 = []
    for _ in range(num_steps):
        arm = agent1.select_arm()
        reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0
        agent1.update(arm, reward)
        rewards_ucb1.append(reward)

    results['UCB1'] = {
        'total_reward': sum(rewards_ucb1),
        'estimated': agent1.get_estimated_values()
    }
    print(f"\nUCB1: 总奖励={results['UCB1']['total_reward']}, 估计={results['UCB1']['estimated']}")

    # MOSS
    agent2 = MOSS(num_arms, horizon=num_steps)
    rewards_moss = []
    for _ in range(num_steps):
        arm = agent2.select_arm()
        reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0
        agent2.update(arm, reward)
        rewards_moss.append(reward)

    results['MOSS'] = {
        'total_reward': sum(rewards_moss),
        'estimated': agent2.get_estimated_values()
    }
    print(f"MOSS: 总奖励={results['MOSS']['total_reward']}, 估计={results['MOSS']['estimated']}")

    return results


if __name__ == "__main__":
    import random

    print("=" * 50)
    print("UCB算法测试")
    print("=" * 50)

    # 测试UCB1
    print("\n--- UCB1 ---")
    num_arms = 5
    true_probs = np.random.rand(num_arms)
    print(f"真实概率: {true_probs}")

    agent = UCB1(num_arms, c=2.0)

    total_reward = 0
    for step in range(500):
        arm = agent.select_arm()
        reward = 1.0 if random.random() < true_probs[arm] else 0.0
        agent.update(arm, reward)
        total_reward += reward

    print(f"总奖励: {total_reward}")
    print(f"估计值: {agent.get_estimated_values()}")

    lower, upper = agent.get_confidence_bounds()
    print(f"95%置信区间:")
    for i in range(num_arms):
        print(f"  臂{i}: [{lower[i]:.4f}, {upper[i]:.4f}]")

    # 比较UCB变体
    print("\n--- UCB算法比较 ---")
    run_ucb_comparison(num_arms=5, num_steps=500)

    print("\n测试完成！")
