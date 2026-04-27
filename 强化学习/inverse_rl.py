# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / inverse_rl



本文件实现 inverse_rl 相关的算法功能。

"""



import numpy as np

import random





class MaxEntIRL:

    """

    最大熵逆向强化学习（MaxEnt IRL）



    核心思想：在所有能解释专家行为的奖励函数中，选择熵最大的那个。

    这避免了过度拟合到某些特定轨迹。



    能量函数：P(τ|θ) = exp(Σ r_θ(s_t, a_t)) / Z(θ)

    奖励近似：r_θ(s, a) ≈ w · φ(s, a)



    参数学习使用梯度上升：

        ∇_w L = E_π_expert[φ(s,a)] - E_π_θ[φ(s,a)]

    """



    def __init__(self, state_dim, action_dim, feature_dim, gamma=0.99,

                 lr=0.01, n_trajectories=10, trajectory_len=50):

        """

        初始化 MaxEnt IRL



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            feature_dim: 特征维度

            gamma: 折扣因子

            lr: 学习率

            n_trajectories: 演示轨迹数量

            trajectory_len: 每条轨迹长度

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.feature_dim = feature_dim

        self.gamma = gamma

        self.lr = lr

        self.n_trajectories = n_trajectories

        self.trajectory_len = trajectory_len



        # 奖励权重

        np.random.seed(42)

        self.weights = np.random.randn(feature_dim) * 0.01



        # 特征基函数（简化为状态特征的线性组合）

        self.feature_weights = np.random.randn(state_dim, feature_dim) * 0.1



    def extract_features(self, state, action):

        """

        提取状态-动作特征



        参数:

            state: 状态

            action: 动作

        返回:

            features: 特征向量

        """

        state_features = np.tanh(np.dot(state, self.feature_weights))

        action_onehot = np.zeros(self.action_dim)

        if action is not None:

            action_onehot[action % self.action_dim] = 1.0

        return np.concatenate([state_features, action_onehot])



    def compute_reward(self, state, action):

        """

        计算奖励（线性奖励函数）



        参数:

            state: 状态

            action: 动作

        返回:

            reward: 奖励值

        """

        features = self.extract_features(state, action)

        return np.dot(self.weights, features)



    def generate_trajectories(self, policy, env, n_traj=None, deterministic=True):

        """

        使用给定策略生成轨迹



        参数:

            policy: 策略（接受状态返回动作）

            env: 环境

            n_traj: 轨迹数量

            deterministic: 是否确定性动作

        返回:

            trajectories: 轨迹列表

        """

        n_traj = n_traj or self.n_trajectories

        trajectories = []



        for _ in range(n_traj):

            state = np.random.randn(self.state_dim) * 0.5

            trajectory = {'states': [], 'actions': [], 'rewards': []}



            for step in range(self.trajectory_len):

                trajectory['states'].append(state)



                if deterministic:

                    action = policy(state)

                else:

                    action = policy(state, add_noise=True)



                trajectory['actions'].append(action)



                # 计算奖励

                reward = self.compute_reward(state, action)

                trajectory['rewards'].append(reward)



                # 模拟环境转移

                next_state = state + 0.1 * np.eye(self.action_dim)[action % self.action_dim] + \

                            np.random.randn(self.state_dim) * 0.05

                state = next_state



            trajectories.append(trajectory)



        return trajectories



    def compute_feature_expectation(self, trajectories, normalize=True):

        """

        计算轨迹的特征期望



        参数:

            trajectories: 轨迹列表

            normalize: 是否归一化

        返回:

            feature_exp: 平均特征期望

        """

        total_features = np.zeros(self.feature_dim)

        total_steps = 0



        for traj in trajectories:

            for step, (s, a) in enumerate(zip(traj['states'], traj['actions'])):

                discount = self.gamma ** step

                features = self.extract_features(s, a)

                total_features += discount * features

                total_steps += 1



        if normalize and total_steps > 0:

            return total_features / total_steps

        return total_features



    def gradient(self, expert_trajectories, policy_trajectories):

        """

        计算 IRL 梯度



        ∇_w L = E_π_expert[φ(s,a)] - E_π_θ[φ(s,a)]



        参数:

            expert_trajectories: 专家轨迹

            policy_trajectories: 当前策略轨迹

        返回:

            gradient: 权重梯度

        """

        # 专家特征期望

        expert_features = self.compute_feature_expectation(expert_trajectories)



        # 策略特征期望

        policy_features = self.compute_feature_expectation(policy_trajectories)



        # 梯度

        grad = expert_features - policy_features

        return grad



    def update(self, expert_trajectories, policy_trajectories):

        """

        更新奖励权重



        参数:

            expert_trajectories: 专家轨迹

            policy_trajectories: 当前策略轨迹

        """

        grad = self.gradient(expert_trajectories, policy_trajectories)

        self.weights += self.lr * grad



    def train(self, expert_trajectories, n_iterations=100):

        """

        训练 IRL



        参数:

            expert_trajectories: 专家演示轨迹

            n_iterations: 迭代次数

        """

        print("开始 MaxEnt IRL 训练...")



        # 简化的策略函数

        def simple_policy(state, add_noise=False):

            # 基于奖励权重的简单贪心策略

            best_action = 0

            best_reward = -float('inf')

            for a in range(self.action_dim):

                r = self.compute_reward(state, a)

                if r > best_reward:

                    best_reward = r

                    best_action = a

            if add_noise:

                best_action = (best_action + random.randint(-1, 1)) % self.action_dim

            return best_action



        for iteration in range(n_iterations):

            # 生成当前策略的轨迹

            policy_trajectories = self.generate_trajectories(

                simple_policy, None, deterministic=False

            )



            # 更新权重

            self.update(expert_trajectories, policy_trajectories)



            if iteration % 20 == 0:

                expert_features = self.compute_feature_expectation(expert_trajectories)

                policy_features = self.compute_feature_expectation(policy_trajectories)

                diff = np.linalg.norm(expert_features - policy_features)

                print(f"Iter {iteration}: feature_diff={diff:.4f}, "

                      f"weights_mean={np.mean(self.weights):.4f}")



        print("MaxEnt IRL 训练完成!")





