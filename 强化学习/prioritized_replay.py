# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / prioritized_replay



本文件实现 prioritized_replay 相关的算法功能。

"""



import numpy as np

import random

from collections import deque





class PrioritizedReplayBuffer:

    """优先经验回放缓冲区"""



    def __init__(self, capacity, alpha=0.6, beta=0.4, beta_increment=0.001, epsilon=1e-6):

        """

        初始化优先经验回放缓冲区



        参数:

            capacity: 缓冲区容量

            alpha: 优先级指数（0=均匀采样，1=完全优先）

            beta: 重要性采样指数（初始值）

            beta_increment: 每个采样批次 beta 的增量

            epsilon: 防止零优先级的微小常数

        """

        self.capacity = capacity  # 缓冲区容量

        self.alpha = alpha  # 优先级指数

        self.beta = beta  # 重要性采样指数

        self.beta_increment = beta_increment  # beta 增量

        self.epsilon = epsilon  # 防止除零的小常数

        self.buffer = deque(maxlen=capacity)  # 存储样本

        self.priorities = deque(maxlen=capacity)  # 存储优先级

        self.max_priority = 1.0  # 最大优先级初始值



    def push(self, state, action, reward, next_state, done):

        """

        添加样本到缓冲区，赋予最大优先级



        参数:

            state: 当前状态

            action: 执行的动作

            reward: 奖励

            next_state: 下一个状态

            done: 是否结束

        """

        # 新样本赋予最大优先级，确保能被采样

        self.buffer.append((state, action, reward, next_state, done))

        self.priorities.append(self.max_priority)



    def sample(self, batch_size):

        """

        基于优先级采样批次数据



        参数:

            batch_size: 批次大小

        返回:

            批次样本、采样概率、重要性权重、样本索引

        """

        if len(self.buffer) < batch_size:

            return None, None, None, None



        # 将优先级转换为概率分布

        priorities = np.array(self.priorities)

        # 归一化优先级

        probs = priorities / np.sum(priorities)



        # 根据概率采样索引

        indices = np.random.choice(len(self.buffer), batch_size, p=probs, replace=False)



        # 计算重要性采样权重

        # w_i = (N * P(i))^(-β)

        weights = (len(self.buffer) * probs[indices]) ** (-self.beta)

        # 归一化权重，防止权重过大

        weights = weights / np.max(weights)



        # 更新 beta

        self.beta = min(1.0, self.beta + self.beta_increment)



        # 提取批次样本

        batch = [self.buffer[i] for i in indices]

        states = np.array([t[0] for t in batch])

        actions = np.array([t[1] for t in batch])

        rewards = np.array([t[2] for t in batch])

        next_states = np.array([t[3] for t in batch])

        dones = np.array([t[4] for t in batch])



        return (states, actions, rewards, next_states, dones), weights, 1.0 / probs[indices], indices



    def update_priorities(self, indices, td_errors):

        """

        更新采样样本的优先级



        参数:

            indices: 样本索引列表

            td_errors: 对应的 TD 误差列表

        """

        for idx, td in zip(indices, td_errors):

            # p_i = |TD_i|^α + ε

            priority = (abs(td) + self.epsilon) ** self.alpha

            self.priorities[idx] = priority

            # 更新最大优先级

            if priority > self.max_priority:

                self.max_priority = priority



    def __len__(self):

        """返回缓冲区当前样本数"""

        return len(self.buffer)





class DQNPER:

    """带优先经验回放的 DQN 算法"""



    def __init__(self, state_dim, action_dim, hidden_dim=128, lr=0.001,

                 gamma=0.99, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995,

                 capacity=10000, batch_size=64, target_update_freq=100,

                 alpha=0.6, beta=0.4):

        """

        初始化带优先经验回放的 DQN



        参数:

            state_dim: 状态空间维度

            action_dim: 动作空间维度

            hidden_dim: 隐藏层维度

            lr: 学习率

            gamma: 折扣因子

            epsilon: 初始探索率

            epsilon_min: 最小探索率

            epsilon_decay: 探索率衰减

            capacity: 经验回放容量

            batch_size: 批次大小

            target_update_freq: 目标网络更新频率

            alpha: 优先级指数

            beta: 初始重要性采样指数

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.gamma = gamma

        self.epsilon = epsilon

        self.epsilon_min = epsilon_min

        self.epsilon_decay = epsilon_decay

        self.batch_size = batch_size

        self.target_update_freq = target_update_freq

        self.train_step = 0



        # 优先经验回放缓冲区

        self.memory = PrioritizedReplayBuffer(capacity, alpha, beta)



        # 初始化网络

        self.q_network = self._init_network()

        self.target_network = self._init_network()

        self._update_target()



    def _init_network(self):

        """初始化网络权重"""

        np.random.seed(42)

        return {

            'w1': np.random.randn(self.state_dim, 128) * 0.01,

            'b1': np.zeros(128),

            'w2': np.random.randn(128, self.action_dim) * 0.01,

            'b2': np.zeros(self.action_dim)

        }



    def _forward(self, network, state):

        """前向传播"""

        h = np.maximum(0, np.dot(state, network['w1']) + network['b1'])

        q = np.dot(h, network['w2']) + network['b2']

        return q



    def _update_target(self):

        """更新目标网络"""

        self.target_network = {

            k: v.copy() for k, v in self.q_network.items()

        }



    def choose_action(self, state):

        """选择动作（epsilon-greedy）"""

        if random.random() < self.epsilon:

            return random.randint(0, self.action_dim - 1)

        state = np.array(state).reshape(1, -1)

        q = self._forward(self.q_network, state)

        return np.argmax(q)



    def store(self, state, action, reward, next_state, done):

        """存储样本"""

        self.memory.push(state, action, reward, next_state, done)



    def train(self):

        """训练网络"""

        result = self.memory.sample(self.batch_size)

        if result[0] is None:

            return 0.0



        batch_data, weights, IS_weights, indices = result

        states, actions, rewards, next_states, dones = batch_data



        # 计算当前 Q 值

        current_q = self._forward(self.q_network, states)

        current_q = np.sum(current_q * np.eye(self.action_dim)[actions], axis=1)



        # 计算目标 Q 值

        next_q = self._forward(self.target_network, next_states)

        next_q_max = np.max(next_q, axis=1)

        td_target = rewards + self.gamma * next_q_max * (1 - dones)



        # 加权 TD 误差

        td_errors = (current_q - td_target) * weights

        loss = np.mean(td_errors ** 2)



        # 更新优先级

        self.memory.update_priorities(indices, td_errors)



        # 更新网络（简化版）

        self.train_step += 1

        if self.train_step % self.target_update_freq == 0:

            self._update_target()



        if self.epsilon > self.epsilon_min:

            self.epsilon *= self.epsilon_decay



        return loss





if __name__ == "__main__":

    # 测试优先经验回放

    state_dim = 4

    action_dim = 2

    agent = DQNPER(state_dim, action_dim, capacity=1000)



    # 模拟收集经验

    for ep in range(3):

        state = np.random.randn(state_dim)

        total_reward = 0

        for step in range(20):

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

        print(f"Episode {ep+1}: reward={total_reward:.2f}, loss={loss:.4f}, "

              f"epsilon={agent.epsilon:.4f}, beta={agent.memory.beta:.4f}")



    print("\n优先经验回放 PER 测试完成!")

