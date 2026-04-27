# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / actor_critic

本文件实现 actor_critic 相关的算法功能。
"""

import numpy as np
import random


class ActorCritic:
    """简化版 Actor-Critic 算法"""

    def __init__(self, state_dim, action_num, hidden_dim=32, actor_lr=0.001,
                 critic_lr=0.01, gamma=0.99):
        self.state_dim = state_dim
        self.action_num = action_num
        self.gamma = gamma

        # Actor（策略网络）参数
        fan_in_actor = state_dim + hidden_dim
        scale = np.sqrt(2.0 / fan_in_actor)
        self.actor_w1 = np.random.randn(state_dim, hidden_dim) * scale
        self.actor_b1 = np.zeros(hidden_dim)
        scale_w2 = np.sqrt(2.0 / (hidden_dim + action_num))
        self.actor_w2 = np.random.randn(hidden_dim, action_num) * scale_w2
        self.actor_b2 = np.zeros(action_num)
        self.actor_lr = actor_lr

        # Critic（价值网络）参数
        scale_c1 = np.sqrt(2.0 / (state_dim + hidden_dim))
        self.critic_w1 = np.random.randn(state_dim, hidden_dim) * scale_c1
        self.critic_b1 = np.zeros(hidden_dim)
        scale_c2 = np.sqrt(2.0 / (hidden_dim + 1))
        self.critic_w2 = np.random.randn(hidden_dim, 1) * scale_c2
        self.critic_b2 = np.zeros(1)
        self.critic_lr = critic_lr

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def forward_actor(self, state):
        """Actor 前向传播：计算动作概率"""
        hidden = np.tanh(np.dot(state, self.actor_w1) + self.actor_b1)
        logits = np.dot(hidden, self.actor_w2) + self.actor_b2
        return self.softmax(logits), hidden

    def forward_critic(self, state):
        """Critic 前向传播：估计状态价值 V(s)"""
        hidden = np.tanh(np.dot(state, self.critic_w1) + self.critic_b1)
        value = np.dot(hidden, self.critic_w2) + self.critic_b2
        return float(value)

    def choose_action(self, state):
        """根据 Actor 策略采样动作"""
        probs, _ = self.forward_actor(state)
        return np.random.choice(self.action_num, p=probs)

    def update(self, state, action, reward, next_state, done):
        """TD 误差驱动的 Actor-Critic 更新"""
        # ---------- Critic 更新 ----------
        current_v = self.forward_critic(state)
        next_v = 0 if done else self.forward_critic(next_state)
        # TD 目标
        td_target = reward + self.gamma * next_v
        # TD 误差 δ = r + γV(s') - V(s)
        td_error = td_target - current_v

        # Critic 梯度 (均方误差 d(td_error^2)/dparams)
        hidden_c = np.tanh(np.dot(state, self.critic_w1) + self.critic_b1)
        d_value = td_error
        d_critic_w2 = np.outer(hidden_c, [d_value])
        d_critic_b2 = [d_value]
        d_hidden_c = d_value * self.critic_w2.flatten() * (1 - hidden_c ** 2)
        d_critic_w1 = np.outer(state, d_hidden_c)
        d_critic_b1 = d_hidden_c

        self.critic_w2 -= self.critic_lr * d_critic_w2
        self.critic_b2 -= self.critic_lr * d_critic_b2
        self.critic_w1 -= self.critic_lr * d_critic_w1
        self.critic_b1 -= self.critic_lr * d_critic_b1

        # ---------- Actor 更新 ----------
        probs, hidden_a = self.forward_actor(state)
        # 策略梯度: ∇J = δ * ∇log π(a|s)
        # softmax 梯度: d_log_pi[a] = 1 - π(a)，其他为 -π(a')
        d_logits = -probs.copy()
        d_logits[action] += 1
        # 近似策略梯度（使用 TD 误差作为 baseline）
        d_actor_w2 = np.outer(hidden_a, d_logits) * td_error
        d_hidden_a = np.dot(d_logits, self.actor_w2.T) * (1 - hidden_a ** 2)
        d_actor_w1 = np.outer(state, d_hidden_a) * td_error
        d_actor_b1 = d_hidden_a * td_error
        d_actor_b2 = d_logits * td_error

        self.actor_w2 += self.actor_lr * d_actor_w2
        self.actor_b2 += self.actor_lr * d_actor_b2
        self.actor_w1 += self.actor_lr * d_actor_w1
        self.actor_b1 += self.actor_lr * d_actor_b1

        return td_error


def simple_env():
    """测试用简单环境"""
    class SimpleEnv:
        def __init__(self):
            self.state_dim = 4
            self.action_num = 2

        def reset(self):
            return np.random.randn(self.state_dim).tolist()

        def step(self, action):
            next_state = np.random.randn(self.state_dim).tolist()
            reward = float(action) * 0.5 - 0.1
            done = random.random() < 0.1
            return next_state, reward, done

    return SimpleEnv()


if __name__ == "__main__":
    # 测试 Actor-Critic
    env = simple_env()
    agent = ActorCritic(state_dim=4, action_num=2, actor_lr=0.001, critic_lr=0.01)
    episodes = 100
    for ep in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False
        while not done:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.update(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
        if ep % 20 == 0:
            print(f"Episode {ep}, reward: {total_reward:.2f}")
    print("Actor-Critic 训练完成")
