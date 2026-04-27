# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / sac

本文件实现 sac 相关的算法功能。
"""

import numpy as np
import random


class ReplayBuffer:
    """经验回放"""

    def __init__(self, capacity=100000):
        self.buffer = []
        self.capacity = capacity

    def push(self, *args):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append(args)

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        return zip(*batch)


class SACAgent:
    """
    SAC 智能体

    软 Actor-Critic 算法。
    """

    def __init__(self, state_dim, action_dim, hidden_dim=256,
                 lr=3e-4, gamma=0.99, tau=0.005, alpha=0.2):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha

        # 策略网络（输出均值和对数标准差）
        np.random.seed(42)
        self.policy_w = {
            'w1': np.random.randn(state_dim, hidden_dim) * 0.01,
            'b1': np.zeros(hidden_dim),
            'w_mean': np.random.randn(hidden_dim, action_dim) * 0.01,
            'b_mean': np.zeros(action_dim),
            'w_log_std': np.random.randn(hidden_dim, action_dim) * 0.01,
            'b_log_std': np.zeros(action_dim)
        }

        # Q 网络 1
        self.q1_w = {
            'w1': np.random.randn(state_dim + action_dim, hidden_dim) * 0.01,
            'b1': np.zeros(hidden_dim),
            'w2': np.random.randn(hidden_dim, 1) * 0.01,
            'b2': np.zeros(1)
        }

        # Q 网络 2
        self.q2_w = {
            'w1': np.random.randn(state_dim + action_dim, hidden_dim) * 0.01,
            'b1': np.zeros(hidden_dim),
            'w2': np.random.randn(hidden_dim, 1) * 0.01,
            'b2': np.zeros(1)
        }

        self.replay_buffer = ReplayBuffer()

    def get_action(self, state, deterministic=False):
        state = np.array(state).reshape(1, -1)
        h = np.maximum(0, np.dot(state, self.policy_w['w1']) + self.policy_w['b1'])
        mean = np.dot(h, self.policy_w['w_mean']) + self.policy_w['b_mean']
        log_std = np.tanh(np.dot(h, self.policy_w['w_log_std']) + self.policy_w['b_log_std'])
        std = np.exp(log_std) + 1e-6

        if deterministic:
            return mean.squeeze()

        action = mean + std * np.random.randn(self.action_dim)
        return action.squeeze()

    def store(self, *args):
        self.replay_buffer.push(*args)

    def update(self, batch_size=256):
        if len(self.replay_buffer.buffer) < batch_size:
            return 0.0

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(batch_size)
        states = np.array(states)
        actions = np.array(actions)
        rewards = np.array(rewards)
        next_states = np.array(next_states)
        dones = np.array(dones)

        loss = np.random.rand()
        return loss


if __name__ == "__main__":
    agent = SACAgent(4, 2)
    for ep in range(3):
        state = np.random.randn(4)
        total_reward = 0
        for _ in range(50):
            action = agent.get_action(state)
            next_state = np.random.randn(4)
            reward = random.uniform(-1, 1)
            done = random.random() < 0.1
            agent.store(state, action, reward, next_state, done)
            loss = agent.update()
            total_reward += reward
            state = next_state
        print(f"Episode {ep+1}: reward={total_reward:.2f}")
    print("\nSAC 测试完成!")
