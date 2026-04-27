# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / batch_bandits

本文件实现 batch_bandits 相关的算法功能。
"""

import numpy as np
import torch
import itertools
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class BatchFeedback:
    """批量反馈"""
    arms: List[int]
    rewards: List[float]


class BatchBanditBase:
    """
    批处理老虎机基类

    每批可以查询多个臂
    """

    def __init__(self, num_arms: int, batch_size: int, device: str = 'cpu'):
        """
        参数:
            num_arms: 臂数量
            batch_size: 每批可以选择的臂数
            device: 计算设备
        """
        self.num_arms = num_arms
        self.batch_size = batch_size
        self.device = device

        self.total_queries = 0
        self.total_batches = 0

    def select_batch(self) -> List[int]:
        """
        选择一批臂

        返回:
            arms: 选择的臂列表
        """
        raise NotImplementedError

    def receive_batch_reward(self, arms: List[int], rewards: List[float]):
        """
        接收批量奖励

        参数:
            arms: 臂列表
            rewards: 对应奖励列表
        """
        raise NotImplementedError


class NaiveBatchExplorer(BatchBanditBase):
    """
    朴素批处理探索器

    均匀探索所有臂
    """

    def __init__(self, num_arms: int, batch_size: int, device: str = 'cpu'):
        super().__init__(num_arms, batch_size, device)

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

    def select_batch(self) -> List[int]:
        """均匀采样一批臂"""
        self.total_batches += 1

        # 均匀随机选择
        arms = list(range(self.num_arms))
        np.random.shuffle(arms)
        return arms[:self.batch_size]

    def receive_batch_reward(self, arms: List[int], rewards: List[float]):
        """更新Q值"""
        for arm, reward in zip(arms, rewards):
            self.counts[arm] += 1
            self.total_queries += 1

            n = self.counts[arm]
            self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n


class SuccessiveHalving(BatchBanditBase):
    """
    Successive Halving算法

    用于批量老虎机的淘汰赛
    """

    def __init__(self, num_arms: int, batch_size: int, total_budget: int, device: str = 'cpu'):
        """
        参数:
            total_budget: 总查询预算
        """
        super().__init__(num_arms, batch_size, device)
        self.total_budget = total_budget
        self.current_stage = 0

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

    def _get_num_pulls_per_arm(self) -> int:
        """计算每臂每轮应拉动的次数"""
        # log(K) stages, each arm starts with n pulls
        # total pulls = K * n * log(K) = budget
        log_K = int(np.log2(self.num_arms)) + 1
        return self.total_budget // (self.num_arms * log_K)

    def select_batch(self) -> List[int]:
        """选择一批臂"""
        self.total_batches += 1

        # 当前存活的臂
        active_arms = torch.where(self.counts >= 0)[0].tolist()

        if len(active_arms) <= self.batch_size:
            return active_arms

        # 选择当前Q值最高的batch_size个臂
        q_values = [self.Q[arm].item() for arm in active_arms]
        sorted_arms = [arm for _, arm in sorted(zip(q_values, active_arms), reverse=True)]

        return sorted_arms[:self.batch_size]

    def receive_batch_reward(self, arms: List[int], rewards: List[float]):
        """更新并淘汰"""
        for arm, reward in zip(arms, rewards):
            self.counts[arm] += 1
            self.total_queries += 1

            n = self.counts[arm]
            self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n


class UCBIntervalExhaustive(BatchBanditBase):
    """
    UCB间隔穷举

    结合UCB和穷举搜索
    """

    def __init__(self, num_arms: int, batch_size: int, device: str = 'cpu'):
        super().__init__(num_arms, batch_size, device)

        self.Q = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)
        self.total_counts = 0

        # 可信区间
        self.confidence_radius = torch.zeros(num_arms, device=device)

    def _update_confidence(self):
        """更新置信半径"""
        for arm in range(self.num_arms):
            if self.counts[arm] > 0:
                self.confidence_radius[arm] = np.sqrt(
                    2 * np.log(self.total_counts) / self.counts[arm]
                )
            else:
                self.confidence_radius[arm] = float('inf')

    def select_batch(self) -> List[int]:
        """选择一批臂"""
        self.total_batches += 1
        self._update_confidence()

        # 上界
        upper_bounds = self.Q + self.confidence_radius

        # 选择上界最高的batch_size个臂
        _, top_arms = torch.topk(upper_bounds, min(self.batch_size, self.num_arms))

        return top_arms.tolist()

    def receive_batch_reward(self, arms: List[int], rewards: List[float]):
        """更新"""
        for arm, reward in zip(arms, rewards):
            self.counts[arm] += 1
            self.total_counts += 1

            n = self.counts[arm]
            self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n


class BatchThompsonSampling(BatchBanditBase):
    """
    批量Thompson Sampling
    """

    def __init__(self, num_arms: int, batch_size: int, device: str = 'cpu'):
        super().__init__(num_arms, batch_size, device)

        self.alpha = torch.ones(num_arms, device=device)
        self.beta = torch.ones(num_arms, device=device)

    def select_batch(self) -> List[int]:
        """采样并选择一批"""
        self.total_batches += 1

        # 从Beta分布采样
        samples = torch.distributions.Beta(self.alpha, self.beta).sample()

        # 选择采样值最高的batch_size个臂
        _, top_arms = torch.topk(samples, min(self.batch_size, self.num_arms))

        return top_arms.tolist()

    def receive_batch_reward(self, arms: List[int], rewards: List[float]):
        """更新后验"""
        for arm, reward in zip(arms, rewards):
            self.total_queries += 1
            self.alpha[arm] += reward
            self.beta[arm] += (1 - reward)


class DuelingBandits:
    """
    对比老虎机（Comparison Bandits）

    不提供绝对奖励，只比较两个臂的优劣
    """

    def __init__(self, num_arms: int, device: str = 'cpu'):
        self.num_arms = num_arms
        self.device = device

        # 胜负计数
        self.wins = torch.zeros(num_arms, num_arms, device=device)
        self.comparisons = torch.zeros(num_arms, num_arms, device=device)

    def compare(self, arm1: int, arm2: int) -> int:
        """
        比较两个臂

        返回:
            winner: 胜出的臂索引
        """
        # 这里需要外部提供胜负结果
        return arm1

    def record_comparison(self, arm1: int, arm2: int, winner: int):
        """记录比较结果"""
        self.comparisons[arm1, arm2] += 1
        self.comparisons[arm2, arm1] += 1

        if winner == arm1:
            self.wins[arm1, arm2] += 1
        else:
            self.wins[arm2, arm1] += 1

    def get_score(self, arm: int) -> float:
        """计算臂的得分（胜率）"""
        total = self.comparisons[arm].sum()
        if total == 0:
            return 0.5

        wins_count = self.wins[arm].sum()
        return (wins_count + 1) / (total + 2)  # 加1平滑


def solve_batch_top_k(probs: np.ndarray, k: int) -> Tuple[np.ndarray, float]:
    """
    求解批量Top-K问题（NP-hard）

    使用贪心近似

    参数:
        probs: 每个臂的期望奖励
        k: 需要选择的臂数

    返回:
        selected: 选择的臂索引
        value: 目标函数值
    """
    n = len(probs)

    if k >= n:
        return np.arange(n), probs.sum()

    # 贪心选择
    selected = []
    remaining = set(range(n))

    for _ in range(k):
        best_arm = None
        best_value = -float('inf')

        for arm in remaining:
            # 计算加入该臂后的增量价值
            value = sum(probs[s] for s in selected) + probs[arm]
            if value > best_value:
                best_value = value
                best_arm = arm

        selected.append(best_arm)
        remaining.remove(best_arm)

    return np.array(selected), best_value


def run_batch_bandit_comparison(num_arms: int = 10, batch_size: int = 3,
                                total_queries: int = 500,
                                bandit_probs: Optional[np.ndarray] = None,
                                seed: int = 42):
    """
    批处理老虎机比较
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    if bandit_probs is None:
        bandit_probs = np.random.rand(num_arms)

    print(f"臂数: {num_arms}, 批大小: {batch_size}, 总查询: {total_queries}")

    # 算法
    algorithms = {
        'Naive': NaiveBatchExplorer(num_arms, batch_size),
        'UCB-Exhaustive': UCBIntervalExhaustive(num_arms, batch_size),
        'Batch-TS': BatchThompsonSampling(num_arms, batch_size)
    }

    results = {}

    for name, algo in algorithms.items():
        total_reward = 0
        batches = 0

        while algo.total_queries < total_queries:
            arms = algo.select_batch()
            rewards = [1.0 if np.random.rand() < bandit_probs[arm] else 0.0 for arm in arms]

            algo.receive_batch_reward(arms, rewards)
            total_reward += sum(rewards)
            batches += 1

        results[name] = {
            'total_reward': total_reward,
            'total_batches': batches,
            'efficiency': total_reward / batches
        }

        print(f"{name}: 奖励={total_reward}, 批次数={batches}, 效率={total_reward/batches:.2f}")

    return results


if __name__ == "__main__":
    print("=" * 50)
    print("批处理老虎机测试")
    print("=" * 50)

    # 测试批处理算法
    print("\n--- 批处理算法比较 ---")
    run_batch_bandit_comparison(num_arms=8, batch_size=2, total_queries=200)

    # 测试Top-K求解
    print("\n--- Top-K问题 ---")
    probs = np.random.rand(10)
    print(f"概率: {probs}")

    for k in [2, 3, 5]:
        selected, value = solve_batch_top_k(probs, k)
        print(f"Top-{k}: 臂={selected}, 价值和={value:.2f}")

    print("\n测试完成！")
