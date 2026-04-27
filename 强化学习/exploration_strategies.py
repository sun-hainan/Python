# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / exploration_strategies



本文件实现 exploration_strategies 相关的算法功能。

"""



import numpy as np

import random

from collections import defaultdict





class EpsilonGreedy:

    """

    Epsilon-Greedy 探索



    最简单的探索策略：以 epsilon 概率随机探索，

    以 1-epsilon 概率贪心选择。

    """



    def __init__(self, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995):

        """

        初始化



        参数:

            epsilon: 初始探索率

            epsilon_min: 最小探索率

            epsilon_decay: 每次衰减率

        """

        self.epsilon = epsilon

        self.epsilon_min = epsilon_min

        self.epsilon_decay = epsilon_decay

        self.initial_epsilon = epsilon



    def select_action(self, q_values):

        """

        选择动作



        参数:

            q_values: 各动作的 Q 值数组

        返回:

            action: 选择的动作索引

        """

        if random.random() < self.epsilon:

            # 探索：随机动作

            return random.randint(0, len(q_values) - 1)

        else:

            # 利用：贪心选择

            return np.argmax(q_values)



    def decay(self):

        """衰减 epsilon"""

        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)



    def reset(self):

        """重置为初始值"""

        self.epsilon = self.initial_epsilon



    def schedule(self, step, total_steps):

        """

        基于步数的时间表衰减



        参数:

            step: 当前步数

            total_steps: 总步数

        """

        self.epsilon = max(self.epsilon_min,

                          self.initial_epsilon * (1 - step / total_steps))





class BoltzmannExploration:

    """

    Boltzmann（Softmax）探索



    使用 softmax 概率选择动作，温度参数控制探索程度：

    - 高温：接近均匀随机

    - 低温：接近贪心

    """



    def __init__(self, temperature=1.0, temperature_min=0.1, tau=1e-4):

        """

        初始化



        参数:

            temperature: 初始温度

            temperature_min: 最小温度

            tau: 温度衰减率

        """

        self.temperature = temperature

        self.temperature_min = temperature_min

        self.tau = tau



    def select_action(self, q_values):

        """

        根据 Boltzmann 分布选择动作



        参数:

            q_values: Q 值数组

        返回:

            action: 选择的动作

        """

        q_values = np.array(q_values, dtype=float)



        # 减去最大值提高数值稳定性

        q_values = q_values - np.max(q_values)



        # 计算指数

        exp_q = np.exp(q_values / self.temperature)

        probs = exp_q / np.sum(exp_q)



        # 按概率采样

        return np.random.choice(len(q_values), p=probs)



    def update_temperature(self):

        """更新温度（指数衰减）"""

        self.temperature = max(self.temperature_min,

                              self.temperature * (1 - self.tau))





class UCB1:

    """

    Upper Confidence Bound (UCB1) 探索



    UCB 平衡探索和利用：

    UCB = Q(a) + c * sqrt(ln(t) / N(a))



    适用于多臂老虎机问题。

    """



    def __init__(self, action_dim, c=2.0):

        """

        初始化 UCB1



        参数:

            action_dim: 动作数量

            c: 探索常数（通常取 2）

        """

        self.action_dim = action_dim

        self.c = c



        # 每个动作的访问次数

        self.N = np.zeros(action_dim)

        # 每个动作的平均奖励

        self.Q = np.zeros(action_dim)

        # 总步数

        self.t = 0



    def select_action(self):

        """

        选择动作



        返回:

            action: 选择的动作索引

        """

        self.t += 1



        # 初始阶段：先尝试所有动作

        if self.t <= self.action_dim:

            action = self.t - 1

        else:

            # UCB 公式

            ucb_values = self.Q + self.c * np.sqrt(np.log(self.t) / self.N)

            action = np.argmax(ucb_values)



        return action



    def update(self, action, reward):

        """

        更新统计量



        参数:

            action: 执行的动作

            reward: 获得的奖励

        """

        self.N[action] += 1

        # 增量更新均值

        self.Q[action] += (reward - self.Q[action]) / self.N[action]





class UCBV:

    """

    UCB-V（方差感知的 UCB）



    UCB-V 使用方差估计来更精确地计算上置信界：

    UCB_V = Q(a) + sqrt(2 * var(a) * ln(t) / N(a)) + 3c * ln(t) / N(a)

    """



    def __init__(self, action_dim, c=2.0):

        self.action_dim = action_dim

        self.c = c

        self.N = np.zeros(action_dim)

        self.Q = np.zeros(action_dim)

        self.sum_sq = np.zeros(action_dim)  # Σ r²

        self.t = 0



    def select_action(self):

        """选择动作"""

        self.t += 1



        if self.t <= self.action_dim:

            return self.t - 1



        # 方差估计

        var = np.maximum(0, self.sum_sq / self.N - self.Q ** 2)



        # UCB-V

        ucb_values = self.Q + np.sqrt(2 * var * np.log(self.t) / self.N) + \

                    3 * self.c * np.log(self.t) / self.N

        return np.argmax(ucb_values)



    def update(self, action, reward):

        """更新统计量"""

        self.N[action] += 1

        self.sum_sq[action] += reward ** 2

        self.Q[action] += (reward - self.Q[action]) / self.N[action]





class ThompsonSampling:

    """

    Thompson Sampling（汤普森采样）



    贝叶斯方法探索：

    1. 对每个动作维护奖励的 Beta/正态分布

    2. 从分布中采样 Q 值

    3. 选择采样值最大的动作

    4. 用观察到的奖励更新分布

    """



    def __init__(self, action_dim, prior='normal', alpha0=1.0, beta0=1.0):

        """

        初始化 Thompson Sampling



        参数:

            action_dim: 动作数量

            prior: 先验分布类型 ('beta' 或 'normal')

            alpha0, beta0: Beta 先验参数

        """

        self.action_dim = action_dim

        self.prior = prior



        if prior == 'beta':

            # Beta-Bernoulli 模型（二元奖励）

            self.alpha = np.ones(action_dim) * alpha0

            self.beta = np.ones(action_dim) * beta0

        else:

            # 正态-正态 模型

            self.mu = np.zeros(action_dim)

            self.sigma_sq = np.ones(action_dim) * 1.0

            self.N = np.zeros(action_dim)



    def select_action(self):

        """选择动作"""

        if self.prior == 'beta':

            # 从 Beta 分布采样

            samples = np.random.beta(self.alpha, self.beta)

        else:

            # 从正态分布采样

            samples = np.random.normal(self.mu, np.sqrt(self.sigma_sq))



        return np.argmax(samples)



    def update(self, action, reward):

        """更新分布"""

        if self.prior == 'beta':

            # 更新 Beta 参数

            if reward > 0:

                self.alpha[action] += 1

            else:

                self.beta[action] += 1

        else:

            # 更新正态参数

            self.N[action] += 1

            old_mu = self.mu[action]

            self.mu[action] += (reward - old_mu) / self.N[action]

            self.sigma_sq[action] = ((self.N[action] - 1) * self.sigma_sq[action] +

                                   (reward - old_mu) * (reward - self.mu[action])) / self.N[action]





class EntropyRegularized:

    """

    熵正则化探索



    在策略优化中加入熵奖励，鼓励探索：

    L = J(π) + β * H(π)



    熵越高，策略越接近均匀分布。

    """



    def __init__(self, action_dim, entropy_coef=0.01):

        """

        初始化



        参数:

            action_dim: 动作维度

            entropy_coef: 熵系数

        """

        self.action_dim = action_dim

        self.entropy_coef = entropy_coef



    def get_action_probs(self, q_values, beta=1.0):

        """

        获取带熵正则化的动作概率



        参数:

            q_values: Q 值

            beta: 温度参数

        返回:

            probs: 动作概率

        """

        q_values = np.array(q_values, dtype=float)

        q_values = q_values - np.max(q_values)  # 数值稳定



        # Softmax

        exp_q = np.exp(q_values / beta)

        probs = exp_q / np.sum(exp_q)



        return probs



    def entropy(self, probs):

        """

        计算熵



        参数:

            probs: 动作概率

        返回:

            H: 熵

        """

        probs = np.clip(probs, 1e-10, 1.0)

        return -np.sum(probs * np.log(probs))



    def select_action(self, q_values):

        """选择动作"""

        probs = self.get_action_probs(q_values)

        return np.random.choice(self.action_dim, p=probs)





class NoisyExcitation:

    """

    噪声激励探索



    通过向 Q 网络或动作添加噪声来探索。

    """



    def __init__(self, action_dim, noise_type='gaussian', sigma=0.1):

        """

        初始化



       参数:

            action_dim: 动作维度

            noise_type: 噪声类型 ('gaussian', 'ou', 'epsilon')

            sigma: 噪声标准差

        """

        self.action_dim = action_dim

        self.noise_type = noise_type

        self.sigma = sigma



        if noise_type == 'ou':

            self.ou_state = np.zeros(action_dim)

            self.ou_theta = 0.15

            self.ou_mu = 0.0



    def add_noise(self, action):

        """

        向动作添加噪声



        参数:

            action: 原始动作

        返回:

            noisy_action: 加噪后的动作

        """

        if self.noise_type == 'gaussian':

            noise = np.random.randn(self.action_dim) * self.sigma

        elif self.noise_type == 'ou':

            dx = self.ou_theta * (self.ou_mu - self.ou_state) + \

                np.random.randn(self.action_dim) * self.sigma

            self.ou_state += dx

            noise = self.ou_state

        else:

            noise = 0



        return action + noise



    def reset(self):

        """重置噪声状态"""

        if self.noise_type == 'ou':

            self.ou_state = np.zeros(self.action_dim)





class IntrinsicCuriosity:

    """

    内在好奇心机制（Intrinsic Curiosity Module）



    ICM 框架：

    - Forward Model: 预测下一个状态

    - Inverse Model: 根据状态预测动作

    - 内在奖励 = 预测误差



    鼓励智能体探索"不可预测"的状态转换。

    """



    def __init__(self, state_dim, action_dim, feature_dim=64,

                 lr=0.001, beta=0.2, eta=0.1):

        """

        初始化 ICM



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            feature_dim: 特征维度

            lr: 学习率

            beta: ICM 损失权重

            eta: 内在奖励权重

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.feature_dim = feature_dim

        self.beta = beta  # inverse model 权重

        self.eta = eta  # 内在奖励权重



        np.random.seed(42)



        # 特征编码器

        self.encoder_weights = {

            'w1': np.random.randn(state_dim, feature_dim) * 0.1,

            'b1': np.zeros(feature_dim)

        }



        # Forward 模型

        self.forward_weights = {

            'w1': np.random.randn(feature_dim + action_dim, feature_dim) * 0.1,

            'b1': np.zeros(feature_dim)

        }



        # Inverse 模型

        self.inverse_weights = {

            'w1': np.random.randn(feature_dim * 2, action_dim) * 0.1,

            'b1': np.zeros(action_dim)

        }



    def encode(self, state):

        """编码状态到特征空间"""

        w = self.encoder_weights

        h = np.tanh(np.dot(state, w['w1']) + w['b1'])

        return h



    def predict_next_feature(self, feature, action):

        """预测下一个状态特征"""

        w = self.forward_weights

        action_onehot = np.zeros(self.action_dim)

        action_onehot[action] = 1.0

        combined = np.concatenate([feature, action_onehot])

        pred = np.tanh(np.dot(combined, w['w1']) + w['b1'])

        return pred



    def predict_action(self, feature1, feature2):

        """根据状态特征预测动作"""

        w = self.inverse_weights

        combined = np.concatenate([feature1, feature2])

        logits = np.dot(combined, w['w1']) + w['b1']

        return logits



    def compute_intrinsic_reward(self, state, action, next_state):

        """

        计算内在奖励



        参数:

            state: 当前状态

            action: 动作

            next_state: 下一个状态

        返回:

            intrinsic_reward: 内在奖励（=预测误差）

        """

        # 编码

        phi1 = self.encode(state)

        phi2 = self.encode(next_state)



        # 预测下一个特征

        phi2_pred = self.predict_next_feature(phi1, action)



        # 内在奖励 = 预测误差（范数）

        intrinsic_reward = self.eta * np.sum((phi2 - phi2_pred) ** 2)



        return intrinsic_reward



    def update(self, state, action, next_state):

        """

        更新 ICM



        返回:

            losses: ICM 各部分损失

        """

        lr = 0.001



        # 编码

        phi1 = self.encode(state)

        phi2 = self.encode(next_state)



        # Forward 预测误差

        phi2_pred = self.predict_next_feature(phi1, action)

        forward_loss = np.sum((phi2 - phi2_pred) ** 2)



        # Inverse 预测动作

        action_logits = self.predict_action(phi1, phi2)

        action_onehot = np.zeros(self.action_dim)

        action_onehot[action] = 1.0

        inverse_loss = -np.sum(action_onehot * action_logits)



        # 总损失（简化的随机更新）

        loss = self.beta * inverse_loss + 0.5 * forward_loss



        # 简化的梯度更新

        grad_scale = lr * loss

        for key in self.encoder_weights:

            self.encoder_weights[key] += grad_scale * np.random.randn(

                *self.encoder_weights[key].shape) * 0.01

        for key in self.forward_weights:

            self.forward_weights[key] += grad_scale * np.random.randn(

                *self.forward_weights[key].shape) * 0.01



        return {'forward_loss': forward_loss, 'inverse_loss': inverse_loss}





