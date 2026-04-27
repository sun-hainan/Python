# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / trpo



本文件实现 trpo 相关的算法功能。

"""



import numpy as np

import random





class TRPOAgent:

    """TRPO 策略优化算法（简化实现）"""



    def __init__(self, state_dim, action_dim, hidden_dim=64,

                 max_kl=0.01, damping=0.1, n_cg_steps=10):

        """

        初始化 TRPO Agent



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

            max_kl: 最大 KL 散度约束

            damping: 共轭梯度阻尼系数

            n_cg_steps: 共轭梯度迭代步数

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.hidden_dim = hidden_dim

        self.max_kl = max_kl  # KL 散度约束

        self.damping = damping  # 阻尼系数（确保 Fisher 信息矩阵正定）

        self.n_cg_steps = n_cg_steps  # CG 迭代次数



        # 策略网络参数（简化为高斯策略）

        self.policy_params = self._init_policy()

        self.log_std = np.zeros(action_dim)  # 对数标准差



    def _init_policy(self):

        """初始化策略网络参数"""

        np.random.seed(42)

        return {

            'w1': np.random.randn(self.state_dim, self.hidden_dim) * np.sqrt(2.0 / self.state_dim),

            'b1': np.zeros(self.hidden_dim),

            'w2': np.random.randn(self.hidden_dim, self.hidden_dim) * np.sqrt(2.0 / self.hidden_dim),

            'b2': np.zeros(self.hidden_dim),

            'w_mean': np.random.randn(self.hidden_dim, self.action_dim) * 0.01,

            'b_mean': np.zeros(self.action_dim)

        }



    def _forward_policy(self, state, params):

        """策略网络前向传播，返回动作分布的均值和标准差"""

        h = np.maximum(0, np.dot(state, params['w1']) + params['b1'])

        h = np.maximum(0, np.dot(h, params['w2']) + params['b2'])

        mean = np.dot(h, params['w_mean']) + params['b_mean']

        std = np.exp(self.log_std)

        return mean, std



    def get_action(self, state):

        """

        根据当前策略采样动作



        参数:

            state: 当前状态

        返回:

            action: 采样动作

            log_prob: 动作的对数概率

        """

        state = np.array(state).reshape(1, -1)

        mean, std = self._forward_policy(state, self.policy_params)

        mean = mean.squeeze()

        std = std.squeeze()



        # 从高斯分布采样

        action = mean + std * np.random.randn(self.action_dim)

        # 计算对数概率

        log_prob = -0.5 * np.sum(((action - mean) / std) ** 2) - \

                   0.5 * self.action_dim * np.log(2 * np.pi) - \

                   np.sum(np.log(std))

        return action, log_prob



    def get_action_det(self, state):

        """获取确定性动作（用于评估）"""

        state = np.array(state).reshape(1, -1)

        mean, _ = self._forward_policy(state, self.policy_params)

        return mean.squeeze()



    def compute_log_prob(self, state, action, params):

        """计算给定状态-动作对的对数概率"""

        mean, std = self._forward_policy(state, params)

        log_prob = -0.5 * np.sum(((action - mean) / std) ** 2) - \

                   0.5 * self.action_dim * np.log(2 * np.pi) - \

                   np.sum(np.log(std))

        return log_prob



    def compute_kl(self, state, params_old, params_new):

        """计算新旧策略之间的平均 KL 散度"""

        kl_sum = 0.0

        batch_size = min(100, len(state))

        indices = np.random.choice(len(state), batch_size, replace=False)

        for idx in indices:

            s = state[idx:idx+1]

            mean_old, std_old = self._forward_policy(s, params_old)

            mean_new, std_new = self._forward_policy(s, params_new)

            mean_old = mean_old.squeeze()

            mean_new = mean_new.squeeze()

            std_old = std_old.squeeze()

            std_new = std_new.squeeze()



            # KL(N(μ1,σ1) || N(μ2,σ2))

            kl = np.sum(np.log(std_new / std_old)) - 0.5 * self.action_dim + \

                 np.sum((std_old ** 2 + (mean_old - mean_new) ** 2) / (2 * std_new ** 2))

            kl_sum += kl

        return kl_sum / batch_size



    def compute_gradient(self, states, actions, advantages, params_old):

        """

        计算策略梯度（简化版：使用有限差分自然梯度）



        返回:

            gradient: 参数梯度方向

        """

        batch_size = len(states)

        gradient = np.zeros(self._get_param_size())



        eps = 1e-4

        for i in range(self._get_param_size()):

            params_plus = self._unpack_params(self.policy_params)

            params_minus = self._unpack_params(self.policy_params)

            params_plus[i] += eps

            params_minus[i] -= eps



            p_plus = self._pack_params(params_plus)

            p_minus = self._pack_params(params_minus)



            # 近似导数

            kl_plus = self.compute_kl(states, p_minus, p_plus)

            grad_i = kl_plus / eps



            gradient[i] = grad_i



        return gradient



    def _get_param_size(self):

        """获取参数总数"""

        size = 0

        for v in self.policy_params.values():

            size += np.size(v)

        return size



    def _unpack_params(self, params_dict):

        """将参数字典展平为向量"""

        vec = []

        for v in sorted(params_dict.keys()):

            vec.append(params_dict[v].flatten())

        return np.concatenate(vec)



    def _pack_params(self, vec):

        """将向量打包为参数字典"""

        idx = 0

        new_params = {}

        shapes = {

            'w1': (self.state_dim, self.hidden_dim),

            'b1': (self.hidden_dim,),

            'w2': (self.hidden_dim, self.hidden_dim),

            'b2': (self.hidden_dim,),

            'w_mean': (self.hidden_dim, self.action_dim),

            'b_mean': (self.action_dim,)

        }

        for name in ['w1', 'b1', 'w2', 'b2', 'w_mean', 'b_mean']:

            shape = shapes[name]

            size = np.prod(shape)

            new_params[name] = vec[idx:idx+size].reshape(shape)

            idx += size

        return new_params



    def update(self, trajectories):

        """

        使用轨迹数据更新策略



        参数:

            trajectories: 轨迹列表，每条轨迹包含 (states, actions, rewards, advantages)

        """

        # 收集所有数据

        all_states = []

        all_actions = []

        all_advantages = []

        all_old_log_probs = []



        for traj in trajectories:

            states, actions, rewards, advantages = traj

            all_states.extend(states)

            all_actions.extend(actions)

            all_advantages.extend(advantages)



            # 计算旧策略的对数概率

            for s, a in zip(states, actions):

                s = np.array(s).reshape(1, -1)

                a = np.array(a)

                log_prob = self.compute_log_prob(s, a, self.policy_params)

                all_old_log_probs.append(log_prob)



        all_states = np.array(all_states)

        all_actions = np.array(all_actions)

        all_advantages = np.array(all_advantages)

        all_old_log_probs = np.array(all_old_log_probs)



        # 归一化 advantages

        all_advantages = (all_advantages - np.mean(all_advantages)) / (np.std(all_advantages) + 1e-8)



        # 简化更新：直接使用策略梯度 + 线搜索

        params_old = {k: v.copy() for k, v in self.policy_params.items()}



        # 计算梯度（简化：使用有限差分）

        gradient = self.compute_gradient(all_states, all_actions, all_advantages, params_old)



        # 线搜索

        step_size = 0.1

        for _ in range(10):

            params_vec = self._unpack_params(self.policy_params)

            new_params_vec = params_vec + step_size * gradient

            new_params = self._pack_params(new_params_vec)



            # 检查 KL 约束

            kl = self.compute_kl(all_states, params_old, new_params)

            if kl < self.max_kl:

                self.policy_params = new_params

                break

            step_size *= 0.5





