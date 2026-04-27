# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / thompson_sampling

本文件实现 thompson_sampling 相关的算法功能。
"""

import numpy as np
import torch
import torch.distributions as dist
from typing import Optional, List


class BernoulliThompsonSampling:
    """
    伯努利老虎机的Thompson Sampling

    使用Beta分布作为先验
    """

    def __init__(self, num_arms: int, prior_alpha: float = 1.0, prior_beta: float = 1.0, device: str = 'cpu'):
        """
        参数:
            num_arms: 臂数量
            prior_alpha: Beta先验alpha参数
            prior_beta: Beta先验beta参数
            device: 计算设备
        """
        self.num_arms = num_arms
        self.device = device

        # Beta分布参数 (alpha=成功次数+1, beta=失败次数+1)
        self.alpha = torch.full((num_arms,), prior_alpha, device=device)
        self.beta = torch.full((num_arms,), prior_beta, device=device)

    def select_arm(self) -> int:
        """
        从后验Beta分布采样，选择采样值最大的臂

        返回:
            arm: 选择的臂索引
        """
        # 从Beta分布采样
        samples = torch.distributions.Beta(self.alpha, self.beta).sample()
        return torch.argmax(samples).item()

    def update(self, arm: int, reward: float):
        """
        更新后验参数

        参数:
            arm: 被选择的臂
            reward: 奖励（0或1）
        """
        # 成功：alpha + 1
        # 失败：beta + 1
        self.alpha[arm] += reward
        self.beta[arm] += (1 - reward)

    def get_posterior_stats(self) -> dict:
        """
        获取后验统计

        返回:
            dict: 包含均值、标准差等信息
        """
        means = self.alpha / (self.alpha + self.beta)
        variances = (self.alpha * self.beta) / ((self.alpha + self.beta) ** 2 * (self.alpha + self.beta + 1))

        return {
            'means': means.cpu().numpy(),
            'variances': variances.cpu().numpy(),
            'alpha': self.alpha.cpu().numpy(),
            'beta': self.beta.cpu().numpy()
        }


class GaussianThompsonSampling:
    """
    高斯老虎机的Thompson Sampling

    使用正态分布作为先验
    """

    def __init__(self, num_arms: int, prior_mean: float = 0.0, prior_std: float = 1.0,
                 noise_std: float = 1.0, device: str = 'cpu'):
        """
        参数:
            prior_mean: 均值先验
            prior_std: 先验标准差
            noise_std: 奖励噪声标准差
        """
        self.num_arms = num_arms
        self.noise_std = noise_std
        self.device = device

        # 后验均值和方差
        self.posterior_mean = torch.full((num_arms,), prior_mean, device=device)
        self.posterior_var = torch.full((num_arms,), prior_std ** 2, device=device)

    def select_arm(self) -> int:
        """从后验分布采样并选择"""
        samples = torch.randn(self.num_arms, device=self.device) * torch.sqrt(self.posterior_var) + self.posterior_mean
        return torch.argmax(samples).item()

    def update(self, arm: int, reward: float):
        """更新后验"""
        # 精确后验更新（噪声已知）
        posterior_prec = 1.0 / self.posterior_var[arm]
        likelihood_prec = 1.0 / (self.noise_std ** 2)

        new_prec = posterior_prec + likelihood_prec
        new_mean = (self.posterior_mean[arm] * posterior_prec + reward * likelihood_prec) / new_prec

        self.posterior_mean[arm] = new_mean
        self.posterior_var[arm] = 1.0 / new_prec

    def get_posterior_stats(self) -> dict:
        """获取后验统计"""
        return {
            'means': self.posterior_mean.cpu().numpy(),
            'stds': torch.sqrt(self.posterior_var).cpu().numpy()
        }


class CategoricalThompsonSampling:
    """
    多类分类的Thompson Sampling

    用于上下文老虎机
    """

    def __init__(self, num_arms: int, num_classes: int, device: str = 'cpu'):
        """
        参数:
            num_arms: 动作/臂数量
            num_classes: 类别数量
        """
        self.num_arms = num_arms
        self.num_classes = num_classes
        self.device = device

        # 每个臂的狄利克雷参数
        self.alpha = torch.ones((num_arms, num_classes), device=device)

    def select_arm(self) -> int:
        """从狄利克雷分布采样，选择期望奖励最高的臂"""
        # 从狄利克雷采样
        samples = torch.distributions.Dirichlet(self.alpha[0]).sample()
        for arm in range(1, self.num_arms):
            sample = torch.distributions.Dirichlet(self.alpha[arm]).sample()
            samples = torch.cat([samples, sample])

        # 选择期望奖励最高的臂（假设类别是有序的）
        expected_rewards = samples.sum(dim=1)
        return torch.argmax(expected_rewards).item()

    def update(self, arm: int, reward: float):
        """更新狄利克雷参数"""
        # 简化：奖励为1时增加对应类别的权重
        # 实际应根据具体奖励结构更新
        pass


class RobustThompsonSampling:
    """
    鲁棒Thompson Sampling

    使用Gamma先验而非Beta先验，提高对异常奖励的鲁棒性
    """

    def __init__(self, num_arms: int, device: str = 'cpu'):
        self.num_arms = num_arms
        self.device = device

        # 使用Gamma分布参数 (shape, rate)
        self.shape = torch.ones(num_arms, device=device)
        self.rate = torch.ones(num_arms, device=device)

    def select_arm(self) -> int:
        """采样并选择"""
        samples = torch.distributions.Gamma(self.shape, 1.0 / self.rate).sample()
        return torch.argmax(samples).item()

    def update(self, arm: int, reward: float):
        """更新Gamma后验"""
        # Gamma分布的共轭更新
        self.shape[arm] += reward
        self.rate[arm] += 1


class ConservativeThompsonSampling:
    """
    保守Thompson Sampling

    在探索和利用之间加入保守项
    """

    def __init__(self, num_arms: int, epsilon: float = 0.1, device: str = 'cpu'):
        """
        参数:
            epsilon: 保守因子
        """
        self.num_arms = num_arms
        self.epsilon = epsilon
        self.device = device

        self.alpha = torch.ones(num_arms, device=device)
        self.beta = torch.ones(num_arms, device=device)

        # 安全奖励下界
        self.safe_reward = 0.0

    def select_arm(self) -> int:
        """选择臂"""
        samples = torch.distributions.Beta(self.alpha, self.beta).sample()

        # 加入保守项
        conservative_samples = (1 - self.epsilon) * samples + self.epsilon * self.safe_reward

        return torch.argmax(conservative_samples).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.alpha[arm] += reward
        self.beta[arm] += (1 - reward)

        # 更新安全奖励
        if reward > self.safe_reward:
            self.safe_reward = reward


def run_thompson_comparison(num_arms: int = 5, num_steps: int = 1000,
                           bandit_probs: Optional[np.ndarray] = None,
                           seed: int = 42) -> dict:
    """
    比较Thompson Sampling与UCB

    参数:
        num_arms: 臂数量
        num_steps: 步数
        bandit_probs: 真实概率
        seed: 随机种子

    返回:
        results: 比较结果
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    if bandit_probs is None:
        bandit_probs = np.random.rand(num_arms)

    device = 'cpu'

    # Thompson Sampling
    ts = BernoulliThompsonSampling(num_arms, device=device)
    ts_rewards = []

    for _ in range(num_steps):
        arm = ts.select_arm()
        reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0
        ts.update(arm, reward)
        ts_rewards.append(reward)

    # UCB (对比基线)
    from ucb_algorithms import UCB1

    ucb = UCB1(num_arms, c=2.0, device=device)
    ucb_rewards = []

    for _ in range(num_steps):
        arm = ucb.select_arm()
        reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0
        ucb.update(arm, reward)
        ucb_rewards.append(reward)

    return {
        'thompson_sampling': {
            'total_reward': sum(ts_rewards),
            'cumulative': np.cumsum(ts_rewards),
            'estimated': ts.get_posterior_stats()['means']
        },
        'ucb': {
            'total_reward': sum(ucb_rewards),
            'cumulative': np.cumsum(ucb_rewards),
            'estimated': ucb.get_estimated_values()
        }
    }


