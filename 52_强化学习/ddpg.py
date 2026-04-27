# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / ddpg



本文件实现 ddpg 相关的算法功能。

"""



import numpy as np

import random

from collections import deque





class DDPG:

    """DDPG 智能体（深度确定性策略梯度）"""



    def __init__(self, state_dim, action_dim, hidden_dim=64, actor_lr=0.001,

                 critic_lr=0.001, gamma=0.99, tau=0.005, replay_size=10000, batch_size=64):

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.gamma = gamma

        self.tau = tau  # 软更新系数

        self.batch_size = batch_size

        self.replay_buffer = deque(maxlen=replay_size)



        # 初始化网络

        scale_actor = np.sqrt(2.0 / (state_dim + hidden_dim))

        self.actor_w1 = np.random.randn(state_dim, hidden_dim) * scale_actor

        self.actor_b1 = np.zeros(hidden_dim)

        scale_actor_out = np.sqrt(2.0 / (hidden_dim + action_dim))

        self.actor_w2 = np.random.randn(hidden_dim, action_dim) * scale_actor_out

        self.actor_b2 = np.zeros(action_dim)



        scale_critic_s = np.sqrt(2.0 / (state_dim + hidden_dim))

        self.critic_w1_s = np.random.randn(state_dim, hidden_dim) * scale_critic_s

        self.critic_b1 = np.zeros(hidden_dim)

        scale_critic_a = np.sqrt(2.0 / (action_dim + hidden_dim))

        self.critic_w1_a = np.random.randn(action_dim, hidden_dim) * scale_critic_a

        self.critic_b1_a = np.zeros(hidden_dim)

        scale_critic_out = np.sqrt(2.0 / (hidden_dim + 1))

        self.critic_w2 = np.random.randn(hidden_dim, 1) * scale_critic_out

        self.critic_b2 = np.zeros(1)



        # 目标网络（初始化为相同权重）

        self.target_actor_w1 = self.actor_w1.copy()

        self.target_actor_b1 = self.actor_b1.copy()

        self.target_actor_w2 = self.actor_w2.copy()

        self.target_actor_b2 = self.actor_b2.copy()

        self.target_critic_w1_s = self.critic_w1_s.copy()

        self.target_critic_w1_a = self.critic_w1_a.copy()

        self.target_critic_b1 = self.critic_b1.copy()

        self.target_critic_b1_a = self.critic_b1_a.copy()

        self.target_critic_w2 = self.critic_w2.copy()

        self.target_critic_b2 = self.critic_b2.copy()



        self.actor_lr = actor_lr

        self.critic_lr = critic_lr

        self.ou_noise_theta = 0.15  # Ornstein-Uhlenbeck 噪声参数

        self.ou_noise_sigma = 0.2

        self.ou_noise_state = np.zeros(action_dim)



    def relu(self, x):

        return np.maximum(0, x)



    def tanh(self, x):

        return np.tanh(x)



    def forward_actor(self, state, target=False):

        """Actor 前向：输出确定性动作"""

        if target:

            w1, b1, w2, b2 = self.target_actor_w1, self.target_actor_b1, self.target_actor_w2, self.target_actor_b2

        else:

            w1, b1, w2, b2 = self.actor_w1, self.actor_b1, self.actor_w2, self.actor_b2

        hidden = self.tanh(np.dot(state, w1) + b1)

        action = np.tanh(np.dot(hidden, w2) + b2)  # 输出 [-1, 1] 范围的动作

        return action



    def forward_critic(self, state, action, target=False):

        """Critic 前向：输出 Q 值"""

        if target:

            w1s, b1, w1a, b1a, w2, b2 = (self.target_critic_w1_s, self.target_critic_b1,

                                         self.target_critic_w1_a, self.target_critic_b1_a,

                                         self.target_critic_w2, self.target_critic_b2)

        else:

            w1s, b1, w1a, b1a, w2, b2 = (self.critic_w1_s, self.critic_b1,

                                         self.critic_w1_a, self.critic_b1_a,

                                         self.critic_w2, self.critic_b2)

        hidden = self.relu(np.dot(state, w1s) + np.dot(action, w1a) + b1 + b1a)

        q_value = float(np.dot(hidden, w2) + b2)

        return q_value



    def ou_noise(self):

        """Ornstein-Uhlenbeck 探索噪声"""

        dx = self.ou_noise_theta * (-self.ou_noise_state) + \

             self.ou_noise_sigma * np.random.randn(self.action_dim)

        self.ou_noise_state += dx

        return self.ou_noise_state



    def choose_action(self, state, add_noise=True):

        """选择动作（确定性策略 + 探索噪声）"""

        state = np.array(state, dtype=np.float32).reshape(1, -1)

        action = self.forward_actor(state).flatten()

        if add_noise:

            action += 0.1 * self.ou_noise()

        return np.clip(action, -1, 1)



    def store(self, state, action, reward, next_state, done):

        """存储经验"""

        self.replay_buffer.append((state, action, reward, next_state, done))



    def soft_update_target(self):

        """软更新目标网络: θ_target = τ * θ_online + (1-τ) * θ_target"""

        for target, online in [

            (self.target_actor_w1, self.actor_w1),

            (self.target_actor_b1, self.actor_b1),

            (self.target_actor_w2, self.actor_w2),

            (self.target_actor_b2, self.actor_b2),

            (self.target_critic_w1_s, self.critic_w1_s),

            (self.target_critic_w1_a, self.critic_w1_a),

            (self.target_critic_b1, self.critic_b1),

            (self.target_critic_b1_a, self.critic_b1_a),

            (self.target_critic_w2, self.critic_w2),

            (self.target_critic_b2, self.critic_b2),

        ]:

            target[:] = self.tau * online + (1 - self.tau) * target



    def update(self):

        """从回放缓冲区采样并更新网络"""

        if len(self.replay_buffer) < self.batch_size:

            return



        batch = random.sample(self.replay_buffer, self.batch_size)

        states = np.array([e[0] for e in batch], dtype=np.float32)

        actions = np.array([e[1] for e in batch], dtype=np.float32)

        rewards = np.array([e[2] for e in batch])

        next_states = np.array([e[3] for e in batch], dtype=np.float32)

        dones = np.array([e[4] for e in batch], dtype=np.float32)



        # Critic 更新

        next_actions = self.forward_actor(next_states, target=True)

        next_q = np.array([self.forward_critic(ns, na, target=True)

                           for ns, na in zip(next_states, next_actions)])

        target_q = rewards + (1 - dones) * self.gamma * next_q



        current_qs = np.array([self.forward_critic(s, a) for s, a in zip(states, actions)])

        critic_loss = np.mean((current_qs - target_q) ** 2)



        # 简化的 Critic 梯度更新

        for i in range(self.batch_size):

            s, a, r, ns, d = states[i], actions[i], rewards[i], next_states[i], dones[i]

            na = self.forward_actor(ns.reshape(1, -1), target=True).flatten()

            tq = r + (1 - d) * self.gamma * self.forward_critic(ns.reshape(1, -1), na, target=True)

            cq = self.forward_critic(s.reshape(1, -1), a.reshape(1, -1))

            err = cq - tq

            # 简化的在线 critic 更新（仅用随机梯度下降一步）

            hidden_c = self.relu(np.dot(s, self.critic_w1_s) + np.dot(a, self.critic_w1_a) +

                                 self.critic_b1 + self.critic_b1_a)

            dw2 = err * hidden_c

            self.critic_w2 -= self.critic_lr * dw2.reshape(self.critic_w2.shape)

            self.critic_b2 -= self.critic_lr * err



        # Actor 更新（确定性策略梯度：∇J ≈ ∇Q(s,μ(s)) = E[∇Q * ∇μ]）

        # 简化为：对每个样本使动作向更高 Q 方向移动

        for i in range(self.batch_size):

            s = states[i].reshape(1, -1)

            a_pred = self.forward_actor(s).flatten()

            q_approx = self.forward_critic(s, a_pred.reshape(1, -1))

            # 梯度上升：∂Q/∂a * ∂a/∂θ

            hidden = self.tanh(np.dot(s, self.actor_w1) + self.actor_b1)

            d_action = self.forward_critic(s, a_pred.reshape(1, -1) + 1e-3) - q_approx

            d_hidden = d_action * self.actor_w2.flatten() * (1 - hidden ** 2)

            dw1 = 1e-4 * np.outer(s.flatten(), d_hidden)

            self.actor_w1 += self.actor_lr * dw1

            self.actor_b1 += self.actor_lr * d_hidden



        # 软更新目标网络

        self.soft_update_target()





def simple_continuous_env():

    """测试用连续动作环境"""

    class ContinuousEnv:

        def __init__(self):

            self.state_dim = 4



        def reset(self):

            return np.random.randn(self.state_dim).tolist()



        def step(self, action):

            next_state = np.random.randn(self.state_dim).tolist()

            reward = -np.sum(action ** 2) * 0.1 + random.random()

            done = random.random() < 0.05

            return next_state, reward, done



    return ContinuousEnv()





if __name__ == "__main__":

    # 测试 DDPG

    env = simple_continuous_env()

    agent = DDPG(state_dim=4, action_dim=2, actor_lr=0.0005, critic_lr=0.001)

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

            print(f"Episode {ep}, reward: {total_reward:.2f}")

    print("DDPG 训练完成")