class Baseline:

    """价值函数基线（用于计算优势函数）"""



    def __init__(self, state_dim, hidden_dim=64):

        self.state_dim = state_dim

        self.weights = np.random.randn(state_dim) * 0.01



    def predict(self, state):

        """预测状态价值"""

        return np.dot(state, self.weights)



    def update(self, states, returns):

        """更新基线（线性回归）"""

        # 简化为线性拟合

        self.weights = np.linalg.lstsq(states, returns, rcond=None)[0]





if __name__ == "__main__":

    state_dim = 4

    action_dim = 2

    agent = TRPOAgent(state_dim, action_dim)

    baseline = Baseline(state_dim)



    # 模拟训练

    for episode in range(5):

        trajectories = []

        for _ in range(3):

            states = []

            actions = []

            rewards = []

            state = np.random.randn(state_dim)

            for step in range(10):

                action, log_prob = agent.get_action(state)

                next_state = np.random.randn(state_dim)

                reward = random.uniform(-1, 1)

                states.append(state)

                actions.append(action)

                rewards.append(reward)

                state = next_state



            # 计算 advantages（简化：reward - baseline）

            returns = np.cumsum(rewards[::-1])[::-1]

            advantages = []

            for s, r in zip(states, returns):

                baseline_val = baseline.predict(s)

                advantages.append(r - baseline_val)

            advantages = np.array(advantages)



            trajectories.append((states, actions, rewards, advantages))



            # 更新 baseline

            baseline.update(np.array(states), returns)



        agent.update(trajectories)

        total_reward = sum(sum(t[2]) for t in trajectories)

        print(f"Episode {episode+1}: total_reward={total_reward:.2f}, "

              f"trajectories={len(trajectories)}")



    print("\nTRPO 测试完成!")