if __name__ == "__main__":
    print("=" * 50)
    print("Thompson Sampling测试")
    print("=" * 50)

    # 测试Bernoulli Thompson Sampling
    print("\n--- Bernoulli Thompson Sampling ---")
    num_arms = 5
    true_probs = np.random.rand(num_arms)
    print(f"真实概率: {true_probs}")

    ts = BernoulliThompsonSampling(num_arms)

    total_reward = 0
    for step in range(500):
        arm = ts.select_arm()
        reward = 1.0 if np.random.rand() < true_probs[arm] else 0.0
        ts.update(arm, reward)
        total_reward += reward

    print(f"总奖励: {total_reward}")

    stats = ts.get_posterior_stats()
    print(f"后验均值: {stats['means']}")
    print(f"后验alpha: {stats['alpha']}")
    print(f"后验beta: {stats['beta']}")

    # 测试高斯Thompson Sampling
    print("\n--- Gaussian Thompson Sampling ---")
    gs = GaussianThompsonSampling(num_arms, prior_mean=0.0, prior_std=1.0, noise_std=0.1)

    for _ in range(100):
        arm = gs.select_arm()
        reward = np.random.randn() * 0.1 + (true_probs[arm] - 0.5) * 2
        gs.update(arm, reward)

    g_stats = gs.get_posterior_stats()
    print(f"后验均值: {g_stats['means']}")

    # 比较TS和UCB
    print("\n--- Thompson Sampling vs UCB 比较 ---")
    results = run_thompson_comparison(num_arms=5, num_steps=500)

    print(f"Thompson Sampling总奖励: {results['thompson_sampling']['total_reward']}")
    print(f"UCB总奖励: {results['ucb']['total_reward']}")

    print(f"\nThompson估计: {results['thompson_sampling']['estimated']}")
    print(f"UCB估计: {results['ucb']['estimated']}")

    print("\n测试完成！")
