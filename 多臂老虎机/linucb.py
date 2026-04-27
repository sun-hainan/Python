# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / linucb

本文件实现 linucb 相关的算法功能。
"""

import numpy as np
import torch
from typing import List, Dict, Optional, Tuple


class LinUCB:
    """
    LinUCB (Linear Upper Confidence Bound)

    线性上下文老虎机算法
    """

    def __init__(self, num_arms: int, feature_dim: int, alpha: float = 1.0, device: str = 'cpu'):
        """
        参数:
            num_arms: 臂数量
            feature_dim: 特征维度
            alpha: 探索参数
            device: 计算设备
        """
        self.num_arms = num_arms
        self.feature_dim = feature_dim
        self.alpha = alpha
        self.device = device

        # 每个臂的模型参数
        # A[a] = feature^T * feature + lambda * I
        self.A = [torch.eye(feature_dim, device=device) for _ in range(num_arms)]
        # b[a] = feature^T * reward
        self.b = [torch.zeros(feature_dim, device=device) for _ in range(num_arms)]

        # 正则化参数
        self.lambda_reg = 0.1

    def _compute_theta(self, arm: int) -> torch.Tensor:
        """
        计算臂的线性模型参数

        theta = A^{-1} * b
        """
        A_inv = torch.inverse(self.A[arm])
        theta = A_inv @ self.b[arm]
        return theta

    def _compute_ucb(self, arm: int, feature: torch.Tensor) -> float:
        """
        计算臂的UCB值

        UCB = theta^T * x + alpha * sqrt(x^T * A^{-1} * x)
        """
        theta = self._compute_theta(arm)

        # 预测均值
        pred_mean = (theta @ feature).item()

        # 计算探索项
        A_inv = torch.inverse(self.A[arm])
        explore = torch.sqrt(feature @ A_inv @ feature).item()

        return pred_mean + self.alpha * explore

    def select_arm(self, features: torch.Tensor) -> int:
        """
        选择臂

        参数:
            features: [num_arms, feature_dim] 每个臂的上下文特征

        返回:
            arm: 选择的臂索引
        """
        if features.dim() == 1:
            features = features.unsqueeze(0)

        ucb_values = []
        for arm in range(self.num_arms):
            ucb = self._compute_ucb(arm, features[arm])
            ucb_values.append(ucb)

        return int(np.argmax(ucb_values))

    def update(self, arm: int, feature: torch.Tensor, reward: float):
        """
        更新模型

        参数:
            arm: 被选择的臂
            feature: 对应的特征
            reward: 获得的奖励
        """
        if feature.dim() > 1:
            feature = feature.squeeze()

        # 更新A和b
        self.A[arm] += torch.outer(feature, feature)
        self.b[arm] += reward * feature

    def get_theta(self, arm: int) -> np.ndarray:
        """获取臂的参数"""
        return self._compute_theta(arm).cpu().numpy()


class DisjointLinUCB(LinUCB):
    """
    非共享LinUCB

    每个臂有独立的模型参数
    """

    def __init__(self, num_arms: int, feature_dim: int, alpha: float = 1.0, device: str = 'cpu'):
        super().__init__(num_arms, feature_dim, alpha, device)


class HybridLinUCB:
    """
    混合LinUCB

    同时包含共享特征和每个臂的特有特征
    """

    def __init__(self, num_arms: int, shared_dim: int, arm_dim: int, alpha: float = 1.0, device: str = 'cpu'):
        """
        参数:
            shared_dim: 共享特征维度
            arm_dim: 每臂特有特征维度
        """
        self.num_arms = num_arms
        self.shared_dim = shared_dim
        self.arm_dim = arm_dim
        self.total_dim = shared_dim + arm_dim
        self.alpha = alpha
        self.device = device

        # 共享参数
        self.A_shared = torch.eye(shared_dim, device=device) * self.lambda_reg
        self.b_shared = torch.zeros(shared_dim, device=device)

        # 每臂参数
        self.A_arms = [torch.eye(arm_dim, device=device) * self.lambda_reg for _ in range(num_arms)]
        self.b_arms = [torch.zeros(arm_dim, device=device) for _ in range(num_arms)]

        self.lambda_reg = 0.1

    def _build_features(self, shared_features: torch.Tensor, arm: int,
                        arm_features: torch.Tensor) -> torch.Tensor:
        """构建完整特征向量"""
        if shared_features.dim() == 1:
            shared_features = shared_features.unsqueeze(0)
        if arm_features.dim() == 1:
            arm_features = arm_features.unsqueeze(0)

        # 拼接
        return torch.cat([shared_features, arm_features], dim=-1)

    def select_arm(self, shared_features: torch.Tensor, arm_features: List[torch.Tensor]) -> int:
        """选择臂"""
        ucb_values = []

        for arm in range(self.num_arms):
            combined = self._build_features(shared_features, arm, arm_features[arm])

            # 简化的UCB计算
            pred_mean = combined.mean().item()
            explore = self.alpha * torch.norm(combined).item() / 10

            ucb_values.append(pred_mean + explore)

        return int(np.argmax(ucb_values))


class ContextualBandit:
    """
    通用上下文老虎机框架
    """

    def __init__(self, num_arms: int, feature_dim: int, algorithm: str = 'linucb', device: str = 'cpu'):
        """
        参数:
            algorithm: 'linucb', 'epsgreedy', 'thompson'
        """
        self.num_arms = num_arms
        self.feature_dim = feature_dim
        self.algorithm = algorithm
        self.device = device

        if algorithm == 'linucb':
            self.agent = LinUCB(num_arms, feature_dim, device=device)
        elif algorithm == 'epsgreedy':
            self.agent = EpsilonGreedyContextual(num_arms, feature_dim, device=device)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def select_arm(self, features: torch.Tensor) -> int:
        """选择臂"""
        return self.agent.select_arm(features)

    def update(self, arm: int, feature: torch.Tensor, reward: float):
        """更新"""
        self.agent.update(arm, feature, reward)


class EpsilonGreedyContextual:
    """
    上下文感知的Epsilon-Greedy
    """

    def __init__(self, num_arms: int, feature_dim: int, epsilon: float = 0.1, device: str = 'cpu'):
        self.num_arms = num_arms
        self.feature_dim = feature_dim
        self.epsilon = epsilon
        self.device = device

        # 简单的线性模型
        self.weights = torch.zeros(num_arms, feature_dim, device=device)

    def select_arm(self, features: torch.Tensor) -> int:
        """选择臂"""
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.num_arms)

        # 预测所有臂的奖励
        predictions = torch.zeros(self.num_arms)
        for arm in range(self.num_arms):
            predictions[arm] = (self.weights[arm] * features[arm]).sum()

        return torch.argmax(predictions).item()

    def update(self, arm: int, feature: torch.Tensor, reward: float):
        """更新"""
        # 简单梯度下降
        pred = (self.weights[arm] * feature).sum()
        error = reward - pred
        self.weights[arm] += 0.1 * error * feature


class LinThompsonSampling:
    """
    线性Thompson Sampling

    上下文老虎机的贝叶斯方法
    """

    def __init__(self, num_arms: int, feature_dim: int, alpha: float = 1.0, device: str = 'cpu'):
        self.num_arms = num_arms
        self.feature_dim = feature_dim
        self.alpha = alpha
        self.device = device

        # 先验参数
        self.mean = [torch.zeros(feature_dim, device=device) for _ in range(num_arms)]
        self.cov = [torch.eye(feature_dim, device=device) * alpha for _ in range(num_arms)]

    def select_arm(self, features: torch.Tensor) -> int:
        """从后验采样并选择"""
        if features.dim() == 1:
            features = features.unsqueeze(0)

        samples = torch.zeros(self.num_arms, device=self.device)

        for arm in range(self.num_arms):
            # 从多元正态分布采样
            sample = torch.distributions.MultivariateNormal(self.mean[arm], self.cov[arm]).sample()
            samples[arm] = (sample * features[arm]).sum()

        return torch.argmax(samples).item()

    def update(self, arm: int, feature: torch.Tensor, reward: float):
        """更新后验"""
        if feature.dim() > 1:
            feature = feature.squeeze()

        # 简化的后验更新
        cov_inv = torch.inverse(self.cov[arm])
        new_cov_inv = cov_inv + torch.outer(feature, feature)
        new_cov = torch.inverse(new_cov_inv)

        new_mean = new_cov @ (cov_inv @ self.mean[arm] + feature * reward)

        self.cov[arm] = new_cov
        self.mean[arm] = new_mean


def run_contextual_bandit_simulation(num_arms: int = 5, feature_dim: int = 10,
                                     num_steps: int = 1000, seed: int = 42):
    """
    运行上下文老虎机模拟
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    print(f"臂数: {num_arms}, 特征维度: {feature_dim}")

    # 真实参数
    true_weights = np.random.randn(num_arms, feature_dim) * 0.5

    # 创建算法
    linucb = LinUCB(num_arms, feature_dim, alpha=1.0)
    lin_thompson = LinThompsonSampling(num_arms, feature_dim, alpha=1.0)

    linucb_rewards = []
    lin_thompson_rewards = []

    for step in range(num_steps):
        # 生成上下文特征
        features = torch.randn(num_arms, feature_dim)

        # 生成真实奖励
        true_rewards = (true_weights * features.numpy()).sum(axis=1) + np.random.randn(num_arms) * 0.1

        # LinUCB
        arm = linucb.select_arm(features)
        reward = true_rewards[arm]
        linucb.update(arm, features[arm], reward)
        linucb_rewards.append(reward)

        # Lin Thompson Sampling
        arm_t = lin_thompson.select_arm(features)
        reward_t = true_rewards[arm_t]
        lin_thompson.update(arm_t, features[arm_t], reward_t)
        lin_thompson_rewards.append(reward_t)

    print(f"\n--- 结果 ---")
    print(f"LinUCB总奖励: {sum(linucb_rewards):.2f}")
    print(f"LinThompson总奖励: {sum(lin_thompson_rewards):.2f}")

    return {
        'linucb': sum(linucb_rewards),
        'lin_thompson': sum(lin_thompson_rewards)
    }


if __name__ == "__main__":
    print("=" * 50)
    print("LinUCB算法测试")
    print("=" * 50)

    # 测试LinUCB
    print("\n--- LinUCB ---")
    num_arms = 3
    feature_dim = 5

    linucb = LinUCB(num_arms, feature_dim, alpha=1.0)

    # 模拟数据
    for step in range(100):
        features = torch.randn(num_arms, feature_dim)
        arm = linucb.select_arm(features)

        # 模拟奖励
        reward = float(np.random.randn() * 0.1 + (step % 3) * 0.2)
        linucb.update(arm, features[arm], reward)

    print(f"估计参数:")
    for arm in range(num_arms):
        print(f"  臂{arm}: {linucb.get_theta(arm)}")

    # 上下文老虎机模拟
    print("\n--- 上下文老虎机模拟 ---")
    run_contextual_bandit_simulation(num_arms=4, feature_dim=8, num_steps=500)

    print("\n测试完成！")
