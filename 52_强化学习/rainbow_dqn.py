# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / rainbow_dqn



本文件实现 rainbow_dqn 相关的算法功能。

"""



import numpy as np

import random

from collections import deque





class NStepBuffer:

    """N 步返回缓冲区"""



    def __init__(self, n_steps=3, gamma=0.99):

        """

        初始化 N 步缓冲区



        参数:

            n_steps: N 步数

            gamma: 折扣因子

        """

        self.n_steps = n_steps

        self.gamma = gamma

        self.buffer = deque(maxlen=n_steps)



    def push(self, state, action, reward, done):

        """添加样本"""

        self.buffer.append((state, action, reward, done))



    def get_n_step(self):

        """获取 N 步回报和最终状态"""

        if len(self.buffer) < self.n_steps:

            return None



        # 获取最早的样本

        first = self.buffer[0]

        # 从 buffer 中累积计算

        R = 0.0

        for i in range(self.n_steps):

            _, _, r, done = self.buffer[i]

            R += (self.gamma ** i) * r

            if done:

                break



        state, action, _, _ = first

        next_state = self.buffer[-1][0] if len(self.buffer) > 0 else state



        return state, action, R, next_state, self.buffer[-1][3]





class RainbowDQN:

    """Rainbow DQN 算法（核心组件集成版）"""



    def __init__(self, state_dim, action_dim, hidden_dim=128,

                 lr=0.001, gamma=0.99, n_steps=3,

                 sigma_init=0.5, alpha=0.6, beta=0.4,

                 memory_size=10000, batch_size=64, target_update_freq=200):

        """

        初始化 Rainbow DQN



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

            lr: 学习率

            gamma: 折扣因子

            n_steps: N 步回报

            sigma_init: NoisyNet 初始化标准差

            alpha: PER 优先级指数

            beta: PER 重要性采样指数

            memory_size: 经验回放容量

            batch_size: 批次大小

            target_update_freq: 目标网络更新频率

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.gamma = gamma

        self.n_steps = n_steps

        self.batch_size = batch_size

        self.target_update_freq = target_update_freq

        self.train_step = 0

        self.alpha = alpha

        self.beta = beta

        self.beta_increment = 0.001

        self.epsilon_init = 1e-6



        # N 步缓冲区

        self.nstep_buffer = NStepBuffer(n_steps, gamma)



        # 优先经验回放

        self.memory = []

        self.priorities = deque(maxlen=memory_size)

        self.max_priority = 1.0

        self.memory_size = memory_size



        # 网络（结合 NoisyNet 和 Dueling）

        self.q_network = self._build_network(sigma_init)

        self.target_network = self._build_network(sigma_init)

        self._sync_target()



    def _build_network(self, sigma_init):

        """构建 Dueling + NoisyNet 网络"""

        np.random.seed(42)

        init_w = lambda n, m: np.random.randn(n, m) * np.sqrt(2.0 / n)



        def noisy_params(shape, sigma):

            mu = init_w(shape[0], shape[1]) if len(shape) == 2 else np.zeros(shape)

            sigma_mat = np.ones_like(mu) * sigma

            return mu, sigma_mat



        mu_w1, sig_w1 = noisy_params((self.state_dim, 128), sigma_init)

        mu_b1, sig_b1 = noisy_params(128, sigma_init)

        mu_w2, sig_w2 = noisy_params((128, 128), sigma_init)

        mu_b2, sig_b2 = noisy_params(128, sigma_init)



        # Dueling 分支

        mu_vw, sig_vw = noisy_params((128, 64), sigma_init)

        mu_vb, sig_vb = noisy_params(64, sigma_init)

        mu_vw2, sig_vw2 = noisy_params((64, 1), sigma_init)

        mu_vb2, sig_vb2 = noisy_params(1, sigma_init)



        mu_aw, sig_aw = noisy_params((128, 64), sigma_init)

        mu_ab, sig_ab = noisy_params(64, sigma_init)

        mu_aw2, sig_aw2 = noisy_params((64, self.action_dim), sigma_init)

        mu_ab2, sig_ab2 = noisy_params(self.action_dim, sigma_init)



        return {

            'mu_w1': mu_w1, 'sig_w1': sig_w1,

            'mu_b1': mu_b1, 'sig_b1': sig_b1,

            'mu_w2': mu_w2, 'sig_w2': sig_w2,

            'mu_b2': mu_b2, 'sig_b2': sig_b2,

            'mu_vw': mu_vw, 'sig_vw': sig_vw,

            'mu_vb': mu_vb, 'sig_vb': sig_vb,

            'mu_vw2': mu_vw2, 'sig_vw2': sig_vw2,

            'mu_vb2': mu_vb2, 'sig_vb2': sig_vb2,

            'mu_aw': mu_aw, 'sig_aw': sig_aw,

            'mu_ab': mu_ab, 'sig_ab': sig_ab,

            'mu_aw2': mu_aw2, 'sig_aw2': sig_aw2,

            'mu_ab2': mu_ab2, 'sig_ab2': sig_ab2

        }



    def _get_noisy_weights(self, network):

        """生成带噪声的权重"""

        eps = lambda shape: np.random.randn(*shape)

        w = {}

        for k, v in network.items():

            if k.startswith('sig_'):

                base_k = k.replace('sig_', 'mu_')

                w[k.replace('sig_', '')] = network[base_k] + network[k] * eps(v.shape)

            elif k.startswith('mu_'):

                w[k] = v

        return w



    def _forward_dueling(self, state, weights):

        """Dueling 网络前向"""

        h = np.maximum(0, np.dot(state, weights['w1']) + weights['b1'])

        h = np.maximum(0, np.dot(h, weights['w2']) + weights['b2'])



        v = np.maximum(0, np.dot(h, weights['vw']) + weights['vb'])

        v = np.dot(v, weights['vw2']) + weights['vb2']



        a = np.maximum(0, np.dot(h, weights['aw']) + weights['ab'])

        a = np.dot(a, weights['aw2']) + weights['ab2']



        q = v + a - np.mean(a)

        return q



    def _forward(self, state, network):

        """完整前向"""

        w = self._get_noisy_weights(network)

        return self._forward_dueling(state, w)



    def _sync_target(self):

        """同步目标网络（只复制 mu 参数）"""

        for k in self.target_network:

            if k.startswith('mu_'):

                self.target_network[k] = self.q_network[k].copy()



    def reset_noise(self):

        """重置噪声（在 episode 开始时调用）"""

        # NoisyNet 不需要显式重置，每次前向自动生成新噪声

        pass



    def choose_action(self, state):

        """选择动作（NoisyNet 驱动，无需 epsilon）"""

        state = np.array(state).reshape(1, -1)

        q_values = self._forward(state, self.q_network)

        return np.argmax(q_values.squeeze())



    def store(self, state, action, reward, next_state, done):

        """存储样本到 N 步缓冲区和 PER"""

        self.nstep_buffer.push(state, action, reward, done)



        if len(self.nstep_buffer.buffer) >= self.n_steps:

            nstep_sample = self.nstep_buffer.get_n_step()

            if nstep_sample:

                ns, na, nr, nns, nd = nstep_sample

                self.memory.append((ns, na, nr, nns, nd))

                self.priorities.append(self.max_priority)

                if len(self.memory) > self.memory_size:

                    self.memory.pop(0)

                    self.priorities.popleft()



    def _sample(self, batch_size):

        """PER 采样"""

        if len(self.memory) < batch_size:

            return None

        priorities = np.array(self.priorities)

        probs = priorities / np.sum(priorities)

        indices = np.random.choice(len(self.memory), batch_size, p=probs)

        weights = (len(self.memory) * probs[indices]) ** (-self.beta)

        weights = weights / np.max(weights)

        self.beta = min(1.0, self.beta + self.beta_increment)

        return indices, weights



    def train(self):

        """训练"""

        result = self._sample(self.batch_size)

        if result is None:

            return 0.0

        indices, weights = result



        batch = [self.memory[i] for i in indices]

        states = np.array([t[0] for t in batch])

        actions = np.array([t[1] for t in batch])

        rewards = np.array([t[2] for t in batch])

        next_states = np.array([t[3] for t in batch])

        dones = np.array([t[4] for t in batch])



        # Double DQN：在线网络选动作，目标网络评估

        current_q = self._forward(states, self.q_network)

        current_q = np.sum(current_q * np.eye(self.action_dim)[actions], axis=1)



        next_q_target = self._forward(next_states, self.target_network)

        next_q_online = self._forward(next_states, self.q_network)

        best_actions = np.argmax(next_q_online, axis=1)

        next_q = np.sum(next_q_target * np.eye(self.action_dim)[best_actions], axis=1)



        td_target = rewards + (self.gamma ** self.n_steps) * next_q * (1 - dones)

        td_errors = (current_q - td_target) * weights

        loss = np.mean(td_errors ** 2)



        # 更新优先级

        for idx, err in zip(indices, np.abs(current_q - td_target)):

            p = (err + 1e-6) ** self.alpha

            self.priorities[idx] = p

            if p > self.max_priority:

                self.max_priority = p



        self.train_step += 1

        if self.train_step % self.target_update_freq == 0:

            self._sync_target()



        return loss





if __name__ == "__main__":

    state_dim = 4

    action_dim = 2

    agent = RainbowDQN(state_dim, action_dim, n_steps=3, memory_size=5000)



    for ep in range(5):

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

              f"memory={len(agent.memory)}, beta={agent.beta:.4f}")



    print("\nRainbow DQN 测试完成!")

