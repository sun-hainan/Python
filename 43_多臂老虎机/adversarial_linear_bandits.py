# -*- coding: utf-8 -*-

"""

算法实现：多臂老虎机 / adversarial_linear_bandits



本文件实现 adversarial_linear_bandits 相关的算法功能。

"""



import numpy as np

import torch

import math

from typing import List, Tuple, Optional





class Exp3Linear:

    """

    Exp3-Linear算法



    将Exp3扩展到线性奖励结构

    """



    def __init__(self, dimension: int, eta: float = 0.1, device: str = 'cpu'):

        """

        参数:

            dimension: 特征维度

            eta: 学习率

        """

        self.dimension = dimension

        self.eta = eta

        self.device = device



        # 权重向量

        self.weights = torch.zeros(dimension, device=device)

        self.total_weight = 0.0



    def select_action(self) -> torch.Tensor:

        """选择动作（特征向量）"""

        # 归一化权重作为概率分布

        probs = torch.softmax(self.weights, dim=0)



        # 采样

        action = torch.zeros(self.dimension, device=self.device)

        action[torch.multinomial(probs, 1).item()] = 1.0



        return action



    def update(self, action: torch.Tensor, reward: float):

        """更新"""

        # 估计重要性加权

        prob = torch.softmax(self.weights, dim=0)

        action_prob = prob[torch.argmax(action).item()]



        # 更新权重

        self.weights += self.eta * reward * action / (action_prob + 1e-10)





class LinUCBAdversarial:

    """

    线性UCB对抗版本

    """



    def __init__(self, dimension: int, delta: float = 0.1, device: str = 'cpu'):

        self.dimension = dimension

        self.delta = delta

        self.device = device



        # 设计矩阵

        self.A = torch.eye(dimension, device=device)

        self.b = torch.zeros(dimension, device=device)



        # 正则化

        self.lambda_reg = 0.1



    def compute_ucb(self, action: torch.Tensor) -> float:

        """计算UCB"""

        # 最小二乘估计

        A_inv = torch.inverse(self.A)

        theta = A_inv @ self.b



        # 预测

        pred = (theta * action).sum()



        # 置信项

        action_norm = (action @ A_inv @ action).item()

        confidence = math.sqrt(

            action_norm * (self.dimension * math.log(1 / self.delta) + math.log(1 + 1 / self.lambda_reg))

        )



        return pred + confidence



    def select_action(self) -> torch.Tensor:

        """选择动作"""

        # 简化：随机选择（实际需要动作空间）

        action = torch.randn(self.dimension, device=self.device)

        action = action / torch.norm(action)



        return action



    def update(self, action: torch.Tensor, reward: float):

        """更新"""

        # 更新设计矩阵

        self.A += torch.outer(action, action)



        # 更新响应向量

        self.b += reward * action





class FollowTheLeader:

    """

    Follow the Leader (FTL) 算法



    线性老虎机的简单启发式方法

    """



    def __init__(self, dimension: int, device: str = 'cpu'):

        self.dimension = dimension

        self.device = device



        self.history_actions = []

        self.history_rewards = []



    def select_action(self) -> torch.Tensor:

        """选择历史最优动作"""

        if not self.history_actions:

            action = torch.randn(self.dimension, device=self.device)

            return action / torch.norm(action)



        # 找到历史累计奖励最高的动作

        action_rewards = {}

        for action, reward in zip(self.history_actions, self.history_rewards):

            key = tuple(action.tolist())

            if key not in action_rewards:

                action_rewards[key] = 0. + reward

            else:

                action_rewards[key] += reward



        best_action = max(action_rewards.items(), key=lambda x: x[1])[0]

        return torch.tensor(best_action, device=self.device)



    def update(self, action: torch.Tensor, reward: float):

        """更新"""

        self.history_actions.append(action.clone())

        self.history_rewards.append(reward)





class RandomProjections:

    """

    基于随机投影的线性老虎机



    将高维问题降维后处理

    """



    def __init__(self, original_dim: int, projected_dim: int, device: str = 'cpu'):

        self.original_dim = original_dim

        self.projected_dim = projected_dim

        self.device = device



        # 随机投影矩阵

        self.projection = torch.randn(projected_dim, original_dim, device=device) / math.sqrt(projected_dim)



        # 投影后的UCB

        self.ucb = LinUCBAdversarial(projected_dim, device=device)



    def project_action(self, action: torch.Tensor) -> torch.Tensor:

        """投影动作"""

        return self.projection @ action



    def select_action(self) -> torch.Tensor:

        """选择动作"""

        return self.ucb.select_action()



    def update(self, original_action: torch.Tensor, reward: float):

        """更新"""

        projected = self.project_action(original_action)

        self.ucb.update(projected, reward)





class GradientBanditLinear:

    """

    线性老虎机的梯度上升算法

    """



    def __init__(self, dimension: int, alpha: float = 0.1, device: str = 'cpu'):

        self.dimension = dimension

        self.alpha = alpha

        self.device = device



        # 偏好向量

        self.preference = torch.zeros(dimension, device=device)



        # 基线

        self.baseline = 0.0

        self.t = 0



    def select_action(self) -> torch.Tensor:

        """基于softmax选择"""

        exp_pref = torch.exp(self.preference - self.preference.max())

        probs = exp_pref / exp_pref.sum()



        # 采样

        selected_idx = torch.multinomial(probs, 1).item()



        action = torch.zeros(self.dimension, device=self.device)

        action[selected_idx] = 1.0



        return action



    def update(self, action: torch.Tensor, reward: float):

        """更新偏好"""

        self.t += 1



        # 更新基线

        self.baseline = 0.99 * self.baseline + 0.01 * reward



        # 计算梯度

        exp_pref = torch.exp(self.preference - self.preference.max())

        probs = exp_pref / exp_pref.sum()



        action_idx = torch.argmax(action).item()



        # 偏好更新

        for i in range(self.dimension):

            if i == action_idx:

                self.preference[i] += self.alpha * (reward - self.baseline) * (1 - probs[i])

            else:

                self.preference[i] -= self.alpha * (reward - self.baseline) * probs[i]





def run_adversarial_linear_comparison(dimension: int = 10, horizon: int = 1000,

                                     seed: int = 42):

    """

    对抗线性老虎机算法比较

    """

    np.random.seed(seed)

    torch.manual_seed(seed)



    print(f"维度: {dimension}, 时间范围: {horizon}")



    algorithms = {

        'Exp3Linear': Exp3Linear(dimension),

        'FTL': FollowTheLeader(dimension),

        'Gradient': GradientBanditLinear(dimension)

    }



    results = {}



    for name, algo in algorithms.items():

        total_reward = 0



        for step in range(horizon):

            # 选择动作

            action = algo.select_action()



            # 对抗奖励（最差情况）

            reward = -torch.dot(action, torch.randn(dimension)).item()



            algo.update(action, reward)

            total_reward += reward



        results[name] = {

            'total_reward': total_reward,

            'avg_reward': total_reward / horizon

        }



        print(f"{name}: 总奖励={total_reward:.2f}, 平均={results[name]['avg_reward']:.4f}")



    return results





if __name__ == "__main__":

    print("=" * 50)

    print("对抗线性老虎机测试")

    print("=" * 50)



    # 测试

    print("\n--- 算法比较 ---")

    run_adversarial_linear_comparison(dimension=10, horizon=500)



    print("\n测试完成！")

