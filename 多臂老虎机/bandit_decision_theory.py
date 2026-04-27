# -*- coding: utf-8 -*-
"""
算法实现：多臂老虎机 / bandit_decision_theory

本文件实现 bandit_decision_theory 相关的算法功能。
"""

import numpy as np
import torch
from typing import List, Dict, Tuple


class RiskSensitiveBandit:
    """
    风险敏感老虎机

    使用CVaR、CVaR等风险度量进行决策
    """

    def __init__(self, num_arms: int, risk_measure='cvar', alpha: float = 0.1, device: str = 'cpu'):
        """
        参数:
            risk_measure: 'cvar', 'variance', 'worst_case'
            alpha: 风险参数（CVaR的百分位）
        """
        self.num_arms = num_arms
        self.risk_measure = risk_measure
        self.alpha = alpha
        self.device = device

        # 统计
        self.rewards = [[] for _ in range(num_arms)]
        self.counts = torch.zeros(num_arms, device=device)

    def add_reward(self, arm: int, reward: float):
        """添加奖励记录"""
        self.rewards[arm].append(reward)
        self.counts[arm] += 1

    def get_risk_score(self, arm: int) -> float:
        """计算风险分数"""
        if not self.rewards[arm]:
            return 0.0

        rewards = np.array(self.rewards[arm])

        if self.risk_measure == 'cvar':
            # Conditional Value at Risk
            var = np.percentile(rewards, 100 * self.alpha)
            cvar = rewards[rewards <= var].mean()
            return cvar

        elif self.risk_measure == 'variance':
            return np.var(rewards)

        elif self.risk_measure == 'worst_case':
            return np.min(rewards)

        else:
            return np.mean(rewards)

    def select_arm(self) -> int:
        """选择臂（风险厌恶）"""
        scores = [self.get_risk_score(arm) for arm in range(self.num_arms)]
        return int(np.argmax(scores))


class ThompsonSamplingRisk:
    """
    带风险控制的Thompson Sampling
    """

    def __init__(self, num_arms: int, risk_weight: float = 0.5, device: str = 'cpu'):
        self.num_arms = num_arms
        self.risk_weight = risk_weight
        self.device = device

        self.alpha = torch.ones(num_arms, device=device)
        self.beta = torch.ones(num_arms, device=device)

        # 风险历史
        self.risk_scores = torch.zeros(num_arms, device=device)

    def select_arm(self) -> int:
        """采样并选择"""
        # 从后验采样
        samples = torch.distributions.Beta(self.alpha, self.beta).sample()

        # 结合风险调整
        adjusted = (1 - self.risk_weight) * samples + self.risk_weight * self.risk_scores

        return torch.argmax(adjusted).item()

    def update(self, arm: int, reward: float):
        """更新"""
        self.alpha[arm] += reward
        self.beta[arm] += (1 - reward)

        # 更新风险分数
        if self.counts[arm] > 0:
            self.risk_scores[arm] = self.alpha[arm] / (self.alpha[arm] + self.beta[arm])

    @property
    def counts(self):
        return (self.alpha + self.beta - 2).clamp(min=0)


class MultiObjectiveBandit:
    """
    多目标老虎机

    同时优化多个目标（如收益和风险）
    """

    def __init__(self, num_arms: int, num_objectives: int = 2, device: str = 'cpu'):
        self.num_arms = num_arms
        self.num_objectives = num_objectives
        self.device = device

        # 每个臂每个目标的统计
        self.means = torch.zeros(num_arms, num_objectives, device=device)
        self.counts = torch.zeros(num_arms, device=device)

    def select_arm(self, weights: torch.Tensor) -> int:
        """
        根据权重选择臂

        参数:
            weights: 目标的权重向量
        """
        # 加权分数
        scores = (self.means * weights).sum(dim=1)

        # 加探索项
        exploration = torch.sqrt(1 / (self.counts + 1e-10))
        ucb = scores + exploration

        return torch.argmax(ucb).item()

    def update(self, arm: int, rewards: torch.Tensor):
        """更新"""
        self.counts[arm] += 1
        n = self.counts[arm]

        for obj in range(self.num_objectives):
            self.means[arm, obj] = self.means[arm, obj] + (rewards[obj] - self.means[arm, obj]) / n