class GAIL:

    """

    生成对抗模仿学习（Generative Adversarial Imitation Learning）



    GAIL 使用 GAN 的思想：

    - Generator（生成器）：策略网络，生成状态-动作对

    - Discriminator（判别器）：判断样本来自专家还是策略



    判别器目标：最大化 D(expert) + (1 - D(generator))

    生成器目标：最小化 -log(D(generator))



    等价于学习一个隐式的奖励函数。

    """



    def __init__(self, state_dim, action_dim, hidden_dim=64,

                 d_lr=0.001, g_lr=0.001, gamma=0.99,

                 n_disc_updates=5):

        """

        初始化 GAIL



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

            d_lr: 判别器学习率

            g_lr: 生成器（策略）学习率

            gamma: 折扣因子

            n_disc_updates: 每步判别器更新次数

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.gamma = gamma



        # 判别器网络

        self.discriminator = self._build_discriminator(hidden_dim)



        # 策略网络（生成器）

        self.policy = self._build_policy(hidden_dim)



        self.d_lr = d_lr

        self.g_lr = g_lr

        self.n_disc_updates = n_disc_updates



    def _build_discriminator(self, hidden_dim):

        """构建判别器网络"""

        np.random.seed(42)

        return {

            'w1': np.random.randn(self.state_dim + self.action_dim, hidden_dim) * 0.1,

            'b1': np.zeros(hidden_dim),

            'w2': np.random.randn(hidden_dim, 1) * 0.1,

            'b2': np.zeros(1)

        }



    def _build_policy(self, hidden_dim):

        """构建策略网络"""

        np.random.seed(123)

        return {

            'w1': np.random.randn(self.state_dim, hidden_dim) * 0.1,

            'b1': np.zeros(hidden_dim),

            'w_mean': np.random.randn(hidden_dim, self.action_dim) * 0.01,

            'b_mean': np.zeros(self.action_dim),

            'log_std': np.zeros(self.action_dim)

        }



    def _forward_disc(self, state_action, network):

        """判别器前向"""

        h = np.maximum(0, np.dot(state_action, network['w1']) + network['b1'])

        logit = np.dot(h, network['w2']) + network['b2']

        # Sigmoid 概率

        prob = 1.0 / (1.0 + np.exp(-logit))

        return prob.squeeze()



    def _forward_policy(self, state, network):

        """策略前向"""

        h = np.maximum(0, np.dot(state, network['w1']) + network['b1'])

        mean = np.dot(h, network['w_mean']) + network['b_mean']

        std = np.exp(network['log_std'])

        return mean, std



    def get_action(self, state):

        """采样动作"""

        mean, std = self._forward_policy(state, self.policy)

        action = mean + std * np.random.randn(self.action_dim)

        return action



    def compute_rewards(self, states, actions):

        """

        计算 GAIL 隐式奖励（来自判别器）



        参数:

            states: 状态序列

            actions: 动作序列

        返回:

            rewards: 奖励序列

        """

        rewards = []

        for s, a in zip(states, actions):

            sa = np.concatenate([s, a.reshape(-1)])

            prob = self._forward_disc(sa, self.discriminator)

            # 奖励 = -log(1 - D) 类似 GAN 的生成器损失

            reward = -np.log(1 - prob + 1e-8)

            rewards.append(reward)

        return np.array(rewards)



    def update_discriminator(self, expert_samples, policy_samples):

        """

        更新判别器



        参数:

            expert_samples: 专家样本列表 [(state, action), ...]

            policy_samples: 策略样本列表

        """

        # 准备数据

        expert_sa = np.array([np.concatenate([s, a]) for s, a in expert_samples])

        policy_sa = np.array([np.concatenate([s, a]) for s, a in policy_samples])



        n_e = len(expert_sa)

        n_p = len(policy_sa)



        # 判别器输出

        d_expert = self._forward_disc(expert_sa, self.discriminator)

        d_policy = self._forward_disc(policy_sa, self.discriminator)



        # 交叉熵损失

        loss_e = -np.mean(np.log(d_expert + 1e-8))

        loss_p = -np.mean(np.log(1 - d_policy + 1e-8))

        loss = loss_e + loss_p



        # 简化的梯度更新（实际应用中需要反向传播）

        grad_scale = 0.001

        for k in self.discriminator:

            self.discriminator[k] -= grad_scale * np.random.randn(

                *self.discriminator[k].shape) * loss



        return loss



    def update_policy(self, states, actions, advantages):

        """

        更新策略（简化的策略梯度）



        参数:

            states: 状态批次

            actions: 动作批次

            advantages: 优势估计

        """

        # 简化的更新：增加高奖励动作的概率

        grad_scale = 0.001

        for k in self.policy:

            grad = np.random.randn(*self.policy[k].shape) * advantages.mean()

            self.policy[k] += grad_scale * grad



    def train_step(self, expert_trajectories):

        """

        单步训练



        参数:

            expert_trajectories: 专家轨迹

        """

        # 生成策略样本

        policy_samples = []

        for _ in range(len(expert_trajectories)):

            state = np.random.randn(self.state_dim)

            for _ in range(20):

                action = self.get_action(state)

                policy_samples.append((state.copy(), action.copy()))

                # 简化的环境转移

                state = state + 0.1 * action + np.random.randn(self.state_dim) * 0.1



        # 更新判别器

        for _ in range(self.n_disc_updates):

            d_loss = self.update_discriminator(expert_trajectories, policy_samples)



        # 计算 GAIL 奖励

        states = [s for s, a in policy_samples]

        actions = [a for s, a in policy_samples]

        gail_rewards = self.compute_rewards(states, actions)



        # 更新策略

        advantages = gail_rewards

        self.update_policy(states, actions, advantages)



        return d_loss





if __name__ == "__main__":

    # 测试 MaxEnt IRL

    print("=== MaxEnt IRL 测试 ===")



    state_dim = 4

    action_dim = 2

    feature_dim = 8



    irl = MaxEntIRL(state_dim, action_dim, feature_dim)



    # 生成"专家"轨迹（基于真实奖励）

    class ExpertEnv:

        def step(self, state, action):

            return state + 0.1 * np.eye(action_dim)[action % action_dim] + \

                   np.random.randn(state_dim) * 0.05



    expert_env = ExpertEnv()



    def expert_policy(state):

        """专家策略（简化为向原点移动）"""

        return 0 if state[0] > 0 else 1



    expert_trajectories = []

    for _ in range(10):

        state = np.array([1.0, 0.0, 0.0, 0.0])

        traj = {'states': [], 'actions': [], 'rewards': []}

        for _ in range(30):

            action = expert_policy(state)

            traj['states'].append(state.copy())

            traj['actions'].append(action)

            state = state + 0.1 * np.eye(action_dim)[action] + \

                    np.random.randn(state_dim) * 0.05

            traj['rewards'].append(-np.sum(state ** 2))

        expert_trajectories.append(traj)



    irl.train(expert_trajectories, n_iterations=50)



    # 测试 GAIL

    print("\n=== GAIL 测试 ===")



    gail = GAIL(state_dim, action_dim)



    # 转换为 GAIL 格式的专家样本

    expert_samples = []

    for traj in expert_trajectories:

        for s, a in zip(traj['states'], traj['actions']):

            a_vec = np.eye(action_dim)[a]

            expert_samples.append((s.copy(), a_vec.copy()))



    for step in range(20):

        d_loss = gail.train_step(expert_samples)

        if step % 5 == 0:

            print(f"GAIL Step {step+1}: d_loss={d_loss:.4f}")



    print("\n逆向强化学习测试完成!")

