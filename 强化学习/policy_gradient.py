# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / policy_gradient

本文件实现 policy_gradient 相关的算法功能。
"""

import numpy as np
import random


class PolicyGradient:
    """REINFORCE 算法实现（基于蒙特卡洛策略梯度）"""

    def __init__(self, state_dim, action_num, hidden_dim=32, lr=0.001, gamma=0.99):
        self.state_dim = state_dim
        self.action_num = action_num
        self.gamma = gamma
        self.lr = lr

        # 策略网络参数 (softmax 策略)
        fan_in = state_dim + hidden_dim
        scale_w = np.sqrt(2.0 / fan_in)
        self.w1 = np.random.randn(state_dim, hidden_dim) * scale_w
        self.b1 = np.zeros(hidden_dim)
        scale_w2 = np.sqrt(2.0 / (hidden_dim + action_num))
        self.w2 = np.random.randn(hidden_dim, action_num) * scale_w2
        self.b2 = np.zeros(action_num)

    def softmax(self, x):
        """Softmax 激活函数"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def forward(self, state):
        """前向传播，返回动作概率分布"""
        hidden = np.tanh(np.dot(state, self.w1) + self.b1)  # tanh 激活
        logits = np.dot(hidden, self.w2) + self.b2  # 未归一化的分数
        probs = self.softmax(logits)  # 动作概率
        return probs

    def choose_action(self, state):
        """根据策略概率分布采样动作"""
        probs = self.forward(state)
        return np.random.choice(self.action_num, p=probs)

    def compute_returns(self, rewards, gamma):
        """计算折扣回报 G_t = r_t + γ r_{t+1} + ... + γ^{T-t} r_T"""
        returns = []
        G = 0
        for reward in reversed(rewards):
            G = reward + gamma * G
            returns.insert(0, G)
        return np.array(returns)

    def update(self, trajectory):
        """根据一条轨迹更新策略参数
        梯度: ∇J(θ) = E[G_t * ∇log π(a_t|s_t; θ)]
        """
        states = np.array(trajectory["states"])  # (T, state_dim)
        actions = np.array(trajectory["actions"])  # (T,)
        rewards = trajectory["rewards"]  # (T,)

        # 计算每个时间步的折扣回报
        returns = self.compute_returns(rewards, self.gamma)
        # 标准化回报（降低方差）
        returns = (returns - np.mean(returns)) / (np.std(returns) + 1e-8)

        # 梯度更新
        for t in range(len(trajectory["states"])):
            state = states[t]
            action = actions[t]
            G_t = returns[t]

            # 前向传播获取概率
            probs = self.forward(state)  # (action_num,)
            # log π(a|s) 的梯度 = ∇log P(a) = 1/P(a) * ∇P(a)，softmax 简化: one_hot - prob
            # d(log π(a|s;θ)) / d(logits = prob[a] - 1 当 a 为所选动作
            d_logits = probs.copy()
            d_logits[action] -= 1  # 对选中的动作减少概率

            # 反向梯度（简化为单层）
            hidden = np.tanh(np.dot(state, self.w1) + self.b1)
            # 策略梯度：∇J = G_t * ∇log π(a|s) ≈ G_t * (d_logits * hidden)
            d_w2 = np.outer(hidden, d_logits) * G_t
            # d_tanh = (1 - tanh^2) ≈ (1 - hidden^2) 当 hidden 接近 tanh 输出
            d_hidden = np.dot(d_logits, self.w2.T) * (1 - hidden ** 2)
            d_w1 = np.outer(state, d_hidden) * G_t
            d_b1 = d_hidden * G_t
            d_b2 = d_logits * G_t

            # 梯度上升更新
            self.w2 += self.lr * d_w2
            self.b2 += self.lr * d_b2
            self.w1 += self.lr * d_w1
            self.b1 += self.lr * d_b1


def simple_env():
    """简单离散环境用于测试"""
    class SimpleEnv:
        def __init__(self):
            self.state_dim = 4
            self.action_num = 2

        def reset(self):
            return np.random.randn(self.state_dim).tolist()

        def step(self, action):
            next_state = np.random.randn(self.state_dim).tolist()
            reward = float(action) * 0.5 - 0.1  # 鼓励选择动作 1
            done = random.random() < 0.1
            return next_state, reward, done

    return SimpleEnv()


if __name__ == "__main__":
    # 测试 REINFORCE
    env = simple_env()
    agent = PolicyGradient(state_dim=4, action_num=2, lr=0.01, gamma=0.99)
    episodes = 100
    for ep in range(episodes):
        state = env.reset()
        trajectory = {"states": [], "actions": [], "rewards": []}
        done = False
        while not done:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            trajectory["states"].append(state)
            trajectory["actions"].append(action)
            trajectory["rewards"].append(reward)
            state = next_state
        agent.update(trajectory)
        total_reward = sum(trajectory["rewards"])
        if ep % 20 == 0:
            print(f"Episode {ep}, total_reward: {total_reward:.2f}")
    print("REINFORCE 训练完成")
