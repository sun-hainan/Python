# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / model_based_rl



本文件实现 model_based_rl 相关的算法功能。

"""



import numpy as np

import random

from collections import deque





class DynamicsModel:

    """

    动态模型（学习环境转移和奖励）



    简化为线性高斯模型：

        s' = f(s, a) + noise

        r = g(s, a) + noise

    """



    def __init__(self, state_dim, action_dim, hidden_dim=64):

        """

        初始化动态模型



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.hidden_dim = hidden_dim



        # 转移网络权重（简化为线性模型 + 残差）

        np.random.seed(42)

        self.transition_weights = np.random.randn(state_dim, state_dim + action_dim) * 0.01

        self.transition_bias = np.zeros(state_dim)



        # 奖励网络权重

        self.reward_weights = np.random.randn(1, state_dim + action_dim) * 0.01

        self.reward_bias = np.zeros(1)



        # 噪声方差估计

        self.state_noise_var = 0.1

        self.reward_noise_var = 0.1



        # 经验缓冲

        self.memory = deque(maxlen=10000)

        self.fitted = False



    def predict_next_state(self, state, action):

        """

        预测下一个状态



        参数:

            state: 当前状态

            action: 执行的动作

        返回:

            next_state: 预测的下一个状态

        """

        state_action = np.concatenate([state, action])

        delta = np.dot(state_action, self.transition_weights.T) + self.transition_bias

        next_state = state + delta

        return next_state



    def predict_reward(self, state, action):

        """

        预测奖励



        参数:

            state: 当前状态

            action: 执行的动作

        返回:

            reward: 预测的奖励

        """

        state_action = np.concatenate([state, action])

        reward = np.dot(state_action, self.reward_weights.T) + self.reward_bias

        return reward.squeeze()



    def store_transition(self, state, action, reward, next_state, done):

        """存储转移样本"""

        self.memory.append((state, action, reward, next_state, done))



    def fit(self):

        """拟合动态模型（线性回归）"""

        if len(self.memory) < 100:

            return



        # 准备数据

        states = np.array([t[0] for t in self.memory])

        actions = np.array([t[1] for t in self.memory])

        rewards = np.array([t[2] for t in self.memory])

        next_states = np.array([t[3] for t in self.memory])



        # 状态变化

        delta_states = next_states - states



        # 构建输入输出

        X = np.concatenate([states, actions], axis=1)

        Y_delta = delta_states

        Y_reward = rewards



        # 线性回归拟合转移

        self.transition_weights = np.linalg.lstsq(X, Y_delta, rcond=None)[0]

        residuals = Y_delta - np.dot(X, self.transition_weights)

        self.state_noise_var = np.var(residuals) + 1e-6



        # 线性回归拟合奖励

        self.reward_weights = np.linalg.lstsq(X, Y_reward, rcond=None)[0]

        reward_residuals = Y_reward - np.dot(X, self.reward_weights.T).squeeze()

        self.reward_noise_var = np.var(reward_residuals) + 1e-6



        self.fitted = True

        print(f"Dynamics Model fitted. State noise var: {self.state_noise_var:.4f}, "

              f"Reward noise var: {self.reward_noise_var:.4f}")





