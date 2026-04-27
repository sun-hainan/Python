# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / double_dqn

本文件实现 double_dqn 相关的算法功能。
"""

import numpy as np
import random
from collections import deque


class DoubleDQN:
    """Double DQN 算法类"""

    def __init__(self, state_dim, action_dim, hidden_dim=128, lr=0.001,
                 gamma=0.99, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995,
                 memory_size=10000, batch_size=64, target_update_freq=100):
        """
        初始化 Double DQN

        参数:
            state_dim: 状态空间维度
            action_dim: 动作空间维度
            hidden_dim: 隐藏层维度
            lr: 学习率
            gamma: 折扣因子
            epsilon: 初始探索率
            epsilon_min: 最小探索率
            epsilon_decay: 探索率衰减系数
            memory_size: 经验回放缓冲区大小
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
        self.train_step = 0  # 训练步数计数器

        # 在线网络和目标网络初始化（共享结构）
        self.q_network = self._build_network(state_dim, action_dim, hidden_dim)
        self.target_network = self._build_network(state_dim, action_dim, hidden_dim)
        self._update_target_network()  # 初始同步

        # 经验回放缓冲区
        self.memory = deque(maxlen=memory_size)
        self.optimizer = None  # 优化器（子类实现）

    def _build_network(self, state_dim, action_dim, hidden_dim):
        """构建 Q 网络（简化为线性层模拟）"""
        # 实际应用中应使用 torch 或 tensorflow
        # 这里使用随机权重模拟网络结构
        np.random.seed(42)
        weights = {
            'w1': np.random.randn(state_dim, hidden_dim) * 0.01,
            'b1': np.zeros(hidden_dim),
            'w2': np.random.randn(hidden_dim, hidden_dim) * 0.01,
            'b2': np.zeros(hidden_dim),
            'w3': np.random.randn(hidden_dim, action_dim) * 0.01,
            'b3': np.zeros(action_dim)
        }
        return weights

    def _update_target_network(self):
        """将在线网络权重复制到目标网络"""
        # 实际应用中需要 deep copy
        self.target_network = {
            'w1': self.q_network['w1'].copy(),
            'b1': self.q_network['b1'].copy(),
            'w2': self.q_network['w2'].copy(),
            'b2': self.q_network['b2'].copy(),
            'w3': self.q_network['w3'].copy(),
            'b3': self.q_network['b3'].copy()
        }

    def _forward(self, network, state):
        """前向传播计算 Q 值"""
        # 简化的前向传播
        h1 = np.dot(state, network['w1']) + network['b1']
        h1 = np.relu(h1)
        h2 = np.dot(h1, network['w2']) + network['b2']
        h2 = np.relu(h2)
        q_values = np.dot(h2, network['w3']) + network['b3']
        return q_values

    def choose_action(self, state):
        """
        根据当前状态选择动作（epsilon-greedy 策略）

        参数:
            state: 当前状态
        返回:
            action: 选择的动作
        """
        if random.random() < self.epsilon:
            # 随机探索
            action = random.randint(0, self.action_dim - 1)
        else:
            # 在线网络选择动作（贪心）
            state = np.array(state).reshape(1, -1)
            q_values = self._forward(self.q_network, state)
            action = np.argmax(q_values)
        return action

    def store_transition(self, state, action, reward, next_state, done):
        """
        存储转移样本到经验回放缓冲区

        参数:
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一个状态
            done: 是否结束
        """
        self.memory.append((state, action, reward, next_state, done))

    def train(self):
        """从经验回放缓冲区采样并训练网络"""
        if len(self.memory) < self.batch_size:
            return

        # 随机采样批次数据
        batch = random.sample(self.memory, self.batch_size)
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])

        # 计算当前 Q 值
        current_q = self._forward(self.q_network, states)
        # 提取实际选择的动作对应的 Q 值
        current_q = np.sum(current_q * np.eye(self.action_dim)[actions], axis=1)

        # Double DQN 核心：使用在线网络选择动作，目标网络评估
        # 在线网络选择下一个状态下的最优动作
        next_q_online = self._forward(self.q_network, next_states)
        best_actions = np.argmax(next_q_online, axis=1)
        # 目标网络计算该动作的 Q 值
        next_q_target = self._forward(self.target_network, next_states)
        next_q = np.sum(next_q_target * np.eye(self.action_dim)[best_actions], axis=1)

        # 计算 TD 目标
        td_target = rewards + self.gamma * next_q * (1 - dones)

        # 计算损失并更新（简化为梯度下降）
        loss = np.mean((current_q - td_target) ** 2)
        # 实际应用中通过反向传播更新权重

        # 更新训练步数
        self.train_step += 1

        # 定期更新目标网络
        if self.train_step % self.target_update_freq == 0:
            self._update_target_network()

        # 衰减探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return loss

    def save(self, filepath):
        """保存模型权重"""
        # 实际应用中保存网络权重到文件
        data = {
            'q_network': self.q_network,
            'target_network': self.target_network,
            'epsilon': self.epsilon
        }
        np.save(filepath, data, allow_pickle=True)

    def load(self, filepath):
        """加载模型权重"""
        data = np.load(filepath, allow_pickle=True).item()
        self.q_network = data['q_network']
        self.target_network = data['target_network']
        self.epsilon = data['epsilon']


if __name__ == "__main__":
    # 测试 Double DQN
    state_dim = 4  # 如 CartPole 状态维度
    action_dim = 2  # 左/右两个动作
    agent = DoubleDQN(state_dim, action_dim)

    # 模拟收集经验
    for episode in range(5):
        state = np.random.randn(state_dim)
        total_reward = 0
        for step in range(10):
            action = agent.choose_action(state)
            next_state = np.random.randn(state_dim)
            reward = random.uniform(-1, 1)
            done = random.random() < 0.1
            agent.store_transition(state, action, reward, next_state, done)
            total_reward += reward
            state = next_state
            if done:
                break
        # 训练网络
        loss = agent.train()
        print(f"Episode {episode+1}: reward={total_reward:.2f}, loss={loss:.4f}, epsilon={agent.epsilon:.4f}")

    print("\nDouble DQN 测试完成!")
