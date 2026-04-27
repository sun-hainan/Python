# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / qmix_algorithm



本文件实现 qmix_algorithm 相关的算法功能。

"""



import numpy as np

import random

from collections import deque





class QMIXAgent:

    """单智能体Q网络（本地策略网络）"""

    

    def __init__(self, obs_dim, n_actions, hidden_dim=64, learning_rate=0.001):

        # obs_dim: 观测维度

        # n_actions: 动作空间大小

        # hidden_dim: 隐藏层维度

        # learning_rate: 学习率

        self.obs_dim = obs_dim

        self.n_actions = n_actions

        self.hidden_dim = hidden_dim

        self.lr = learning_rate

        

        # 简化版：使用随机权重模拟Q网络

        # 实际应用中用PyTorch/TensorFlow实现

        self.w1 = np.random.randn(obs_dim, hidden_dim) * 0.1

        self.b1 = np.zeros(hidden_dim)

        self.w2 = np.random.randn(hidden_dim, n_actions) * 0.1

        self.b2 = np.zeros(n_actions)

        

        # 目标网络

        self.target_w1 = self.w1.copy()

        self.target_w2 = self.w2.copy()

        self.target_b1 = self.b1.copy()

        self.target_b2 = self.b2.copy()

    

    def forward(self, obs):

        """前向传播，计算Q值"""

        # obs: 当前观测

        hidden = np.tanh(np.dot(obs, self.w1) + self.b1)

        q_values = np.dot(hidden, self.w2) + self.b2

        return q_values

    

    def get_action(self, obs, epsilon=0.1):

        """epsilon-贪婪策略选择动作"""

        if random.random() < epsilon:

            return random.randint(0, self.n_actions - 1)

        q_values = self.forward(obs)

        return np.argmax(q_values)

    

    def update(self, obs, action, td_error):

        """单步梯度更新"""

        # 简化版梯度下降

        hidden = np.tanh(np.dot(obs, self.w1) + self.b1)

        q_values = np.dot(hidden, self.w2) + self.b2

        

        grad = np.zeros_like(q_values)

        grad[action] = td_error

        

        # 链式法则更新

        self.w2 -= self.lr * np.outer(hidden, grad)

        self.b2 -= self.lr * grad

        

        hidden_grad = np.dot(self.w2, grad) * (1 - hidden**2)

        self.w1 -= self.lr * np.outer(obs, hidden_grad)

        self.b1 -= self.lr * hidden_grad

    

    def update_target(self, tau=0.005):

        """软更新目标网络"""

        # tau: 软更新系数

        self.target_w1 = (1 - tau) * self.target_w1 + tau * self.w1

        self.target_w2 = (1 - tau) * self.target_w2 + tau * self.w2

        self.target_b1 = (1 - tau) * self.target_b1 + tau * self.b1

        self.target_b2 = (1 - tau) * self.target_b2 + tau * self.b2





class MixerNetwork:

    """混合器网络：联合分解全局Q值"""

    

    def __init__(self, n_agents, state_dim, hidden_dim=32):

        # n_agents: 智能体数量

        # state_dim: 全局状态维度

        # hidden_dim: 隐藏层维度

        self.n_agents = n_agents

        self.state_dim = state_dim

        self.hidden_dim = hidden_dim

        

        # 超参数网络(hyper-network)权重

        self.w1 = np.random.randn(state_dim, hidden_dim * n_agents) * 0.1

        self.b1 = np.zeros(hidden_dim * n_agents)

        self.w2 = np.random.randn(hidden_dim, 1) * 0.1

        self.b2 = np.zeros(1)

    

    def forward(self, q_local, state):

        """

        混合器前向传播

        q_local: 各智能体本地Q值 [n_agents, n_actions]选取max后

        state: 全局状态

        """

        # 将本地Q值压缩为标量（每个智能体取最大Q值）

        q_max = np.max(q_local, axis=1, keepdims=True)  # [n_agents, 1]

        q_agent = q_max.flatten()  # [n_agents]

        

        # 超参数网络：状态决定权重

        hyper_hidden = np.tanh(np.dot(state, self.w1) + self.b1)

        hyper_w = hyper_hidden[:, :self.hidden_dim * self.n_agents].reshape(

            self.n_agents, self.hidden_dim)

        hyper_b = hyper_hidden[:, self.hidden_dim * self.n_agents:].reshape(

            self.n_agents, 1)

        

        # 逐智能体计算混合Q值

        q_mixed = np.sum(np.tanh(q_agent.reshape(-1, 1) * hyper_w) + hyper_b, axis=0)

        q_total = np.dot(np.tanh(q_mixed), self.w2) + self.b2

        return q_total.flatten()[0]





class QMIX:

    """QMIX主算法类"""

    

    def __init__(self, n_agents, obs_dim, n_actions, state_dim):

        # n_agents: 智能体数量

        # obs_dim: 每个智能体的观测维度

        # n_actions: 动作空间大小

        # state_dim: 全局状态维度

        self.n_agents = n_agents

        self.obs_dim = obs_dim

        self.n_actions = n_actions

        self.state_dim = state_dim

        

        # 创建各智能体的Q网络

        self.agents = [

            QMIXAgent(obs_dim, n_actions) 

            for _ in range(n_agents)

        ]

        

        # 创建混合器网络

        self.mixer = MixerNetwork(n_agents, state_dim)

        

        # 经验回放缓冲区

        self.replay_buffer = deque(maxlen=10000)

        

        # 训练参数

        self.gamma = 0.99  # 折扣因子

        self.epsilon = 1.0  # 探索率

    

    def select_actions(self, obs_list):

        """为所有智能体选择动作"""

        actions = []

        for i, obs in enumerate(obs_list):

            action = self.agents[i].get_action(obs, self.epsilon)

            actions.append(action)

        return actions

    

    def store_transition(self, obs_list, actions, reward, next_obs_list, done):

        """存储转移样本到回放缓冲区"""

        self.replay_buffer.append({

            'obs_list': obs_list,

            'actions': actions,

            'reward': reward,

            'next_obs_list': next_obs_list,

            'done': done

        })

    

    def train(self, batch_size=32):

        """从回放缓冲区采样训练"""

        if len(self.replay_buffer) < batch_size:

            return

        

        # 采样批次

        batch = random.sample(self.replay_buffer, batch_size)

        

        total_loss = 0

        for sample in batch:

            # 提取数据

            obs_list = sample['obs_list']

            actions = sample['actions']

            reward = sample['reward']

            next_obs_list = sample['next_obs_list']

            done = sample['done']

            

            # 构建全局状态（简化处理）

            state = np.mean(obs_list, axis=0)

            next_state = np.mean(next_obs_list, axis=0)

            

            # 计算各智能体的本地Q值

            q_local = np.array([

                self.agents[i].forward(obs_list[i]) 

                for i in range(self.n_agents)

            ])

            

            # 计算目标Q值

            q_next_local = np.array([

                self.agents[i].forward(next_obs_list[i]) 

                for i in range(self.n_agents)

            ])

            

            # 混合器计算全局Q值

            q_total = self.mixer.forward(q_local, state)

            q_next_total = self.mixer.forward(q_next_local, next_state)

            

            # TD目标

            if done:

                td_target = reward

            else:

                td_target = reward + self.gamma * q_next_total

            

            # TD误差

            td_error = td_target - q_total

            

            # 更新混合器（简化版）

            self.mixer.w2 += 0.01 * td_error * self.mixer.w2.flatten()

            

            # 各智能体更新

            for i in range(self.n_agents):

                action = actions[i]

                self.agents[i].update(obs_list[i], action, td_error / self.n_agents)

            

            total_loss += td_error ** 2

        

        # 软更新目标网络

        for agent in self.agents:

            agent.update_target()

        

        return total_loss / batch_size

    

    def decay_epsilon(self, epsilon_min=0.05, epsilon_decay=0.995):

        """探索率衰减"""

        self.epsilon = max(epsilon_min, self.epsilon * epsilon_decay)





if __name__ == "__main__":

    # 测试QMIX算法

    print("=" * 50)

    print("QMIX多智能体Q值分解算法测试")

    print("=" * 50)

    

    # 参数设置

    n_agents = 3  # 3个智能体

    obs_dim = 10  # 观测维度10

    n_actions = 5  # 动作空间大小5

    state_dim = 15  # 全局状态维度15

    

    # 初始化QMIX

    qmix = QMIX(n_agents, obs_dim, n_actions, state_dim)

    

    # 模拟环境交互

    print("\n模拟环境交互...")

    for episode in range(5):

        # 随机初始化观测

        obs_list = [np.random.randn(obs_dim) for _ in range(n_agents)]

        next_obs_list = [np.random.randn(obs_dim) for _ in range(n_agents)]

        

        # 选择动作

        actions = qmix.select_actions(obs_list)

        

        # 计算奖励（简化的协同奖励）

        reward = np.sum(actions) / n_actions

        

        # 存储转移

        done = (episode == 4)  # 最后一轮为done

        qmix.store_transition(obs_list, actions, reward, next_obs_list, done)

        

        print(f"  Episode {episode+1}: actions={actions}, reward={reward:.3f}")

    

    # 训练

    print("\n开始训练...")

    for step in range(10):

        loss = qmix.train(batch_size=4)

        qmix.decay_epsilon()

        print(f"  Step {step+1}: loss={loss:.4f}, epsilon={qmix.epsilon:.4f}")

    

    print("\n✓ QMIX算法测试完成")

    print(f"  智能体数量: {n_agents}")

    print(f"  经验回放缓冲区: {len(qmix.replay_buffer)} 条样本")

