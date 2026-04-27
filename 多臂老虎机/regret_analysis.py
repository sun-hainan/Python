# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / regret_analysis

本文件实现 regret_analysis 相关的算法功能。
"""

import numpy as np
import torch
import math
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt


class RegretCalculator:
    """
    遗憾度计算器
    """

    def __init__(self, num_arms: int, true_probs: np.ndarray, device: str = 'cpu'):
        """
        参数:
            num_arms: 臂数量
            true_probs: 每个臂的真实期望奖励
            device: 计算设备
        """
        self.num_arms = num_arms
        self.true_probs = true_probs
        self.device = device

        self.optimal_arm = np.argmax(true_probs)
        self.optimal_prob = max(true_probs)

        self.history = {
            'rewards': [],
            'arms': [],
            'regrets': []
        }

    def add_result(self, arm: int, reward: float):
        """添加一轮结果"""
        self.history['arms'].append(arm)
        self.history['rewards'].append(reward)

        # 计算即时遗憾
        instantaneous_regret = self.optimal_prob - reward
        cumulative_regret = sum(self.history['regrets']) + instantaneous_regret
        self.history['regrets'].append(cumulative_regret)

    def get_cumulative_regret(self) -> np.ndarray:
        """获取累计遗憾序列"""
        return np.array(self.history['regrets'])

    def get_total_regret(self) -> float:
        """获取总遗憾"""
        return self.history['regrets'][-1] if self.history['regrets'] else 0.0

    def get_optimality_gap(self) -> float:
        """
        最优性差距

        期望最优动作比例 vs 实际
        """
        if not self.history['arms']:
            return 0.0

        optimal_selections = sum(1 for arm in self.history['arms'] if arm == self.optimal_arm)
        return optimal_selections / len(self.history['arms'])


class SubGaussianRegret:
    """
    次高斯奖励的遗憾界

    适用于方差有界的奖励分布
    """

    @staticmethod
    def ucb_regret(T: int, K: int, delta: float = 0.1) -> float:
        """
        UCB的遗憾上界

        O(sqrt(K * T * log(T)))
        """
        return np.sqrt(2 * K * T * math.log(T / delta))

    @staticmethod
    def kl_ucb_regret(T: int, K: int) -> float:
        """
        KL-UCB的遗憾界

        O(K * log(T))
        """
        return K * math.log(T)

    @staticmethod
    def thompson_regret(T: int, K: int, gap: float) -> float:
        """
        Thompson Sampling的遗憾界

        O((K * log(T)) / gap)
        """
        return (K * math.log(T)) / gap


class WorstCaseRegret:
    """
    最坏情况遗憾分析

    针对对抗老虎机
    """

    @staticmethod
    def exp3_regret(T: int, K: int) -> float:
        """
        EXP3的遗憾界

        O(sqrt(K * T * log(K)))
        """
        return np.sqrt(2 * K * T * math.log(K))

    @staticmethod
    def exp3_ix_regret(T: int, K: int) -> float:
        """
        EXP3-IX的遗憾界

        O(sqrt(K * T * log(K)))
        """
        return np.sqrt(2 * K * T * math.log(K))

    @staticmethod
    def minimax_regret(T: int, K: int) -> float:
        """
        最小最大遗憾下界

        Omega(sqrt(K * T))
        """
        return np.sqrt(K * T)


class InstanceDependentRegret:
    """
    实例相关遗憾分析

    基于最优动作与次优动作的gap
    """

    def __init__(self, true_probs: np.ndarray):
        self.true_probs = true_probs
        self.optimal_prob = max(true_probs)
        self.optimal_arm = np.argmax(true_probs)

        # 计算gap
        sorted_probs = np.sort(true_probs)[::-1]
        self.delta = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else 0

    def upper_bound(self, T: int) -> float:
        """
        上界

        O((K * log(T)) / delta)
        """
        if self.delta == 0:
            return float('inf')
        return len(self.true_probs) * math.log(T) / self.delta

    def lower_bound(self, T: int) -> float:
        """
        下界

        Omega((1/delta) * log(T))
        """
        if self.delta == 0:
            return 0
        return (1 / self.delta) * math.log(T)


def compute_theoretical_regret_bounds(T: int, K: int, gap: float = 0.1):
    """
    计算理论遗憾界
    """
    bounds = {
        'UCB': SubGaussianRegret.ucb_regret(T, K),
        'KL-UCB': SubGaussianRegret.kl_ucb_regret(T, K),
        'Thompson': SubGaussianRegret.thompson_regret(T, K, gap),
        'EXP3': WorstCaseRegret.exp3_regret(T, K),
        'Minimax': WorstCaseRegret.minimax_regret(T, K)
    }

    return bounds


def plot_regret_comparison(results: dict, save_path: Optional[str] = None):
    """
    可视化遗憾对比

    参数:
        results: {algorithm_name: list_of_cumulative_regrets}
        save_path: 保存路径
    """
    # 简化实现（不依赖matplotlib）
    print("遗憾度对比:")
    for name, regrets in results.items():
        if regrets:
            print(f"  {name}: 最终遗憾={regrets[-1]:.2f}")


class AsymptoticRegretAnalyzer:
    """
    渐近遗憾分析

    分析当T -> infinity时的遗憾行为
    """

    def __init__(self, true_probs: np.ndarray):
        self.true_probs = true_probs
        self.K = len(true_probs)
        self.optimal_arm = np.argmax(true_probs)
        self.optimal_prob = max(true_probs)

        # 计算gap
        sorted_probs = np.sort(true_probs)[::-1]
        self.gaps = sorted_probs[0] - sorted_probs[1:]

    def ucb_asymptotic_rate(self) -> float:
        """
        UCB渐近遗憾率

        lim_{T->inf} R(T) / log(T) = sum_{a != *} (2 * delta_a / delta_min)
        """
        if not self.gaps.any():
            return 0

        delta_min = min(self.gaps)
        rate = 0

        for delta_a in self.gaps:
            rate += 2 * delta_a / (delta_a ** 2)

        return rate * delta_min

    def thompson_asymptotic_rate(self) -> float:
        """
        Thompson Sampling渐近遗憾率

        比UCB有更小的常数因子
        """
        return 0.5 * self.ucb_asymptotic_rate()

    def compute_efficiency_ratio(self) -> float:
        """
        计算算法效率比

        实际遗憾 / 理论下界
        """
        return 1.0  # 占位


def run_regret_analysis():
    """运行遗憾分析"""
    np.random.seed(42)

    print("=" * 50)
    print("遗憾度分析")
    print("=" * 50)

    # 测试问题
    true_probs = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
    T = 1000
    K = len(true_probs)

    print(f"臂概率: {true_probs}")
    print(f"最优臂: {np.argmax(true_probs)}, 概率: {max(true_probs)}")

    # 理论界
    print("\n--- 理论遗憾界 ---")
    bounds = compute_theoretical_regret_bounds(T, K, gap=0.1)
    for name, bound in bounds.items():
        print(f"{name}: {bound:.2f}")

    # 实例相关分析
    print("\n--- 实例相关分析 ---")
    analyzer = InstanceDependentRegret(true_probs)
    print(f"Gap (最优-次优): {analyzer.delta:.2f}")
    print(f"实例相关上界: {analyzer.upper_bound(T):.2f}")
    print(f"实例相关下界: {analyzer.lower_bound(T):.2f}")

    # 渐近分析
    print("\n--- 渐近分析 ---")
    asymptotic = AsymptoticRegretAnalyzer(true_probs)
    print(f"UCB渐近率: {asymptotic.ucb_asymptotic_rate():.4f}")
    print(f"Thompson渐近率: {asymptotic.thompson_asymptotic_rate():.4f}")

    # 实际运行比较
    print("\n--- 实际运行比较 ---")
    from ucb_algorithms import UCB1
    from thompson_sampling import BernoulliThompsonSampling

    agents = {
        'UCB1': UCB1(K, c=2.0),
        'Thompson': BernoulliThompsonSampling(K)
    }

    regret_trackers = {name: RegretCalculator(K, true_probs) for name in agents}

    for step in range(T):
        for name, agent in agents.items():
            arm = agent.select_arm()
            reward = 1.0 if np.random.rand() < true_probs[arm] else 0.0
            agent.update(arm, reward)
            regret_trackers[name].add_result(arm, reward)

    for name, tracker in regret_trackers.items():
        regret = tracker.get_total_regret()
        print(f"{name}: 总遗憾={regret:.2f}, 最优选择率={tracker.get_optimality_gap():.2%}")

    return regret_trackers


if __name__ == "__main__":
    run_regret_analysis()
    print("\n测试完成！")
