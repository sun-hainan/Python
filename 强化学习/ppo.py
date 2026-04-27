# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / ppo



本文件实现 ppo 相关的算法功能。

"""



import numpy as np

import random





class PPO:

    """PPO 智能体（近端策略优化，使用自适应 KL 散度约束）"""



    def __init__(self, state_dim, action_num, hidden_dim=64, lr=0.0003,

                 gamma=0.99, eps_clip=0.2, k_epochs=4, entropy_coef=0.01):

        self.state_dim = state_dim

        self.action_num = action_num

        self.gamma = gamma

        self.eps_clip = eps_clip  # PPO 剪辑范围

        self.k_epochs = k_epochs  # 每次更新的 epoch 数

        self.entropy_coef = entropy_coef  # 熵正则化系数

        self.lr = lr



        # 策略网络（Actor）

        fan_in = state_dim + hidden_dim

        scale = np.sqrt(2.0 / fan_in)

        self.actor_w1 = np.random.randn(state_dim, hidden_dim) * scale

        self.actor_b1 = np.zeros(hidden_dim)

        scale_out = np.sqrt(2.0 / (hidden_dim + action_num))

        self.actor_w2 = np.random.randn(hidden_dim, action_num) * scale_out

        self.actor_b2 = np.zeros(action_num)



        # 价值网络（Critic）

        scale_c = np.sqrt(2.0 / (state_dim + hidden_dim))

        self.critic_w1 = np.random.randn(state_dim, hidden_dim) * scale_c

        self.critic_b1 = np.zeros(hidden_dim)

        scale_cout = np.sqrt(2.0 / (hidden_dim + 1))

        self.critic_w2 = np.random.randn(hidden_dim, 1) * scale_cout

        self.critic_b2 = np.zeros(1)



        # 旧策略概率（用于计算重要性采样比）

        self.old_log_probs = None



    def softmax(self, x):

        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))

        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)



    def forward_actor(self, state):

        """Actor: 计算动作概率"""

        hidden = np.tanh(np.dot(state, self.actor_w1) + self.actor_b1)

        logits = np.dot(hidden, self.actor_w2) + self.actor_b2

        return self.softmax(logits), hidden



    def forward_critic(self, state):

        """Critic: 估计状态价值 V(s)"""

        hidden = np.tanh(np.dot(state, self.critic_w1) + self.critic_b1)

        return float(np.dot(hidden, self.critic_w2) + self.critic_b2)



    def choose_action(self, state):

        """采样动作并返回 log 概率"""

        probs, _ = self.forward_actor(state)

        action = np.random.choice(self.action_num, p=probs)

        log_prob = np.log(probs[action] + 1e-8)

        return action, log_prob



    def compute_returns(self, rewards, gamma):

        """计算折扣回报和优势"""

        returns = []

        G = 0

        for reward in reversed(rewards):

            G = reward + gamma * G

            returns.insert(0, G)

        returns = np.array(returns)

        # 标准化

        returns = (returns - np.mean(returns)) / (np.std(returns) + 1e-8)

        advantages = returns  # 简化为 returns 作为 advantage（实际应用可用 GAE）

        return returns, advantages



    def update(self, trajectory):

        """PPO 更新：多 epoch 小批量更新"""

        states = np.array(trajectory["states"])

        actions = np.array(trajectory["actions"])

        old_log_probs = np.array(trajectory["log_probs"])

        rewards = trajectory["rewards"]



        returns, advantages = self.compute_returns(rewards, self.gamma)



        for _ in range(self.k_epochs):

            # 随机打乱并分批

            indices = np.arange(len(states))

            np.random.shuffle(indices)



            for idx in indices:

                s = states[idx:idx+1] if len(states) > 1 else states

                s = s.reshape(1, -1) if s.ndim == 1 else s

                a = actions[idx]

                old_log_p = old_log_probs[idx]

                advantage = advantages[idx]



                # 当前策略的概率和隐藏层

                probs, hidden = self.forward_actor(s.reshape(1, -1) if s.ndim == 1 else s)

                new_log_prob = np.log(probs[a] + 1e-8)



                # 重要性采样比 r(θ) = π_θ(a|s) / π_old(a|s)

                ratio = np.exp(new_log_prob - old_log_p)

                ratio = np.clip(ratio, 0.5, 2.0)  # 防止极端值



                # PPO 剪辑目标

                surr1 = ratio * advantage

                surr2 = np.clip(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantage

                policy_loss = -np.minimum(surr1, surr2)



                # 熵奖励（鼓励探索）

                entropy = -np.sum(probs * np.log(probs + 1e-8))

                entropy_loss = -self.entropy_coef * entropy



                # Critic 损失

                value_pred = self.forward_critic(s.reshape(1, -1) if s.ndim == 1 else s)

                critic_loss = 0.5 * (value_pred - returns[idx]) ** 2



                # 简化梯度更新

                total_loss = policy_loss + entropy_loss + 0.5 * critic_loss



                # 策略梯度（单步 SGD）

                d_logits = -probs.copy()

                d_logits[a] += 1

                d_actor_w2 = np.outer(hidden.flatten(), d_logits) * (-np.minimum(surr1, surr2) + entropy_loss)

                d_hidden = np.dot(d_logits, self.actor_w2.T) * (1 - hidden ** 2)

                d_actor_w1 = np.outer(s.flatten() if s.ndim == 1 else s, d_hidden) * (-np.minimum(surr1, surr2))



                self.actor_w2 -= self.lr * d_actor_w2

                self.actor_b2 -= self.lr * d_logits * (-np.minimum(surr1, surr2))

                self.actor_w1 -= self.lr * d_actor_w1

                self.actor_b1 -= self.lr * d_hidden.flatten() * (-np.minimum(surr1, surr2))



                # Critic 更新

                td_err = returns[idx] - value_pred

                d_critic_w2 = td_err * hidden.flatten()

                d_critic_w1 = td_err * self.critic_w2.flatten() * (1 - hidden.flatten() ** 2)

                if s.ndim == 1:

                    d_critic_w1 = np.outer(s, d_critic_w1)

                else:

                    d_critic_w1 = np.outer(s.flatten(), d_critic_w1)

                self.critic_w2 -= self.lr * d_critic_w2.reshape(self.critic_w2.shape)

                self.critic_b2 -= self.lr * td_err

                self.critic_w1 -= self.lr * d_critic_w1

                self.critic_b1 -= self.lr * td_err * (1 - hidden.flatten() ** 2)





def simple_env():

    """测试用环境"""

    class SimpleEnv:

        def __init__(self):

            self.state_dim = 4

            self.action_num = 2



        def reset(self):

            return np.random.randn(self.state_dim).tolist()



        def step(self, action):

            next_state = np.random.randn(self.state_dim).tolist()

            reward = float(action) * 0.5 - 0.1

            done = random.random() < 0.1

            return next_state, reward, done



    return SimpleEnv()





if __name__ == "__main__":

    # 测试 PPO

    env = simple_env()

    agent = PPO(state_dim=4, action_num=2, lr=0.0003)

    episodes = 100

    for ep in range(episodes):

        state = env.reset()

        trajectory = {"states": [], "actions": [], "log_probs": [], "rewards": []}

        done = False

        while not done:

            action, log_prob = agent.choose_action(state)

            next_state, reward, done = env.step(action)

            trajectory["states"].append(state)

            trajectory["actions"].append(action)

            trajectory["log_probs"].append(log_prob)

            trajectory["rewards"].append(reward)

            state = next_state

        agent.update(trajectory)

        total_reward = sum(trajectory["rewards"])

        if ep % 20 == 0:

            print(f"Episode {ep}, reward: {total_reward:.2f}")

    print("PPO 训练完成")