class BanditWithContext:
    """
    带上下文的决策支持

    结合上下文信息进行决策
    """

    def __init__(self, num_arms: int, context_dim: int, device: str = 'cpu'):
        self.num_arms = num_arms
        self.context_dim = context_dim
        self.device = device

        # 上下文-奖励映射
        self.context_weights = torch.randn(num_arms, context_dim, device=device) * 0.1

    def predict_reward(self, arm: int, context: torch.Tensor) -> float:
        """预测奖励"""
        return (self.context_weights[arm] * context).sum().item()

    def select_arm(self, context: torch.Tensor) -> int:
        """选择臂"""
        predictions = [
            self.predict_reward(arm, context) for arm in range(self.num_arms)
        ]
        return int(np.argmax(predictions))

    def update(self, arm: int, context: torch.Tensor, reward: float, lr=0.1):
        """更新"""
        pred = self.predict_reward(arm, context)
        error = reward - pred

        self.context_weights[arm] += lr * error * context


class ParetoBandit:
    """
    Pareto最优老虎机

    寻找Pareto前沿
    """

    def __init__(self, num_arms: int, num_objectives: int = 2, device: str = 'cpu'):
        self.num_arms = num_arms
        self.num_objectives = num_objectives
        self.device = device

        self.means = torch.zeros(num_arms, num_objectives, device=device)
        self.counts = torch.zeros(num_arms, device=device)

    def is_dominated(self, arm: int) -> bool:
        """检查臂是否被支配"""
        for other in range(self.num_arms):
            if other == arm:
                continue

            # 检查other是否支配arm
            dominates = True
            for obj in range(self.num_objectives):
                if self.means[arm, obj] > self.means[other, obj]:
                    dominates = False
                    break

            if dominates:
                return True

        return False

    def get_pareto_front(self) -> List[int]:
        """获取Pareto前沿"""
        front = []
        for arm in range(self.num_arms):
            if not self.is_dominated(arm):
                front.append(arm)
        return front

    def select_arm(self) -> int:
        """从Pareto前沿选择"""
        front = self.get_pareto_front()
        if not front:
            return np.random.randint(self.num_arms)

        # 从前沿随机选择
        return front[np.random.randint(len(front))]


def run_risk_sensitive_comparison(num_arms: int = 5, horizon: int = 500, seed: int = 42):
    """运行风险敏感算法比较"""
    np.random.seed(seed)

    true_probs = np.random.rand(num_arms)

    print(f"真实概率: {true_probs}")

    # 标准TS
    from thompson_sampling import BernoulliThompsonSampling
    ts = BernoulliThompsonSampling(num_arms, device='cpu')

    # 风险敏感TS
    ts_risk = ThompsonSamplingRisk(num_arms, risk_weight=0.3)

    ts_rewards = []
    ts_risk_rewards = []

    for step in range(horizon):
        # 标准TS
        arm = ts.select_arm()
        reward = 1.0 if np.random.rand() < true_probs[arm] else 0.0
        ts.update(arm, reward)
        ts_rewards.append(reward)

        # 风险敏感TS
        arm_r = ts_risk.select_arm()
        reward_r = 1.0 if np.random.rand() < true_probs[arm_r] else 0.0
        ts_risk.update(arm_r, reward_r)
        ts_risk_rewards.append(reward_r)

    print(f"\nThompson Sampling: 总奖励={sum(ts_rewards)}")
    print(f"Risk-sensitive TS: 总奖励={sum(ts_risk_rewards)}")

    return {
        'ts': sum(ts_rewards),
        'ts_risk': sum(ts_risk_rewards)
    }


if __name__ == "__main__":
    print("=" * 50)
    print("老虎机决策理论测试")
    print("=" * 50)

    # 风险敏感老虎机
    print("\n--- 风险敏感老虎机 ---")
    rs_bandit = RiskSensitiveBandit(5, risk_measure='cvar')

    for arm in range(5):
        for _ in range(20):
            reward = 1.0 if np.random.rand() < 0.3 + arm * 0.1 else 0.0
            rs_bandit.add_reward(arm, reward)

    for arm in range(5):
        print(f"  臂{arm} CVaR: {rs_bandit.get_risk_score(arm):.4f}")

    # 多目标老虎机
    print("\n--- 多目标老虎机 ---")
    mo_bandit = MultiObjectiveBandit(5, num_objectives=2)

    for arm in range(5):
        mo_bandit.update(arm, torch.tensor([0.5 + arm * 0.1, 1.0 - arm * 0.1]))

    weights = torch.tensor([0.6, 0.4])
    arm = mo_bandit.select_arm(weights)
    print(f"选择臂: {arm}")

    # 比较
    print("\n--- 风险敏感比较 ---")
    run_risk_sensitive_comparison(num_arms=5, horizon=300)

    print("\n测试完成！")
