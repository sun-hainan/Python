# -*- coding: utf-8 -*-

"""

算法实现：多臂老虎机 / epsilon_greedy



本文件实现 epsilon_greedy 相关的算法功能。

"""



import numpy as np

import torch

from typing import List, Dict, Tuple

import random





class EpsilonGreedy:

    """

    标准Epsilon-Greedy算法



    每次以概率ε随机选择一个臂，以概率1-ε选择当前估计最优的臂

    """



    def __init__(self, num_arms, epsilon=0.1, device='cpu'):

        """

        参数:

            num_arms: 臂的数量

            epsilon: 探索概率

            device: 计算设备

        """

        self.num_arms = num_arms

        self.epsilon = epsilon

        self.device = device



        # Q值估计

        self.Q = torch.zeros(num_arms, device=device)

        # 每个臂被选择的次数

        self.counts = torch.zeros(num_arms, device=device)

        # 总奖励

        self.rewards = torch.zeros(num_arms, device=device)



    def select_arm(self):

        """

        选择臂



        返回:

            arm: 选择的臂索引

        """

        if random.random() < self.epsilon:

            # 探索：随机选择

            return random.randint(0, self.num_arms - 1)

        else:

            # 利用：选择当前最优

            return torch.argmax(self.Q).item()



    def update(self, arm, reward):

        """

        更新Q值



        参数:

            arm: 被选择的臂索引

            reward: 获得的奖励

        """

        self.counts[arm] += 1

        self.rewards[arm] += reward



        # 增量更新：Q(a) = Q(a) + (r - Q(a)) / N(a)

        self.Q[arm] += (reward - self.Q[arm]) / self.counts[arm]



    def get_estimated_values(self):

        """获取估计值"""

        return self.Q.cpu().numpy()





class DecayingEpsilonGreedy:

    """

    衰减Epsilon-Greedy



    探索率随时间逐渐衰减

    """



    def __init__(self, num_arms, initial_epsilon=1.0, min_epsilon=0.01, decay_rate=0.995, device='cpu'):

        """

        参数:

            initial_epsilon: 初始探索率

            min_epsilon: 最小探索率

            decay_rate: 衰减率

        """

        self.num_arms = num_arms

        self.epsilon = initial_epsilon

        self.min_epsilon = min_epsilon

        self.decay_rate = decay_rate

        self.device = device



        self.Q = torch.zeros(num_arms, device=device)

        self.counts = torch.zeros(num_arms, device=device)

        self.total_steps = 0



    def select_arm(self):

        """选择臂（带衰减的epsilon）"""

        if random.random() < self.epsilon:

            return random.randint(0, self.num_arms - 1)

        else:

            return torch.argmax(self.Q).item()



    def update(self, arm, reward):

        """更新并衰减epsilon"""

        self.counts[arm] += 1

        self.total_steps += 1



        # 增量更新

        self.Q[arm] += (reward - self.Q[arm]) / self.counts[arm]



        # 衰减epsilon

        self.epsilon = max(self.min_epsilon, self.epsilon * self.decay_rate)



    def get_current_epsilon(self):

        """获取当前epsilon值"""

        return self.epsilon





class SoftmaxExplorer:

    """

    Softmax探索策略



    基于Gibbs/Boltzmann分布选择臂

    """



    def __init__(self, num_arms, temperature=1.0, device='cpu'):

        """

        参数:

            temperature: 温度参数（高温度=更均匀，低温度=更贪婪）

        """

        self.num_arms = num_arms

        self.temperature = temperature

        self.device = device



        self.Q = torch.zeros(num_arms, device=device)

        self.counts = torch.zeros(num_arms, device=device)



    def select_arm(self):

        """基于softmax选择臂"""

        # 计算概率

        exp_q = torch.exp(self.Q / self.temperature)

        probs = exp_q / exp_q.sum()



        # 采样

        return torch.multinomial(probs, 1).item()



    def update(self, arm, reward):

        """更新Q值"""

        self.counts[arm] += 1

        self.Q[arm] += (reward - self.Q[arm]) / self.counts[arm]





class UCB1Tuned:

    """

    UCB-Tuned算法



    使用方差估计来调整上界

    """



    def __init__(self, num_arms, c=2.0, device='cpu'):

        """

        参数:

            c: 探索常数

        """

        self.num_arms = num_arms

        self.c = c

        self.device = device



        self.Q = torch.zeros(num_arms, device=device)

        self.counts = torch.zeros(num_arms, device=device)

        self.rewards = torch.zeros(num_arms, device=device)

        self.squared_rewards = torch.zeros(num_arms, device=device)

        self.total_counts = 0



    def select_arm(self):

        """选择臂"""

        # 确保每个臂都被选择过

        if self.total_counts < self.num_arms:

            return self.total_counts



        # 计算UCB

        avg_rewards = self.Q

        ucb_values = torch.zeros(self.num_arms, device=self.device)



        for arm in range(self.num_arms):

            if self.counts[arm] > 0:

                # UCB-Tuned公式

                avg = avg_rewards[arm]

                var_est = (self.squared_rewards[arm] / self.counts[arm]) - (avg ** 2)

                variance = avg + var_est + np.sqrt(2 * np.log(self.total_counts) / self.counts[arm])

                ucb_values[arm] = variance



        return torch.argmax(ucb_values).item()



    def update(self, arm, reward):

        """更新统计"""

        self.counts[arm] += 1

        self.total_counts += 1



        self.rewards[arm] += reward

        self.squared_rewards[arm] += reward ** 2



        self.Q[arm] = self.rewards[arm] / self.counts[arm]





