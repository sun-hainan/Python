# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / a3c



本文件实现 a3c 相关的算法功能。

"""



import numpy as np

import random

import threading

import time





class ActorCritic:

    """Actor-Critic 网络（共享特征提取 + 分离的策略和价值头）"""



    def __init__(self, state_dim, action_dim, hidden_dim=128, lr=0.0007,

                 gamma=0.99, entropy_coef=0.01, value_coef=0.5):

        """

        初始化 Actor-Critic



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

            lr: 学习率

            gamma: 折扣因子

            entropy_coef: 熵正则化系数（鼓励探索）

            value_coef: 价值损失系数

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.gamma = gamma

        self.entropy_coef = entropy_coef

        self.value_coef = value_coef

        self.lr = lr



        # 初始化网络权重

        np.random.seed(42)

        self.weights = self._init_weights()



    def _init_weights(self):

        """初始化网络权重"""

        return {

            'w1': np.random.randn(self.state_dim, 128) * np.sqrt(2.0 / self.state_dim),

            'b1': np.zeros(128),

            'w2': np.random.randn(128, 128) * np.sqrt(2.0 / 128),

            'b2': np.zeros(128),

            # Actor 头（策略）

            'w_actor': np.random.randn(128, self.action_dim) * 0.01,

            'b_actor': np.zeros(self.action_dim),

            # Critic 头（价值）

            'w_critic': np.random.randn(128, 1) * 0.01,

            'b_critic': np.zeros(1)

        }



    def forward(self, state, weights=None):

        """

        前向传播



        参数:

            state: 输入状态

            weights: 可选的权重覆盖（用于从全局网络拉取）

        返回:

            action_probs: 动作概率分布

            value: 状态价值

        """

        if weights is None:

            weights = self.weights



        # 共享特征提取

        h = np.maximum(0, np.dot(state, weights['w1']) + weights['b1'])

        h = np.maximum(0, np.dot(h, weights['w2']) + weights['b2'])



        # Actor：Softmax 动作概率

        logits = np.dot(h, weights['w_actor']) + weights['b_actor']

        logits_exp = np.exp(logits - np.max(logits))

        action_probs = logits_exp / np.sum(logits_exp, axis=-1, keepdims=True)



        # Critic：状态价值

        value = np.dot(h, weights['w_critic']) + weights['b_critic']



        return action_probs, value.squeeze()



    def get_action(self, state, weights=None):

        """

        采样动作



        参数:

            state: 当前状态

            weights: 使用的权重

        返回:

            action: 采样的动作索引

            log_prob: 对数概率

            entropy: 策略熵

            value: 状态价值

        """

        state = np.array(state).reshape(1, -1)

        action_probs, value = self.forward(state, weights)

        action_probs = action_probs.squeeze()



        # 采样

        action = np.random.choice(self.action_dim, p=action_probs)

        # 计算对数概率（加入 eps 防止 log(0)）

        eps = 1e-8

        log_prob = np.log(action_probs[action] + eps)

        # 计算熵

        entropy = -np.sum(action_probs * np.log(action_probs + eps))



        return action, log_prob, entropy, value



    def compute_gae(self, rewards, values, next_value, dones, gamma=0.99, lam=0.95):

        """

        计算 GAE（Generalized Advantage Estimation）



        GAE 通过平衡偏差和方差提供更好的优势函数估计：

        A_t = δ_t + γλδ_{t+1} + ... + (γλ)^{T-t}δ_T



        参数:

            rewards: 奖励序列

            values: 价值序列

            next_value: 最后一个状态的估计价值

            dones: 完成标志

            gamma: 折扣因子

            lam: GAE 参数（lambda）

        返回:

            advantages: 优势序列

        """

        advantages = []

        gae = 0

        values = list(values) + [next_value]



        for t in reversed(range(len(rewards))):

            # TD 误差

            delta = rewards[t] + gamma * values[t + 1] * (1 - dones[t]) - values[t]

            # GAE 累积

            gae = delta + gamma * lam * (1 - dones[t]) * gae

            advantages.insert(0, gae)



        return np.array(advantages)





class A3CTrainer:

    """A3C 训练器（管理多个 worker 线程）"""



    def __init__(self, state_dim, action_dim, n_workers=4,

                 max_steps=20, update_freq=5):

        """

        初始化 A3C 训练器



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            n_workers: 并行 worker 数量

            max_steps: 每个 episode 最大步数

            update_freq: 更新频率（每隔多少步同步到全局）

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.n_workers = n_workers

        self.max_steps = max_steps

        self.update_freq = update_freq



        # 全局网络

        self.global_network = ActorCritic(state_dim, action_dim)

        self.global_weights = self.global_network.weights.copy()



        # 优化器状态（简化版）

        self.optimizer_state = None



        # 锁（用于同步全局网络）

        self.lock = threading.Lock()



    def local_update(self, worker_id):

        """

        Worker 线程的本地更新流程



        参数:

            worker_id: Worker 编号

        """

        np.random.seed(int(time.time() * 1000) % (2**31))

        local_network = ActorCritic(self.state_dim, self.action_dim)



        episode_rewards = []

        total_steps = 0



        for episode in range(3):

            state = np.random.randn(self.state_dim)

            episode_reward = 0

            values_history = []

            rewards_history = []

            states_history = []

            actions_history = []

            dones_history = []



            for step in range(self.max_steps):

                # 从全局网络拉取最新权重

                with self.lock:

                    local_network.weights = self.global_weights.copy()



                # 选择动作

                action, log_prob, entropy, value = local_network.get_action(state)



                # 环境交互（模拟）

                next_state = np.random.randn(self.state_dim)

                reward = random.uniform(-1, 1)

                done = random.random() < 0.1



                # 存储经验

                states_history.append(state)

                actions_history.append(action)

                rewards_history.append(reward)

                values_history.append(value)

                dones_history.append(done)



                episode_reward += reward

                state = next_state

                total_steps += 1



                # 定期更新全局网络

                if len(rewards_history) >= self.update_freq or done:

                    # 计算 GAE

                    if done:

                        next_value = 0

                    else:

                        _, _, _, next_value = local_network.get_action(state)



                    advantages = local_network.compute_gae(

                        rewards_history, values_history, next_value, dones_history

                    )



                    # 简化的梯度更新（实际应反向传播）

                    with self.lock:

                        # 应用梯度更新到全局网络（简化版）

                        grad_scale = 0.01

                        for key in self.global_network.weights:

                            # 简单 SGD 更新

                            self.global_weights[key] += grad_scale * np.random.randn(

                                *self.global_network.weights[key].shape

                            ) * np.mean(advantages)



                    # 清空本地历史

                    values_history = []

                    rewards_history = []

                    states_history = []

                    actions_history = []

                    dones_history = []



                if done:

                    break



            episode_rewards.append(episode_reward)

            print(f"Worker {worker_id} | Episode {episode+1}: reward={episode_reward:.2f}")



        return episode_rewards



    def train(self):

        """启动多线程训练"""

        threads = []

        for i in range(self.n_workers):

            t = threading.Thread(target=lambda wid=i: self.local_update(wid))

            threads.append(t)

            t.start()



        for t in threads:

            t.join()



    def get_weights(self):

        """获取全局网络权重"""

        return self.global_weights.copy()





if __name__ == "__main__":

    state_dim = 4

    action_dim = 2

    n_workers = 4



    trainer = A3CTrainer(state_dim, action_dim, n_workers=n_workers)



    print(f"启动 A3C 训练（{n_workers} 个 Workers）...")

    trainer.train()



    print("\nA3C 测试完成!")

