# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / varying_confidence

本文件实现 varying_confidence 相关的算法功能。
"""

import numpy as np
import torch
import math
from typing import List, Tuple, Optional


class KLLUCB:
    """
    KL-LUCB算法

    使用KL散度计算置信区间，适用于指数族分布
    """

    def __init__(self, num_arms: int, horizon: int, delta: float = 0.1, device: str = 'cpu'):
        """
        参数:
            horizon: 时间范围
            delta: 失败概率
        """
        self.num_arms = num_arms
        self.horizon = horizon
        self.delta = delta
        self.device = device

        # 统计
        self.sum_rewards = torch.zeros(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

    def _kl_divergence(self, p: float, q: float) -> float:
        """伯努利分布的KL散度"""
        if p == 0:
            return (1 - p) * math.log((1 - p) / (1 - q + 1e-10))
        elif p == 1:
            return p * math.log(p / (q + 1e-10))
        else:
            return p * math.log(p / (q + 1e-10)) + (1 - p) * math.log((1 - p) / (1 - q + 1e-10))

    def _find_ucb(self, arm: int, target: float) -> float:
        """
        找到满足KL(p_hat, q) = target的最大q

        参数:
            arm: 臂索引
            target: 目标KL值

        返回:
            上界
        """
        p_hat = self.sum_rewards[arm] / self.counts[arm] if self.counts[arm] > 0 else 0.5

        # 二分搜索
        low, high = p_hat, 1.0

        for _ in range(50):
            mid = (low + high) / 2
            kl = self._kl_divergence(p_hat, mid)

            if kl < target:
                low = mid
            else:
                high = mid

        return (low + high) / 2

    def _find_lcb(self, arm: int, target: float) -> float:
        """找到满足KL(p_hat, q) = target的最小q"""
        p_hat = self.sum_rewards[arm] / self.counts[arm] if self.counts[arm] > 0 else 0.5

        low, high = 0.0, p_hat

        for _ in range(50):
            mid = (low + high) / 2
            kl = self._kl_divergence(p_hat, mid)

            if kl < target:
                high = mid
            else:
                low = mid

        return (low + high) / 2

    def select_arms(self) -> Tuple[int, int]:
        """
        选择两个臂进行比较

        返回:
            (top_arm, challenger): 最佳候选和挑战者
        """
        # 计算每个臂的均值
        means = torch.zeros(self.num_arms, device=self.device)
        for arm in range(self.num_arms):
            if self.counts[arm] > 0:
                means[arm] = self.sum_rewards[arm] / self.counts[arm]

        # 找到均值最高的臂
        top_arm = torch.argmax(means).item()

        # 计算探索预算
        total_counts = self.counts.sum().item()
        if total_counts == 0:
            total_counts = 1

        target = math.log(self.horizon / self.delta) / total_counts

        # 找挑战者（KL上界与top的KL下界差距最大）
        top_ucb = self._find_ucb(top_arm, target)

        max_gap = -float('inf')
        challenger = -1

        for arm in range(self.num_arms):
            if arm == top_arm:
                continue

            lcb = self._find_lcb(arm, target)
            gap = top_ucb - lcb

            if gap > max_gap:
                max_gap = gap
                challenger = arm

        return top_arm, challenger

    def update(self, arm: int, reward: float):
        """更新统计"""
        self.sum_rewards[arm] += reward
        self.counts[arm] += 1

    def get_best_arm(self) -> int:
        """获取最佳臂"""
        means = torch.zeros(self.num_arms, device=self.device)
        for arm in range(self.num_arms):
            if self.counts[arm] > 0:
                means[arm] = self.sum_rewards[arm] / self.counts[arm]

        return torch.argmax(means).item()


class VaryingVarianceBandit:
    """
    变方差老虎机

    臂的方差随时间变化
    """

    def __init__(self, num_arms: int, device: str = 'cpu'):
        self.num_arms = num_arms
        self.device = device

        # 使用Welford算法追踪均值和方差
        self.mean = torch.zeros(num_arms, device=device)
        self.variance = torch.ones(num_arms, device=device)
        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

    def update(self, arm: int, reward: float):
        """Welford在线方差更新"""
        self.counts[arm] += 1
        n = self.counts[arm].item()

        if n == 1:
            self.mean[arm] = reward
            self.variance[arm] = 0
        else:
            old_mean = self.mean[arm].item()
            new_mean = old_mean + (reward - old_mean) / n

            old_var = self.variance[arm].item()
            new_var = ((n - 2) * old_var + (reward - old_mean) ** 2) / (n - 1)

            self.mean[arm] = new_mean
            self.variance[arm] = new_var

    def get_confidence_bound(self, arm: int, confidence: float = 0.95) -> Tuple[float, float]:
        """
        获取置信边界

        返回:
            (lower, upper)
        """
        n = self.counts[arm].item()
        if n < 2:
            return -float('inf'), float('inf')

        # t分布临界值
        from scipy.stats import t
        t_crit = t.ppf((1 + confidence) / 2, df=n - 1)

        std = math.sqrt(self.variance[arm].item())
        se = std / math.sqrt(n)

        lower = self.mean[arm].item() - t_crit * se
        upper = self.mean[arm].item() + t_crit * se

        return lower, upper

    def select_arm(self) -> int:
        """选择臂（上界最大）"""
        upper_bounds = []

        for arm in range(self.num_arms):
            if self.counts[arm] < 2:
                upper_bounds.append(float('inf'))
            else:
                _, upper = self.get_confidence_bound(arm)
                upper_bounds.append(upper)

        return int(np.argmax(upper_bounds))


class NonStationaryBandit:
    """
    非平稳老虎机

    臂的期望奖励随时间变化
    """

    def __init__(self, num_arms: int, change_frequency: int = 100, device: str = 'cpu'):
        """
        参数:
            change_frequency: 变化频率
        """
        self.num_arms = num_arms
        self.change_frequency = change_frequency
        self.device = device

        # 当前真实概率
        self.current_probs = np.random.rand(num_arms)

        # 追踪统计（带滑动窗口）
        self.window_size = 50
        self.recent_rewards = [[] for _ in range(num_arms)]

    def change_environment(self):
        """改变环境"""
        # 随机改变某些臂的概率
        change_mask = np.random.rand(self.num_arms) < 0.3
        self.current_probs[change_mask] = np.random.rand(change_mask.sum())

    def generate_reward(self, arm: int) -> float:
        """生成奖励"""
        return 1.0 if np.random.rand() < self.current_probs[arm] else 0.0

    def update(self, arm: int, reward: float):
        """更新（滑动窗口）"""
        self.recent_rewards[arm].append(reward)

        if len(self.recent_rewards[arm]) > self.window_size:
            self.recent_rewards[arm].pop(0)

    def get_estimated_mean(self, arm: int) -> float:
        """获取滑动窗口均值"""
        if not self.recent_rewards[arm]:
            return 0.0

        return np.mean(self.recent_rewards[arm])

    def select_arm(self) -> int:
        """基于滑动窗口的UCB"""
        estimates = [self.get_estimated_mean(arm) for arm in range(self.num_arms)]

        # 添加探索项
        counts = [len(self.recent_rewards[arm]) for arm in range(self.num_arms)]

        ucb_values = []
        for arm in range(self.num_arms):
            if counts[arm] == 0:
                ucb_values.append(float('inf'))
            else:
                explore = math.sqrt(2 * math.log(sum(counts) + 1) / counts[arm])
                ucb_values.append(estimates[arm] + explore)

        return int(np.argmax(ucb_values))


class DiscountedThompsonSampling:
    """
    折扣Thompson Sampling

    对近期数据给予更高权重
    """

    def __init__(self, num_arms: int, gamma: float = 0.9, device: str = 'cpu'):
        """
        参数:
            gamma: 折扣因子
        """
        self.num_arms = num_arms
        self.gamma = gamma
        self.device = device

        # 折扣计数
        self.alpha = torch.ones(num_arms, device=device)
        self.beta = torch.ones(num_arms, device=device)

    def update(self, arm: int, reward: float):
        """折扣更新"""
        # 所有参数折扣
        self.alpha *= self.gamma
        self.beta *= self.gamma

        # 更新当前臂
        self.alpha[arm] += reward
        self.beta[arm] += (1 - reward)

    def select_arm(self) -> int:
        """采样并选择"""
        samples = torch.distributions.Beta(self.alpha, self.beta).sample()
        return torch.argmax(samples).item()


def run_varying_confidence_comparison(num_arms: int = 5, horizon: int = 1000,
                                      seed: int = 42):
    """
    变置信度算法比较
    """
    np.random.seed(seed)

    probs = np.random.rand(num_arms)

    print(f"真实概率: {probs}")

    algorithms = {
        'KLLUCB': KLLUCB(num_arms, horizon),
        'Discounted-TS': DiscountedThompsonSampling(num_arms, gamma=0.95)
    }

    results = {}

    for name, algo in algorithms.items():
        total_reward = 0

        for step in range(horizon):
            if name == 'KLLUCB':
                arm1, arm2 = algo.select_arms()
                arm = arm1  # 简化：使用第一个
            else:
                arm = algo.select_arm()

            reward = 1.0 if np.random.rand() < probs[arm] else 0.0
            algo.update(arm, reward)
            total_reward += reward

        results[name] = {
            'total_reward': total_reward,
            'best_arm': algo.get_best_arm() if hasattr(algo, 'get_best_arm') else -1
        }

        print(f"{name}: 奖励={total_reward}, 识别最佳={results[name]['best_arm']}")

    return results


if __name__ == "__main__":
    print("=" * 50)
    print("变置信度老虎机测试（KL-LUCB）")
    print("=" * 50)

    # KL-LUCB测试
    print("\n--- KL-LUCB ---")
    num_arms = 5
    probs = np.array([0.2, 0.4, 0.6, 0.8, 0.9])

    kl_lucb = KLLUCB(num_arms, horizon=500)

    for step in range(200):
        arm1, arm2 = kl_lucb.select_arms()

        # 选择其中一个
        arm = arm1
        reward = 1.0 if np.random.rand() < probs[arm] else 0.0
        kl_lucb.update(arm, reward)

    print(f"识别最佳臂: {kl_lucb.get_best_arm()}")
    print(f"真实最佳臂: {np.argmax(probs)}")

    # 折扣TS测试
    print("\n--- Discounted Thompson Sampling ---")
    discounted_ts = DiscountedThompsonSampling(num_arms, gamma=0.9)

    for step in range(500):
        arm = discounted_ts.select_arm()
        reward = 1.0 if np.random.rand() < probs[arm] else 0.0
        discounted_ts.update(arm, reward)

    print(f"Alpha: {discounted_ts.alpha}")
    print(f"Beta: {discounted_ts.beta}")

    # 比较
    print("\n--- 算法比较 ---")
    run_varying_confidence_comparison(num_arms=5, horizon=500)

    print("\n测试完成！")