class ThompsonSampling:

    """

    Thompson Sampling（贝叶斯方法）



    使用Beta分布进行探索

    """



    def __init__(self, num_arms, prior_alpha=1.0, prior_beta=1.0, device='cpu'):

        """

        参数:

            prior_alpha: Beta分布alpha参数（成功次数+1）

            prior_beta: Beta分布beta参数（失败次数+1）

        """

        self.num_arms = num_arms

        self.device = device



        # Beta分布参数

        self.alpha = torch.full((num_arms,), prior_alpha, device=device)

        self.beta = torch.full((num_arms,), prior_beta, device=device)



    def select_arm(self):

        """从后验分布采样并选择"""

        # 从Beta分布采样

        samples = torch.distributions.Beta(self.alpha, self.beta).sample()

        return torch.argmax(samples).item()



    def update(self, arm, reward):

        """更新Beta分布参数"""

        # 成功：alpha + 1

        # 失败：beta + 1

        self.alpha[arm] += reward

        self.beta[arm] += (1 - reward)



    def get_posterior_means(self):

        """获取后验均值"""

        return self.alpha / (self.alpha + self.beta)





def run_bandit_simulation(num_arms=10, num_steps=1000, bandit_probs=None, epsilon=0.1):

    """

    运行老虎机模拟



    参数:

        num_arms: 臂数

        num_steps: 步数

        bandit_probs: 每个臂的真实成功概率

        epsilon: 探索率



    返回:

        results: 模拟结果

    """

    if bandit_probs is None:

        bandit_probs = np.random.rand(num_arms)



    device = torch.device("cpu")

    agent = EpsilonGreedy(num_arms, epsilon=epsilon, device=device)



    total_reward = 0

    cumulative_rewards = []

    regrets = []



    # 最优臂的概率

    optimal_prob = max(bandit_probs)



    for step in range(num_steps):

        # 选择臂

        arm = agent.select_arm()



        # 生成奖励（伯努利老虎机）

        reward = 1.0 if random.random() < bandit_probs[arm] else 0.0



        # 更新

        agent.update(arm, reward)



        total_reward += reward

        cumulative_rewards.append(total_reward)



        # 计算遗憾

        expected_optimal = optimal_prob * (step + 1)

        regret = expected_optimal - total_reward

        regrets.append(regret)



    return {

        'total_reward': total_reward,

        'cumulative_rewards': cumulative_rewards,

        'regrets': regrets,

        'estimated_values': agent.get_estimated_values(),

        'true_probs': bandit_probs,

        'counts': agent.counts.cpu().numpy()

    }





if __name__ == "__main__":

    print("=" * 50)

    print("Epsilon-Greedy算法测试")

    print("=" * 50)



    # 运行模拟

    np.random.seed(42)

    random.seed(42)



    # 随机生成老虎机概率

    num_arms = 5

    true_probs = np.random.rand(num_arms)



    print(f"\n真实概率: {true_probs}")



    # 标准Epsilon-Greedy

    print("\n--- 标准 Epsilon-Greedy (ε=0.1) ---")

    results = run_bandit_simulation(num_arms=num_arms, num_steps=500,

                                   bandit_probs=true_probs, epsilon=0.1)

    print(f"总奖励: {results['total_reward']}")

    print(f"估计值: {results['estimated_values']}")

    print(f"选择次数: {results['counts']}")



    # 衰减Epsilon-Greedy

    print("\n--- 衰减 Epsilon-Greedy ---")

    agent = DecayingEpsilonGreedy(num_arms, initial_epsilon=1.0, min_epsilon=0.01, decay_rate=0.995)



    for step in range(100):

        arm = agent.select_arm()

        reward = 1.0 if random.random() < true_probs[arm] else 0.0

        agent.update(arm, reward)



    print(f"最终epsilon: {agent.get_current_epsilon():.4f}")

    print(f"估计值: {agent.get_estimated_values()}")



    # Thompson Sampling

    print("\n--- Thompson Sampling ---")

    thompson = ThompsonSampling(num_arms)



    for step in range(100):

        arm = thompson.select_arm()

        reward = 1.0 if random.random() < true_probs[arm] else 0.0

        thompson.update(arm, reward)



    print(f"后验均值: {thompson.get_posterior_means().cpu().numpy()}")

    print(f"真实概率: {true_probs}")



    print("\n测试完成！")

