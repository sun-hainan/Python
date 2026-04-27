# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / noisy_net



本文件实现 noisy_net 相关的算法功能。

"""



import numpy as np

import random





class NoisyLinear:

    """

    噪声线性层



    在标准线性变换 y = Wx + b 的基础上，

    将权重和偏置参数化为: W = μ_w + σ_w ⊙ ε_w

    """



    def __init__(self, in_dim, out_dim, sigma_init=0.5):

        """

        初始化噪声线性层



        参数:

            in_dim: 输入维度

            out_dim: 输出维度

            sigma_init: 噪声标准差的初始值

        """

        self.in_dim = in_dim  # 输入维度

        self.out_dim = out_dim  # 输出维度

        self.sigma_init = sigma_init_init = sigma_init  # 初始标准差



        # 可学习参数：均值 μ 和 标准差 σ

        self.mu_w = np.random.randn(out_dim, in_dim) * np.sqrt(2.0 / in_dim)

        self.sigma_w = np.ones((out_dim, in_dim)) * sigma_init

        self.mu_b = np.zeros(out_dim)

        self.sigma_b = np.ones(out_dim) * sigma_init



        # 当前有效的权重（均值 + 噪声）

        self.weight = None

        self.bias = None



        # 生成初始噪声

        self._reset_noise()



    def _reset_noise(self):

        """重置噪声（每个 episode 或 step 调用）"""

        # 生成独立的高斯噪声

        epsilon_w = np.random.randn(self.out_dim, self.in_dim)

        epsilon_b = np.random.randn(self.out_dim)

        # 当前权重 = 均值 + 标准差 * 噪声

        self.weight = self.mu_w + self.sigma_w * epsilon_w

        self.bias = self.mu_b + self.sigma_b * epsilon_b

        return epsilon_w, epsilon_b



    def forward(self, x):

        """

        前向传播



        参数:

            x: 输入张量 (batch, in_dim)

        返回:

            y: 输出张量 (batch, out_dim)

        """

        return np.dot(x, self.weight.T) + self.bias



    def update_parameters(self, lr):

        """

        更新噪声参数（简化版，实际需要反向传播）



        参数:

            lr: 学习率

        """

        # 实际实现中，噪声参数应通过梯度更新

        # 这里简化为轻微的均值的更新

        pass



    def get_regularization_loss(self):

        """获取噪声参数的 L2 正则化损失"""

        # 鼓励 sigma 变小，减少噪声

        return np.sum(self.sigma_w ** 2) + np.sum(self.sigma_b ** 2)





class NoisyDQN:

    """基于 NoisyNet 的 DQN 算法"""



    def __init__(self, state_dim, action_dim, hidden_dim=128,

                 lr=0.001, gamma=0.99, sigma_init=0.5,

                 memory_size=10000, batch_size=64, target_update_freq=200):

        """

        初始化 NoisyNet DQN



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

            lr: 学习率

            gamma: 折扣因子

            sigma_init: 噪声标准差初始值

            memory_size: 经验回放容量

            batch_size: 批次大小

            target_update_freq: 目标网络更新频率

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.gamma = gamma

        self.batch_size = batch_size

        self.target_update_freq = target_update_freq

        self.train_step = 0



        self.memory = deque(maxlen=memory_size) if 'deque' in dir() else []

        self.memory_buffer = []



        # NoisyNet 层

        self.noisy1 = NoisyLinear(state_dim, hidden_dim, sigma_init)

        self.noisy2 = NoisyLinear(hidden_dim, hidden_dim, sigma_init)

        self.noisy3 = NoisyLinear(hidden_dim, action_dim, sigma_init)



        # 目标网络（Noisy）

        self.target_noisy1 = NoisyLinear(state_dim, hidden_dim, sigma_init)

        self.target_noisy2 = NoisyLinear(hidden_dim, hidden_dim, sigma_init)

        self.target_noisy3 = NoisyLinear(hidden_dim, action_dim, sigma_init)



        self._sync_target()



    def _forward(self, state, noisy_layers):

        """前向传播"""

        h = np.maximum(0, noisy_layers[0].forward(state))

        h = np.maximum(0, noisy_layers[1].forward(h))

        q = noisy_layers[2].forward(h)

        return q



    def _sync_target(self):

        """同步目标网络（复制均值参数）"""

        self.target_noisy1.mu_w = self.noisy1.mu_w.copy()

        self.target_noisy1.sigma_w = self.noisy1.sigma_w.copy()

        self.target_noisy1.mu_b = self.noisy1.mu_b.copy()

        self.target_noisy1.sigma_b = self.noisy1.sigma_b.copy()



        self.target_noisy2.mu_w = self.noisy2.mu_w.copy()

        self.target_noisy2.sigma_w = self.noisy2.sigma_w.copy()

        self.target_noisy2.mu_b = self.noisy2.mu_b.copy()

        self.target_noisy2.sigma_b = self.noisy2.sigma_b.copy()



        self.target_noisy3.mu_w = self.noisy3.mu_w.copy()

        self.target_noisy3.sigma_w = self.noisy3.sigma_w.copy()

        self.target_noisy3.mu_b = self.noisy3.mu_b.copy()

        self.target_noisy3.sigma_b = self.noisy3.sigma_b.copy()



    def reset_noise(self):

        """重置所有噪声层（每个 episode 开始时调用）"""

        self.noisy1._reset_noise()

        self.noisy2._reset_noise()

        self.noisy3._reset_noise()

        self.target_noisy1._reset_noise()

        self.target_noisy2._reset_noise()

        self.target_noisy3._reset_noise()



    def choose_action(self, state):

        """选择动作（无需 epsilon-greedy，纯贪心）"""

        state = np.array(state).reshape(1, -1)

        q_values = self._forward(state, [self.noisy1, self.noisy2, self.noisy3])

        return np.argmax(q_values)



    def store(self, state, action, reward, next_state, done):

        """存储样本"""

        self.memory_buffer.append((state, action, reward, next_state, done))

        if len(self.memory_buffer) > 10000:

            self.memory_buffer.pop(0)



    def train(self):

        """训练网络"""

        if len(self.memory_buffer) < self.batch_size:

            return 0.0



        batch = random.sample(self.memory_buffer, self.batch_size)

        states = np.array([t[0] for t in batch])

        actions = np.array([t[1] for t in batch])

        rewards = np.array([t[2] for t in batch])

        next_states = np.array([t[3] for t in batch])

        dones = np.array([t[4] for t in batch])



        # 当前 Q 值

        current_q = self._forward(states, [self.noisy1, self.noisy2, self.noisy3])

        current_q = np.sum(current_q * np.eye(self.action_dim)[actions], axis=1)



        # 目标 Q 值

        next_q = self._forward(next_states, [self.target_noisy1, self.target_noisy2, self.target_noisy3])

        next_q_max = np.max(next_q, axis=1)

        td_target = rewards + self.gamma * next_q_max * (1 - dones)



        loss = np.mean((current_q - td_target) ** 2)



        self.train_step += 1

        if self.train_step % self.target_update_freq == 0:

            self._sync_target()



        return loss



    def get_noise_std(self):

        """获取当前噪声标准差（调试用）"""

        return {

            'layer1': np.mean(self.noisy1.sigma_w),

            'layer2': np.mean(self.noisy2.sigma_w),

            'layer3': np.mean(self.noisy3.sigma_w)

        }





if __name__ == "__main__":

    from collections import deque



    # 重新定义 memory（避免导入问题）

    class TestNoisyDQN(NoisyDQN):

        def __init__(self, *args, **kwargs):

            super().__init__(*args, **kwargs)

            self.memory = deque(maxlen=10000)



    state_dim = 4

    action_dim = 2

    agent = TestNoisyDQN(state_dim, action_dim)



    for ep in range(5):

        agent.reset_noise()  # 每个 episode 重置噪声

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

        noise_std = agent.get_noise_std()

        print(f"Episode {ep+1}: reward={total_reward:.2f}, loss={loss:.4f}, "

              f"noise_std={noise_std['layer1']:.4f}")



    print("\nNoisyNet DQN 测试完成!")

