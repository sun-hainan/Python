# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / exp3_algorithm

本文件实现 exp3_algorithm 相关的算法功能。
"""

import numpy as np
import torch
import math
from typing import List, Optional


class EXP3:
    """
    EXP3 (Exponential-weight algorithm for Exploration and Exploitation)

    基础EXP3算法
    """

    def __init__(self, num_arms: int, gamma: float = 0.0, device: str = 'cpu'):
        """
        参数:
            num_arms: 臂数量
            gamma: 探索参数 (0 <= gamma <= 1)
            device: 计算设备
        """
        self.num_arms = num_arms
        self.gamma = gamma
        self.device = device

        # 权重
        self.weights = torch.ones(num_arms, device=device)

        # 选择概率
        self.probs = torch.ones(num_arms, device=device) / num_arms

        self.total_reward = 0.0
        self.time_step = 0

    def select_arm(self) -> int:
        """
        选择臂

        混合均匀分布：
        P(a) = (1-gamma) * w(a) / sum(w) + gamma / K
        """
        # 计算概率
        weight_sum = self.weights.sum()
        self.probs = (1 - self.gamma) * self.weights / weight_sum + self.gamma / self.num_arms

        # 采样
        return torch.multinomial(self.probs, 1).item()

    def update(self, arm: int, reward: float):
        """
        更新权重

        参数:
            arm: 被选择的臂
            reward: 获得的奖励
        """
        self.time_step += 1

        # 估计奖励（抵消探索导致的偏差）
        estimated_reward = reward / (self.probs[arm] + 1e-10)

        # 更新权重
        self.weights[arm] *= torch.exp(self.gamma * estimated_reward / self.num_arms)

        self.total_reward += reward

    def get_probabilities(self) -> np.ndarray:
        """获取当前概率分布"""
        return self.probs.cpu().numpy()


class EXP3S:
    """
    EXP3-S (EXP3 with Stochastic rewards)

    适用于随机奖励环境的EXP3变体
    """

    def __init__(self, num_arms: int, eta: float = 0.5, device: str = 'cpu'):
        """
        参数:
            eta: 学习率
        """
        self.num_arms = num_arms
        self.eta = eta
        self.device = device

        self.weights = torch.ones(num_arms, device=device)
        self.total_counts = torch.zeros(num_arms, device=device)
        self.time_step = 0

    def select_arm(self) -> int:
        """选择臂"""
        weight_sum = self.weights.sum()
        probs = self.weights / weight_sum

        return torch.multinomial(probs, 1).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.time_step += 1
        self.total_counts[arm] += 1

        # 计算概率
        weight_sum = self.weights.sum()
        probs = self.weights / weight_sum

        # 估计奖励
        estimated_reward = reward / probs[arm]

        # 更新权重
        self.weights[arm] *= torch.exp(self.eta * estimated_reward / self.num_arms)

        # 归一化
        self.weights = self.weights / self.weights.sum()


class EXP3IX:
    """
    EXP3-IX (EXP3 with Implicit Exploration)

    改进的EXP3，使用隐式探索
    """

    def __init__(self, num_arms: int, gamma: float = 0.1, device: str = 'cpu'):
        self.num_arms = num_arms
        self.gamma = gamma
        self.device = device

        self.weights = torch.ones(num_arms, device=device)
        self.time_step = 0

    def select_arm(self) -> int:
        """选择臂"""
        weight_sum = self.weights.sum()
        probs = (1 - self.gamma) * self.weights / weight_sum + self.gamma / self.num_arms

        return torch.multinomial(probs, 1).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.time_step += 1

        # 计算概率
        weight_sum = self.weights.sum()
        probs = (1 - self.gamma) * self.weights / weight_sum + self.gamma / self.num_arms

        # IX更新规则
        if reward >= 0:
            estimated = reward / probs[arm]
        else:
            # 负奖励处理
            estimated = (reward + self.gamma) / (probs[arm] + self.gamma)

        self.weights[arm] *= torch.exp(estimated * self.gamma / self.num_arms)


class EXP3P:
    """
    EXP3-P (EXP3 with Predictions)

    带预测的EXP3变体
    """

    def __init__(self, num_arms: int, delta: float = 0.1, device: str = 'cpu'):
        """
        参数:
            delta: 失败概率
        """
        self.num_arms = num_arms
        self.delta = delta
        self.device = device

        self.weights = torch.ones(num_arms, device=device)
        self.time_step = 0

    def _compute_gamma(self) -> float:
        """计算gamma"""
        T = self.time_step + 1
        K = self.num_arms

        return min(1, math.sqrt(K * math.log(K / self.delta) / (T * math.e)))

    def select_arm(self) -> int:
        """选择臂"""
        gamma = self._compute_gamma()
        weight_sum = self.weights.sum()
        probs = (1 - gamma) * self.weights / weight_sum + gamma / self.num_arms

        return torch.multinomial(probs, 1).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.time_step += 1
        gamma = self._compute_gamma()

        weight_sum = self.weights.sum()
        probs = (1 - gamma) * self.weights / weight_sum + gamma / self.num_arms

        # 估计奖励
        estimated = reward / probs[arm]

        # 更新
        self.weights[arm] *= torch.exp(gamma * estimated / self.num_arms)


class AdversarialBanditSimulator:
    """
    对抗老虎机模拟器

    生成对抗性的奖励序列
    """

    def __init__(self, num_arms: int, reward_type: str = 'worst_case'):
        """
        参数:
            reward_type: 'worst_case', 'alternating', 'random'
        """
        self.num_arms = num_arms
        self.reward_type = reward_type
        self.time_step = 0

    def generate_rewards(self) -> np.ndarray:
        """
        生成奖励

        返回:
            rewards: 每个臂的奖励
        """
        if self.reward_type == 'worst_case':
            # 对手总是让最差臂的奖励高
            return np.zeros(self.num_arms)

        elif self.reward_type == 'alternating':
            # 交替奖励
            if self.time_step % 2 == 0:
                return np.array([1.0 if i == 0 else 0.0 for i in range(self.num_arms)])
            else:
                return np.array([0.0 if i == 0 else 1.0 for i in range(self.num_arms)])

        else:  # random
            return np.random.rand(self.num_arms)


def run_adversarial_comparison(num_arms: int = 5, num_steps: int = 1000,
                               reward_type: str = 'alternating', seed: int = 42):
    """
    对抗环境下的算法比较
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    print(f"对抗环境: {reward_type}")

    # 创建对抗老虎机
    bandit = AdversarialBanditSimulator(num_arms, reward_type)

    # 算法
    exp3 = EXP3(num_arms, gamma=0.1)
    exp3_ix = EXP3IX(num_arms, gamma=0.1)

    # 收集奖励
    exp3_rewards = []
    exp3_ix_rewards = []

    for step in range(num_steps):
        # 生成对抗奖励
        true_rewards = bandit.generate_rewards()
        bandit.time_step = step

        # EXP3
        arm = exp3.select_arm()
        reward = true_rewards[arm]
        exp3.update(arm, reward)
        exp3_rewards.append(reward)

        # EXP3-IX
        arm_ix = exp3_ix.select_arm()
        reward_ix = true_rewards[arm_ix]
        exp3_ix.update(arm_ix, reward_ix)
        exp3_ix_rewards.append(reward_ix)

    # 计算遗憾
    optimal_reward = num_steps * 1.0  # 假设最优臂总是给1

    exp3_regret = optimal_reward - sum(exp3_rewards)
    exp3_ix_regret = optimal_reward - sum(exp3_ix_rewards)

    print(f"\n--- 结果 ---")
    print(f"EXP3: 总奖励={sum(exp3_rewards)}, 遗憾={exp3_regret}")
    print(f"EXP3-IX: 总奖励={sum(exp3_ix_rewards)}, 遗憾={exp3_ix_regret}")

    return {
        'exp3_total': sum(exp3_rewards),
        'exp3_ix_total': sum(exp3_ix_rewards),
        'exp3_regret': exp3_regret,
        'exp3_ix_regret': exp3_ix_regret
    }


if __name__ == "__main__":
    print("=" * 50)
    print("EXP3算法测试（对抗老虎机）")
    print("=" * 50)

    # 基础EXP3测试
    print("\n--- EXP3基础测试 ---")
    num_arms = 5
    exp3 = EXP3(num_arms, gamma=0.1)

    print(f"初始概率: {exp3.get_probabilities()}")

    for step in range(100):
        arm = exp3.select_arm()
        # 模拟奖励
        reward = 1.0 if np.random.rand() < 0.3 + 0.1 * arm else 0.0
        exp3.update(arm, reward)

    print(f"100步后概率: {exp3.get_probabilities()}")
    print(f"总奖励: {exp3.total_reward}")

    # 对抗环境测试
    print("\n--- 对抗环境测试 ---")
    run_adversarial_comparison(num_arms=5, num_steps=500, reward_type='alternating')

    print("\n测试完成！")