class ExplorationScheduler:

    """

    探索策略调度器



    在训练过程中自动切换和调整探索策略。

    """



    def __init__(self, strategy='epsilon_greedy'):

        """

        初始化调度器



        参数:

            strategy: 初始策略

        """

        self.strategy_name = strategy

        self.strategies = {}

        self.current_strategy = None



    def add_strategy(self, name, strategy):

        """添加策略"""

        self.strategies[name] = strategy

        if self.current_strategy is None:

            self.current_strategy = strategy



    def switch_strategy(self, name):

        """切换策略"""

        if name in self.strategies:

            self.current_strategy = self.strategies[name]

            self.strategy_name = name



    def select_action(self, q_values):

        """选择动作"""

        if self.current_strategy is None:

            return np.argmax(q_values)

        return self.current_strategy.select_action(q_values)



    def update(self, *args, **kwargs):

        """更新当前策略"""

        if hasattr(self.current_strategy, 'update'):

            self.current_strategy.update(*args, **kwargs)

        if hasattr(self.current_strategy, 'decay'):

            self.current_strategy.decay()

        if hasattr(self.current_strategy, 'update_temperature'):

            self.current_strategy.update_temperature()





if __name__ == "__main__":

    print("=== 探索策略测试 ===")



    action_dim = 4



    # 1. Epsilon-Greedy

    print("\n1. Epsilon-Greedy")

    eg = EpsilonGreedy(epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.99)

    q = np.array([1.0, 2.0, 0.5, 1.5])



    for step in range(5):

        action = eg.select_action(q)

        print(f"  Step {step+1}: epsilon={eg.epsilon:.4f}, action={action}")

        eg.decay()



    # 2. Boltzmann

    print("\n2. Boltzmann 探索")

    bz = BoltzmannExploration(temperature=2.0, temperature_min=0.1)

    for _ in range(5):

        action = bz.select_action(q)

        print(f"  Temperature={bz.temperature:.4f}, action={action}")

        bz.update_temperature()



    # 3. UCB1

    print("\n3. UCB1")

    ucb = UCB1(action_dim=4, c=2.0)

    rewards = [1.0, 0.0, 1.0, 0.5, 1.5, 2.0, 0.5, 1.0]

    for i, r in enumerate(rewards):

        action = ucb.select_action()

        ucb.update(action, r)

        print(f"  Step {i+1}: action={action}, reward={r}, Q={ucb.Q.round(3)}")



    # 4. Thompson Sampling

    print("\n4. Thompson Sampling")

    ts = ThompsonSampling(action_dim=4, prior='normal')

    for i in range(5):

        action = ts.select_action()

        reward = 1.0 if action == 1 else 0.0

        ts.update(action, reward)

        print(f"  Step {i+1}: action={action}, reward={reward}, μ={ts.mu.round(3)}")



    # 5. 熵正则化

    print("\n5. 熵正则化")

    ent = EntropyRegularized(action_dim=4, entropy_coef=0.01)

    probs = ent.get_action_probs(q, beta=1.0)

    print(f"  动作概率: {probs.round(3)}")

    print(f"  熵: {ent.entropy(probs):.4f}")



    # 6. ICM 内在奖励

    print("\n6. 内在好奇心模块")

    icm = IntrinsicCuriosity(state_dim=4, action_dim=4)

    state = np.random.randn(4)

    action = 1

    next_state = np.random.randn(4)

    intrinsic_reward = icm.compute_intrinsic_reward(state, action, next_state)

    print(f"  内在奖励: {intrinsic_reward:.4f}")



    losses = icm.update(state, action, next_state)

    print(f"  Forward loss: {losses['forward_loss']:.4f}")



    print("\n探索策略测试完成!")

