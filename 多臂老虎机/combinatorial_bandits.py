# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / combinatorial_bandits

本文件实现 combinatorial_bandits 相关的算法功能。
"""

import numpy as np
import torch
import math
from typing import List, Tuple, Set, Optional, Dict


class CombinatorialBanditBase:
    """
    组合老虎机基类
    """

    def __init__(self, num_base_arms: int, max_selection: int, device: str = 'cpu'):
        """
        参数:
            num_base_arms: 基础臂数量
            max_selection: 每次最多选择的臂数
            device: 计算设备
        """
        self.num_base_arms = num_base_arms
        self.max_selection = max_selection
        self.device = device

        self.total_pulls = 0

    def select_superset(self) -> List[int]:
        """选择一组臂"""
        raise NotImplementedError

    def receive_reward(self, arms: List[int], reward: float):
        """接收奖励"""
        raise NotImplementedError


class EpsGreedyCombinatorial(CombinatorialBanditBase):
    """
    Epsilon-Greedy组合老虎机
    """

    def __init__(self, num_base_arms: int, max_selection: int, epsilon: float = 0.1, device: str = 'cpu'):
        super().__init__(num_base_arms, max_selection, device)
        self.epsilon = epsilon

        # 基础臂的Q值
        self.Q = torch.zeros(num_base_arms, device=device)
        self.counts = torch.zeros(num_base_arms, device=device, dtype=torch.long)

    def select_superset(self) -> List[int]:
        """选择臂集合"""
        if np.random.rand() < self.epsilon:
            # 探索：随机选择
            arms = list(range(self.num_base_arms))
            np.random.shuffle(arms)
            return arms[:self.max_selection]
        else:
            # 利用：选择Q值最高的臂
            _, top_arms = torch.topk(self.Q, self.max_selection)
            return top_arms.tolist()

    def receive_reward(self, arms: List[int], reward: float):
        """更新（奖励按基础臂平均分配）"""
        self.total_pulls += 1
        reward_per_arm = reward / len(arms)

        for arm in arms:
            self.counts[arm] += 1
            n = self.counts[arm]
            self.Q[arm] = self.Q[arm] + (reward_per_arm - self.Q[arm]) / n


class CUCB(CombinatorialUCB):
    """
    CUCB (Combinatorial UCB) 算法
    """

    def __init__(self, num_base_arms: int, max_selection: int, horizon: int, device: str = 'cpu'):
        super().__init__(num_base_arms, max_selection, device)
        self.horizon = horizon

        self.Q = torch.zeros(num_base_arms, device=device)
        self.counts = torch.zeros(num_base_arms, device=device, dtype=torch.long)

    def _compute_confidence(self, arm: int) -> float:
        """计算UCB置信项"""
        if self.counts[arm] == 0:
            return float('inf')

        return math.sqrt(
            2 * math.log(self.horizon) / self.counts[arm]
        )

    def select_superset(self) -> List[int]:
        """选择上界最高的臂集合"""
        ucb_values = self.Q + torch.tensor(
            [self._compute_confidence(arm) for arm in range(self.num_base_arms)],
            device=self.device
        )

        _, top_arms = torch.topk(ucb_values, self.max_selection)
        return top_arms.tolist()

    def receive_reward(self, arms: List[int], reward: float):
        """更新"""
        self.total_pulls += 1
        reward_per_arm = reward / len(arms)

        for arm in arms:
            self.counts[arm] += 1
            n = self.counts[arm]
            self.Q[arm] = self.Q[arm] + (reward_per_arm - self.Q[arm]) / n


class ThompsonSamplingCombinatorial(CombinatorialBanditBase):
    """
    组合老虎机的Thompson Sampling
    """

    def __init__(self, num_base_arms: int, max_selection: int, device: str = 'cpu'):
        super().__init__(num_base_arms, max_selection, device)

        self.alpha = torch.ones(num_base_arms, device=device)
        self.beta = torch.ones(num_base_arms, device=device)

    def select_superset(self) -> List[int]:
        """从后验采样并选择"""
        # 采样每个臂的均值
        samples = torch.distributions.Beta(self.alpha, self.beta).sample()

        # 选择采样值最高的max_selection个臂
        _, top_arms = torch.topk(samples, self.max_selection)
        return top_arms.tolist()

    def receive_reward(self, arms: List[int], reward: float):
        """更新后验"""
        self.total_pulls += 1
        reward_per_arm = reward / len(arms)

        for arm in arms:
            self.alpha[arm] += reward_per_arm
            self.beta[arm] += (1 - reward_per_arm)


class SubsetSelection:
    """
    子集选择问题

    给定一组臂，选择能够最大化某个目标函数的子集
    """

    def __init__(self, num_arms: int, k: int, device: str = 'cpu'):
        """
        参数:
            k: 子集大小
        """
        self.num_arms = num_arms
        self.k = k
        self.device = device

        self.estimates = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

    def greedy_select(self) -> List[int]:
        """贪心选择"""
        _, top_k = torch.topk(self.estimates, self.k)
        return top_k.tolist()

    def update(self, arm: int, reward: float):
        """更新估计"""
        self.counts[arm] += 1
        n = self.counts[arm]
        self.estimates[arm] = self.estimates[arm] + (reward - self.estimates[arm]) / n


class UCBVI:
    """
    UCB-VI (Upper Confidence Bound with Value Iteration)

    适用于MDP或组合动作空间
    """

    def __init__(self, num_states: int, num_actions: int, gamma: float = 0.9, device: str = 'cpu'):
        """
        参数:
            num_states: 状态数
            num_actions: 动作数
            gamma: 折扣因子
        """
        self.num_states = num_states
        self.num_actions = num_actions
        self.gamma = gamma
        self.device = device

        # Q函数
        self.Q = torch.zeros(num_states, num_actions, device=device)
        self.counts = torch.zeros(num_states, num_actions, device=device, dtype=torch.long)

    def select_action(self, state: int) -> int:
        """选择动作"""
        ucb_values = self.Q[state] + torch.sqrt(
            2 * torch.log(torch.sum(self.counts[state]) + 1) / (self.counts[state] + 1e-10)
        )
        return torch.argmax(ucb_values).item()

    def update(self, state: int, action: int, reward: float, next_state: int):
        """更新Q函数"""
        self.counts[state, action] += 1

        # TD更新
        td_target = reward + self.gamma * torch.max(self.Q[next_state])
        n = self.counts[state, action].item()
        self.Q[state, action] = self.Q[state, action] + (td_target - self.Q[state, action]) / n


def run_combinatorial_comparison(num_arms: int = 10, max_selection: int = 3,
                                horizon: int = 1000, seed: int = 42):
    """
    组合老虎机算法比较
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    # 真实概率
    true_probs = np.random.rand(num_arms)

    print(f"基础臂数: {num_arms}, 选择数: {max_selection}")
    print(f"真实概率: {true_probs}")

    algorithms = {
        'EpsGreedy': EpsGreedyCombinatorial(num_arms, max_selection, epsilon=0.1),
        'CUCB': CUCB(num_arms, max_selection, horizon),
        'Thompson': ThompsonSamplingCombinatorial(num_arms, max_selection)
    }

    results = {}

    for name, algo in algorithms.items():
        total_reward = 0

        for step in range(horizon):
            # 选择臂集合
            arms = algo.select_superset()

            # 生成奖励（组合奖励 = 所选臂的平均概率）
            reward = 1.0 if np.random.rand() < true_probs[arms].mean() else 0.0

            algo.receive_reward(arms, reward)
            total_reward += reward

        results[name] = {
            'total_reward': total_reward,
            'avg_reward': total_reward / horizon
        }

        print(f"{name}: 总奖励={total_reward}, 平均={results[name]['avg_reward']:.4f}")

    return results


if __name__ == "__main__":
    print("=" * 50)
    print("组合老虎机测试（CUCB）")
    print("=" * 50)

    # 组合老虎机测试
    print("\n--- 组合老虎机算法比较 ---")
    run_combinatorial_comparison(num_arms=10, max_selection=3, horizon=500)

    # 子集选择测试
    print("\n--- 子集选择 ---")
    subset_selector = SubsetSelection(num_arms=10, k=3)

    # 模拟运行
    true_probs = np.random.rand(10)
    optimal_subset = set(np.argsort(true_probs)[-3:])

    print(f"真实概率: {true_probs}")
    print(f"最优3臂: {optimal_subset}")

    for step in range(500):
        # 贪心选择
        selected = subset_selector.greedy_select()

        # 奖励
        reward = 1.0 if set(selected) == optimal_subset else 0.0

        for arm in selected:
            subset_selector.update(arm, reward)

    print(f"估计概率: {subset_selector.estimates.numpy()}")

    print("\n测试完成！")
