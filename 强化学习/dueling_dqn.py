# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / dueling_dqn

本文件实现 dueling_dqn 相关的算法功能。
"""

import numpy as np
import random
from collections import deque


class DuelingDQN:
    """Dueling DQN 算法"""

    def __init__(self, state_dim, action_dim, hidden_dim=128, lr=0.001,
                 gamma=0.99, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995,
                 memory_size=10000, batch_size=64, target_update_freq=200):
        """
        初始化 Dueling DQN

        参数:
            state_dim: 状态空间维度
            action_dim: 动作空间维度
            hidden_dim: 共享隐藏层维度
            lr: 学习率
            gamma: 折扣因子
            epsilon: 初始探索率
            epsilon_min: 最小探索率
            epsilon_decay: 探索率衰减系数
            memory_size: 经验回放容量
            batch_size: 批次大小
            target_update_freq: 目标网络更新频率
        """
        self.state_dim = state_dim  # 状态维度
        self.action_dim = action_dim  # 动作维度
        self.gamma = gamma  # 折扣因子
        self.epsilon = epsilon  # 探索率
        self.epsilon_min = epsilon_min  # 最小探索率
        self.epsilon_decay = epsilon_decay  # 探索率衰减
        self.batch_size = batch_size  # 批次大小
        self.target_update_freq = target_update_freq  # 目标网络更新频率
        self.train_step = 0  # 训练步数

        # 经验回放缓冲区
        self.memory = deque(maxlen=memory_size)

        # 初始化网络（共享层 + 价值分支 + 优势分支）
        self.q_network = self._build_network()
        self.target_network = self._build_network()
        self._sync_target()

    def _build_network(self):
        """
        构建 Dueling 网络结构

        网络结构:
            共享层 -> 价值分支 V(s)
                   -> 优势分支 A(s, a)
            Q(s,a) = V(s) + A(s,a) - mean(A)
        """
        np.random.seed(42)
        network = {
            # 共享层权重
            'shared_w1': np.random.randn(self.state_dim, 128) * 0.01,
            'shared_b1': np.zeros(128),
            # 价值分支权重（输出标量）
            'value_w1': np.random.randn(128, 64) * 0.01,
            'value_b1': np.zeros(64),
            'value_w2': np.random.randn(64, 1) * 0.01,
            'value_b2': np.zeros(1),
            # 优势分支权重（输出 action_dim 维向量）
            'advantage_w1': np.random.randn(128, 64) * 0.01,
            'advantage_b1': np.zeros(64),
            'advantage_w2': np.random.randn(64, self.action_dim) * 0.01,
            'advantage_b2': np.zeros(self.action_dim)
        }
        return network

    def _forward_shared(self, state, network):
        """共享层前向传播"""
        h = np.maximum(0, np.dot(state, network['shared_w1']) + network['shared_b1'])
        return h

    def _forward_value(self, shared_features, network):
        """价值分支前向传播，输出 V(s)"""
        h = np.maximum(0, np.dot(shared_features, network['value_w1']) + network['value_b1'])
        value = np.dot(h, network['value_w2']) + network['value_b2']
        return value.squeeze()  # 输出标量

    def _forward_advantage(self, shared_features, network):
        """优势分支前向传播，输出 A(s, a) 向量"""
        h = np.maximum(0, np.dot(shared_features, network['advantage_w1']) + network['advantage_b1'])
        advantage = np.dot(h, network['advantage_w2']) + network['advantage_b2']
        return advantage

    def _compute_q(self, state, network):
        """
        计算 Q 值（核心：价值 + 优势 - 均值）

        参数:
            state: 输入状态
            network: 网络权重
        返回:
            q_values: 各动作的 Q 值
        """
        shared = self._forward_shared(state, network)
        value = self._forward_value(shared, network)  # V(s)
        advantage = self._forward_advantage(shared, network)  # A(s,a)

        # Q(s,a) = V(s) + A(s,a) - mean(A)
        q_values = value + advantage - np.mean(advantage)
        return q_values

    def _sync_target(self):
        """同步目标网络"""
        self.target_network = {k: v.copy() for k, v in self.q_network.items()}

    def choose_action(self, state):
        """
        选择动作（epsilon-greedy）

        参数:
            state: 当前状态
        返回:
            action: 选择的动作索引
        """
        if random.random() < self.epsilon:
            action = random.randint(0, self.action_dim - 1)
        else:
            state = np.array(state).reshape(1, -1)
            q_values = self._compute_q(state, self.q_network)
            action = np.argmax(q_values)
        return action

    def store(self, state, action, reward, next_state, done):
        """存储转移样本"""
        self.memory.append((state, action, reward, next_state, done))

    def train(self):
        """训练网络"""
        if len(self.memory) < self.batch_size:
            return 0.0

        # 采样批次
        batch = random.sample(self.memory, self.batch_size)
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])

        # 计算当前 Q 值（在线网络）
        current_q = self._compute_q(states, self.q_network)
        current_q_selected = np.sum(current_q * np.eye(self.action_dim)[actions], axis=1)

        # 计算目标 Q 值（目标网络 + Double DQN 思想）
        next_q_target = self._compute_q(next_states, self.target_network)
        next_q_online = self._compute_q(next_states, self.q_network)
        best_actions = np.argmax(next_q_online, axis=1)
        next_q_selected = np.sum(next_q_target * np.eye(self.action_dim)[best_actions], axis=1)

        # TD 目标
        td_target = rewards + self.gamma * next_q_selected * (1 - dones)

        # 计算损失
        loss = np.mean((current_q_selected - td_target) ** 2)

        # 更新
        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self._sync_target()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return loss

    def get_state_value(self, state):
        """获取状态的 V(s) 值（用于调试/分析）"""
        state = np.array(state).reshape(1, -1)
        shared = self._forward_shared(state, self.q_network)
        return self._forward_value(shared, self.q_network)


if __name__ == "__main__":
    # 测试 Dueling DQN
    state_dim = 4
    action_dim = 2
    agent = DuelingDQN(state_dim, action_dim)

    # 模拟训练
    for ep in range(5):
        state = np.random.randn(state_dim)
        total_reward = 0
        for step in range(15):
            action = agent.choose_action(state)
            next_state = np.random.randn(state_dim)
            reward = random.uniform(-1, 1)
            done = random.random() < 0.1
            agent.store(state, action, reward, next_state, done)
            total_reward += reward
            state = next_state
            if done:
                break
        loss = agent.train()
        v_s = agent.get_state_value(state)
        print(f"Episode {ep+1}: reward={total_reward:.2f}, loss={loss:.4f}, "
              f"V(s)={v_s:.4f}, epsilon={agent.epsilon:.4f}")

    print("\nDueling DQN 测试完成!")