class MPCPlanner:

    """

    模型预测控制（Model Predictive Control）规划器



    MPC 通过以下步骤进行决策：

    1. 使用动态模型模拟未来 T 步

    2. 优化动作序列使累积奖励最大

    3. 只执行第一个动作，然后重新规划

    """



    def __init__(self, dynamics_model, state_dim, action_dim,

                 horizon=5, n_samples=1000, top_k=50):

        """

        初始化 MPC 规划器



        参数:

            dynamics_model: 动态模型

            state_dim: 状态维度

            action_dim: 动作维度

            horizon: 预测时域

            n_samples: 每个时刻的采样数量

            top_k: 每轮保留的最优动作数

        """

        self.model = dynamics_model

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.horizon = horizon

        self.n_samples = n_samples

        self.top_k = top_k



        # 动作空间（假设连续动作，有界）

        self.action_low = -2.0

        self.action_high = 2.0



    def plan(self, state, epsilon=0.0):

        """

        为给定状态规划动作



        参数:

            state: 当前状态

            epsilon: 随机探索概率

        返回:

            best_action: 最优动作

        """

        if random.random() < epsilon:

            # 随机探索

            return np.random.uniform(self.action_low, self.action_high, self.action_dim)



        best_total_reward = -float('inf')

        best_action = None

        best_trajectories = []



        for _ in range(self.n_samples):

            # 采样动作序列

            actions = np.random.uniform(

                self.action_low, self.action_high,

                size=(self.horizon, self.action_dim)

            )

            # 简化的交叉变异：用已有好动作扰动

            if best_trajectories and random.random() < 0.5:

                parent = random.choice(best_trajectories)

                actions[0] = parent[0] + np.random.randn(self.action_dim) * 0.5



            # 模拟轨迹

            total_reward, final_state, trajectory = self._simulate(state, actions)

            best_trajectories.append((actions[0].copy(), total_reward))



            if total_reward > best_total_reward:

                best_total_reward = total_reward

                best_action = actions[0]



        # 保留 top-k 用于下次采样

        best_trajectories.sort(key=lambda x: x[1], reverse=True)

        self.elite_actions = [t[0] for t in best_trajectories[:self.top_k]]



        return best_action if best_action is not None else np.zeros(self.action_dim)



    def _simulate(self, state, actions):

        """

        使用模型模拟轨迹



        参数:

            state: 起始状态

            actions: 动作序列

        返回:

            total_reward: 累积奖励

            final_state: 最终状态

            trajectory: 轨迹（状态-动作序列）

        """

        current_state = state.copy()

        total_reward = 0.0

        trajectory = [(current_state, actions[0])]



        for t, action in enumerate(actions):

            # 预测下一步

            next_state = self.model.predict_next_state(current_state, action)

            reward = self.model.predict_reward(current_state, action)



            # 添加噪声

            next_state += np.random.randn(self.state_dim) * np.sqrt(self.model.state_noise_var)

            reward += np.random.randn() * np.sqrt(self.model.reward_noise_var)



            total_reward += (0.99 ** t) * reward

            current_state = next_state

            trajectory.append((current_state, actions[t + 1] if t + 1 < len(actions) else None))



        return total_reward, current_state, trajectory





class ModelBasedRL:

    """

    基于模型的强化学习智能体



    结合：

    1. 动态模型学习

    2. MPC 规划

    3. 无模型微调（可选）

    """



    def __init__(self, state_dim, action_dim, hidden_dim=64,

                 horizon=5, n_samples=500, real_env_ratio=0.1):

        """

        初始化 Model-Based RL



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

            horizon: MPC 预测时域

            n_samples: MPC 采样数量

            real_env_ratio: 真实环境交互比例

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.horizon = horizon

        self.n_samples = n_samples

        self.real_env_ratio = real_env_ratio



        # 动态模型

        self.dynamics_model = DynamicsModel(state_dim, action_dim, hidden_dim)



        # MPC 规划器

        self.planner = MPCPlanner(

            self.dynamics_model, state_dim, action_dim,

            horizon=horizon, n_samples=n_samples

        )



        # 经验缓冲（真实交互）

        self.real_memory = deque(maxlen=5000)



        # 是否使用模型

        self.use_model = True



    def select_action(self, state, epsilon=0.0):

        """

        选择动作



        参数:

            state: 当前状态

            epsilon: 探索率

        返回:

            action: 选择的动作

        """

        if self.use_model and self.dynamics_model.fitted:

            # 使用 MPC 规划

            action = self.planner.plan(state, epsilon=epsilon)

        else:

            # 随机动作

            action = np.random.uniform(-2, 2, self.action_dim)

        return action



    def update(self, state, action, reward, next_state, done):

        """

        更新模型



        参数:

            state: 当前状态

            action: 执行的动作

            reward: 获得的奖励

            next_state: 下一个状态

            done: 是否结束

        """

        # 存储真实经验

        self.real_memory.append((state, action, reward, next_state, done))



        # 更新动态模型

        self.dynamics_model.store_transition(state, action, reward, next_state, done)



        # 每隔一定步数拟合模型

        if len(self.real_memory) % 100 == 0:

            self.dynamics_model.fit()





if __name__ == "__main__":

    state_dim = 4

    action_dim = 2



    agent = ModelBasedRL(state_dim, action_dim, horizon=5, n_samples=200)



    # 模拟训练

    for episode in range(10):

        state = np.random.randn(state_dim)

        total_reward = 0



        for step in range(50):

            # 选择动作

            action = agent.select_action(state, epsilon=0.2)



            # 模拟环境

            next_state = state + 0.1 * action + np.random.randn(state_dim) * 0.1

            reward = -np.sum(state ** 2) - 0.1 * np.sum(action ** 2)

            done = random.random() < 0.05



            # 更新

            agent.update(state, action, reward, next_state, done)



            total_reward += reward

            state = next_state



            if done:

                break



        model_status = "fitted" if agent.dynamics_model.fitted else "unfitted"

        print(f"Episode {episode+1}: reward={total_reward:.2f}, "

              f"model={model_status}, memory={len(agent.real_memory)}")



    print("\nModel-Based RL 测试完成!")

