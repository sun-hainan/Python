# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / contextual_bandits

本文件实现 contextual_bandits 相关的算法功能。
"""

import numpy as np
import torch
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Context:
    """上下文数据"""
    features: torch.Tensor  # 上下文特征
    metadata: Optional[Dict] = None  # 额外元数据


@dataclass
class Action:
    """动作"""
    arm: int
    features: torch.Tensor  # 该动作对应的特征
    reward: Optional[float] = None


class ContextualBanditBase:
    """
    上下文老虎机基类
    """

    def __init__(self, num_arms: int, feature_dim: int, device: str = 'cpu'):
        self.num_arms = num_arms
        self.feature_dim = feature_dim
        self.device = device

        self.total_reward = 0.0
        self.time_step = 0

    def select_arm(self, context: Context) -> int:
        """
        根据上下文选择臂

        参数:
            context: 当前上下文

        返回:
            arm: 选择的臂索引
        """
        raise NotImplementedError

    def update(self, arm: int, context: Context, reward: float):
        """
        更新算法状态

        参数:
            arm: 被选择的臂
            context: 对应的上下文
            reward: 获得的奖励
        """
        raise NotImplementedError


class EpsilonGreedyContextual(ContextualBanditBase):
    """
    Epsilon-Greedy上下文老虎机

    每个臂维护一个线性模型
    """

    def __init__(self, num_arms: int, feature_dim: int, epsilon: float = 0.1, device: str = 'cpu'):
        super().__init__(num_arms, feature_dim, device)
        self.epsilon = epsilon

        # 每个臂的权重
        self.weights = torch.zeros(num_arms, feature_dim, device=device)

    def select_arm(self, context: Context) -> int:
        """基于ε-greedy选择"""
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.num_arms)

        # 预测所有臂的值
        predictions = torch.zeros(self.num_arms, device=self.device)

        for arm in range(self.num_arms):
            if context.features.dim() == 1:
                predictions[arm] = (self.weights[arm] * context.features).sum()
            else:
                predictions[arm] = (self.weights[arm] * context.features[arm]).sum()

        return torch.argmax(predictions).item()

    def update(self, arm: int, context: Context, reward: float):
        """更新权重"""
        self.time_step += 1

        # 获取特征
        if context.features.dim() == 1:
            features = context.features
        else:
            features = context.features[arm]

        # 梯度更新
        pred = (self.weights[arm] * features).sum()
        error = reward - pred
        lr = 0.1 / (1 + self.time_step * 0.001)
        self.weights[arm] += lr * error * features


class LinUCBContextual(ContextualBanditBase):
    """
    LinUCB上下文老虎机

    使用上置信界进行探索
    """

    def __init__(self, num_arms: int, feature_dim: int, alpha: float = 1.0, device: str = 'cpu'):
        super().__init__(num_arms, feature_dim, device)
        self.alpha = alpha

        # 每个臂的模型
        self.A = [torch.eye(feature_dim, device=device) for _ in range(num_arms)]
        self.b = [torch.zeros(feature_dim, device=device) for _ in range(num_arms)]
        self.lambda_reg = 0.1

    def _compute_ucb(self, arm: int, features: torch.Tensor) -> float:
        """计算UCB"""
        A_inv = torch.inverse(self.A[arm])
        theta = A_inv @ self.b[arm]

        # 均值
        mean = (theta * features).sum()

        # 探索项
        explore = self.alpha * torch.sqrt(features @ A_inv @ features)

        return (mean + explore).item()

    def select_arm(self, context: Context) -> int:
        """选择臂"""
        if context.features.dim() == 1:
            features_list = [context.features] * self.num_arms
        else:
            features_list = context.features

        ucb_values = []
        for arm in range(self.num_arms):
            ucb = self._compute_ucb(arm, features_list[arm])
            ucb_values.append(ucb)

        return int(np.argmax(ucb_values))

    def update(self, arm: int, context: Context, reward: float):
        """更新模型"""
        self.time_step += 1

        if context.features.dim() == 1:
            features = context.features
        else:
            features = context.features[arm]

        # 更新
        self.A[arm] += torch.outer(features, features)
        self.b[arm] += reward * features


class ThompsonSamplingContextual(ContextualBanditBase):
    """
    Thompson Sampling上下文老虎机

    使用贝叶斯后验进行采样
    """

    def __init__(self, num_arms: int, feature_dim: int, prior_variance: float = 1.0, device: str = 'cpu'):
        super().__init__(num_arms, feature_dim, device)
        self.prior_variance = prior_variance

        # 后验均值和方差
        self.mean = [torch.zeros(feature_dim, device=device) for _ in range(num_arms)]
        self.cov = [torch.eye(feature_dim, device=device) * prior_variance for _ in range(num_arms)]

    def select_arm(self, context: Context) -> int:
        """从后验采样并选择"""
        if context.features.dim() == 1:
            features_list = [context.features] * self.num_arms
        else:
            features_list = context.features

        samples = torch.zeros(self.num_arms, device=self.device)

        for arm in range(self.num_arms):
            # 从多元正态采样
            sample = torch.distributions.MultivariateNormal(self.mean[arm], self.cov[arm]).sample()
            samples[arm] = (sample * features_list[arm]).sum()

        return torch.argmax(samples).item()

    def update(self, arm: int, context: Context, reward: float):
        """更新后验"""
        self.time_step += 1

        if context.features.dim() == 1:
            features = context.features
        else:
            features = context.features[arm]

        # 后验更新（贝叶斯线性回归）
        cov_inv = torch.inverse(self.cov[arm])
        new_cov_inv = cov_inv + torch.outer(features, features)
        new_cov = torch.inverse(new_cov_inv)

        new_mean = new_cov @ (cov_inv @ self.mean[arm] + features * reward)

        self.cov[arm] = new_cov
        self.mean[arm] = new_mean


class GradientBanditContextual(ContextualBanditBase):
    """
    梯度上升上下文老虎机

    使用梯度上升更新动作偏好
    """

    def __init__(self, num_arms: int, feature_dim: int, alpha: float = 0.1, device: str = 'cpu'):
        super().__init__(num_arms, feature_dim, device)
        self.alpha = alpha

        # 偏好权重
        self.theta = torch.zeros(num_arms, feature_dim, device=device)

        # 基线
        self.baseline = 0.0

    def _compute_preferences(self, features: torch.Tensor) -> torch.Tensor:
        """计算每个臂的偏好"""
        preferences = torch.zeros(self.num_arms, device=self.device)
        for arm in range(self.num_arms):
            if features.dim() == 1:
                preferences[arm] = (self.theta[arm] * features).sum()
            else:
                preferences[arm] = (self.theta[arm] * features[arm]).sum()
        return preferences

    def select_arm(self, context: Context) -> int:
        """使用softmax选择"""
        if context.features.dim() == 1:
            features_list = [context.features] * self.num_arms
        else:
            features_list = context.features

        prefs = self._compute_preferences(context.features)

        # softmax概率
        exp_prefs = torch.exp(prefs - prefs.max())
        probs = exp_prefs / exp_prefs.sum()

        return torch.multinomial(probs, 1).item()

    def update(self, arm: int, context: Context, reward: float):
        """更新偏好"""
        self.time_step += 1

        if context.features.dim() == 1:
            features = context.features
        else:
            features = context.features[arm]

        prefs = self._compute_preferences(context.features)
        exp_prefs = torch.exp(prefs - prefs.max())
        probs = exp_prefs / exp_prefs.sum()

        # 更新基线
        self.baseline = 0.99 * self.baseline + 0.01 * reward

        # 偏好更新
        for a in range(self.num_arms):
            if a == arm:
                self.theta[a] += self.alpha * (reward - self.baseline) * features
            else:
                self.theta[a] -= self.alpha * (reward - self.baseline) * probs[a] * features


def run_contextual_bandit_comparison(num_arms: int = 5, feature_dim: int = 10,
                                     num_steps: int = 1000, seed: int = 42):
    """
    比较不同的上下文老虎机算法
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    # 生成真实权重
    true_weights = np.random.randn(num_arms, feature_dim) * 0.5

    # 创建算法
    algorithms = {
        'epsilon-greedy': EpsilonGreedyContextual(num_arms, feature_dim, epsilon=0.1),
        'linucb': LinUCBContextual(num_arms, feature_dim, alpha=1.0),
        'thompson': ThompsonSamplingContextual(num_arms, feature_dim, prior_variance=1.0),
        'gradient': GradientBanditContextual(num_arms, feature_dim, alpha=0.1)
    }

    results = {name: {'rewards': [], 'total': 0} for name in algorithms}

    for step in range(num_steps):
        # 生成上下文
        features = torch.randn(num_arms, feature_dim)

        # 生成真实奖励
        true_rewards = (true_weights * features.numpy()).sum(axis=1) + np.random.randn(num_arms) * 0.1

        for name, algo in algorithms.items():
            # 选择臂
            context = Context(features=features)
            arm = algo.select_arm(context)

            # 获取奖励
            reward = true_rewards[arm]

            # 更新
            algo.update(arm, context, reward)

            results[name]['rewards'].append(reward)
            results[name]['total'] += reward

    # 打印结果
    print(f"臂数: {num_arms}, 特征维度: {feature_dim}, 步数: {num_steps}")
    print("\n--- 结果 ---")
    for name, result in results.items():
        avg_reward = result['total'] / num_steps
        print(f"{name}: 总奖励={result['total']:.2f}, 平均={avg_reward:.4f}")

    return results


if __name__ == "__main__":
    print("=" * 50)
    print("上下文老虎机测试")
    print("=" * 50)

    # 运行比较
    run_contextual_bandit_comparison(num_arms=4, feature_dim=8, num_steps=500)

    print("\n测试完成！")
