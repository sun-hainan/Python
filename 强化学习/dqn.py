# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / dqn



本文件实现 dqn 相关的算法功能。

"""



import numpy as np

import random

from collections import deque





class DQN:

    """简化版 DQN 智能体"""



    def __init__(self, state_dim, action_num, hidden_dim=64, lr=0.001, gamma=0.99,

                 epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01,

                 batch_size=32, replay_size=10000):

        self.state_dim = state_dim

        self.action_num = action_num

        self.gamma = gamma

        self.epsilon = epsilon

        self.epsilon_decay = epsilon_decay

        self.epsilon_min = epsilon_min

        self.batch_size = batch_size



        # 经验回放缓冲区

        self.replay_buffer = deque(maxlen=replay_size)



        # 简单策略网络（用 numpy 实现）

        self.hidden_dim = hidden_dim

        # Xavier 初始化

        scale_w1 = np.sqrt(2.0 / (state_dim + hidden_dim))

        scale_w2 = np.sqrt(2.0 / (hidden_dim + action_num))

        self.w1 = np.random.randn(state_dim, hidden_dim) * scale_w1

        self.b1 = np.zeros(hidden_dim)

        self.w2 = np.random.randn(hidden_dim, action_num) * scale_w2

        self.b2 = np.zeros(action_num)



        # 目标网络（延迟更新）

        self.target_w1 = self.w1.copy()

        self.target_b1 = self.b1.copy()

        self.target_w2 = self.w2.copy()

        self.target_b2 = self.b2.copy()



        self.lr = lr

        self.update_freq = 100  # 每多少步更新一次目标网络

        self.step_counter = 0



    def relu(self, x):

        """ReLU 激活函数"""

        return np.maximum(0, x)



    def forward(self, state, target_net=False):

        """前向传播"""

        if target_net:

            w1, b1, w2, b2 = self.target_w1, self.target_b1, self.target_w2, self.target_b2

        else:

            w1, b1, w2, b2 = self.w1, self.b1, self.w2, self.b2



        # 隐藏层

        hidden = self.relu(np.dot(state, w1) + b1)

        # 输出层（Q 值）

        q_values = np.dot(hidden, w2) + b2

        return q_values



    def choose_action(self, state):

        """ε-贪心策略选择动作"""

        if random.random() < self.epsilon:

            return random.randint(0, self.action_num - 1)

        else:

            state = np.array(state, dtype=np.float32).reshape(1, -1)

            q_values = self.forward(state)

            return int(np.argmax(q_values))



    def store(self, state, action, reward, next_state, done):

        """存储转移经验到回放缓冲区"""

        self.replay_buffer.append((state, action, reward, next_state, done))



    def update_target(self):

        """复制权重到目标网络"""

        self.target_w1 = self.w1.copy()

        self.target_b1 = self.b1.copy()

        self.target_w2 = self.w2.copy()

        self.target_b2 = self.b2.copy()



    def update(self):

        """从回放缓冲区采样并更新网络"""

        if len(self.replay_buffer) < self.batch_size:

            return



        # 随机采样一批经验

        batch = random.sample(self.replay_buffer, self.batch_size)

        states = np.array([e[0] for e in batch], dtype=np.float32)

        actions = np.array([e[1] for e in batch])

        rewards = np.array([e[2] for e in batch])

        next_states = np.array([e[3] for e in batch], dtype=np.float32)

        dones = np.array([e[4] for e in batch], dtype=np.float32)



        # 计算当前 Q 值

        current_q = self.forward(states)  # (batch, action_num)

        current_q = np.sum(current_q * np.eye(self.action_num)[actions], axis=1)  # (batch,)



        # 计算目标 Q 值（使用目标网络）

        next_q = np.max(self.forward(next_states, target_net=True), axis=1)  # (batch,)

        target_q = rewards + (1 - dones) * self.gamma * next_q



        # 计算损失梯度（均方误差）

        delta = current_q - target_q

        # 简化的梯度更新：直接对网络参数求导

        # 反向传播（单层网络简化版）

        hidden = self.relu(np.dot(states, self.w1) + self.b1)

        dq_dw2 = np.dot(hidden.T, delta.reshape(-1, 1) * np.eye(self.action_num)[actions]) / self.batch_size

        dq_dw1 = np.dot(states.T, (np.dot(delta.reshape(-1, 1), self.w2[actions].reshape(1, -1)) *

                                   (hidden > 0).astype(float))) / self.batch_size



        # 更新权重

        self.w2 -= self.lr * dq_dw2

        self.w1 -= self.lr * dq_dw1



        # 定期更新目标网络

        self.step_counter += 1

        if self.step_counter % self.update_freq == 0:

            self.update_target()



        # 衰减探索率

        if self.epsilon > self.epsilon_min:

            self.epsilon *= self.epsilon_decay





def simple_env():

    """简单连续状态环境用于测试"""

    class SimpleEnv:

        def __init__(self):

            self.state_dim = 4



        def reset(self):

            return np.random.randn(self.state_dim).tolist()



        def step(self, action):

            next_state = np.random.randn(self.state_dim).tolist()

            reward = random.random() - 0.5

            done = random.random() < 0.1

            return next_state, reward, done



    return SimpleEnv()





if __name__ == "__main__":

    # 测试 DQN

    env = simple_env()

    agent = DQN(state_dim=4, action_num=2)

    episodes = 50

    for ep in range(episodes):

        state = env.reset()

        total_reward = 0

        done = False

        while not done:

            action = agent.choose_action(state)

            next_state, reward, done = env.step(action)

            agent.store(state, action, reward, next_state, done)

            agent.update()

            state = next_state

            total_reward += reward

        if ep % 10 == 0:

            print(f"Episode {ep}, reward: {total_reward:.2f}, epsilon: {agent.epsilon:.3f}")

    print("DQN 训练完成")

