# -*- coding: utf-8 -*-

"""

算法实现：多臂老虎机 / pac_analysis



本文件实现 pac_analysis 相关的算法功能。

"""



import numpy as np

import torch

import math

from typing import List, Optional, Tuple





class PACAnalysis:

    """

    PAC分析基类

    """



    def __init__(self, num_arms: int, delta: float = 0.1, device: str = 'cpu'):

        """

        参数:

            num_arms: 臂数量

            delta: 失败概率 (1-delta的置信度)

            device: 计算设备

        """

        self.num_arms = num_arms

        self.delta = delta

        self.device = device



    def sample_complexity_bound(self, epsilon: float) -> float:

        """

        计算达到epsilon-近似所需的样本复杂度上界



        参数:

            epsilon: 近似误差



        返回:

            样本复杂度

        """

        raise NotImplementedError





class MOSSBandit:

    """

    MOSS (Minimax Optimal Strategy in the Stochastic regime)



    PAC可证的有限时间遗憾度最优算法

    """



    def __init__(self, num_arms: int, horizon: int, delta: float = 0.1, device: str = 'cpu'):

        """

        参数:

            horizon: 时间范围T

            delta: 失败概率

        """

        self.num_arms = num_arms

        self.horizon = horizon

        self.delta = delta

        self.device = device



        self.Q = torch.zeros(num_arms, device=device)

        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

        self.total_counts = 0



    def select_arm(self) -> int:

        """选择臂"""

        if self.total_counts < self.num_arms:

            return self.total_counts



        # MOSS UCB

        ucb_values = torch.zeros(self.num_arms, device=self.device)



        for arm in range(self.num_arms):

            if self.counts[arm] > 0:

                log_term = math.log(self.horizon / self.num_arms)

                exploration = math.sqrt(log_term / self.counts[arm])

                ucb_values[arm] = self.Q[arm] + exploration



        return torch.argmax(ucb_values).item()



    def update(self, arm: int, reward: float):

        """更新"""

        self.counts[arm] += 1

        self.total_counts += 1



        n = self.counts[arm]

        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n



    def sample_complexity(self, epsilon: float) -> int:

        """

        PAC样本复杂度



        返回: 在1-delta置信度下达到epsilon-最优所需的样本数

        """

        # MOSS的样本复杂度

        C = 8 * self.num_arms * math.log(self.horizon / self.delta) / (epsilon ** 2)

        return int(C)





class MOSSCHBandit:

    """

    MOSS-CH (MOSS with Confidence Halving)



    使用置信减半来加速探索

    """



    def __init__(self, num_arms: int, horizon: int, delta: float = 0.1, device: str = 'cpu'):

        self.num_arms = num_arms

        self.horizon = horizon

        self.delta = delta

        self.device = device



        self.Q = torch.zeros(num_arms, device=device)

        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

        self.confidence = torch.ones(num_arms, device=device)  # 置信半径

        self.total_counts = 0



    def select_arm(self) -> int:

        """选择臂"""

        if self.total_counts < self.num_arms:

            return self.total_counts



        # 选择置信区间上界最大的臂

        upper_bounds = self.Q + self.confidence



        return torch.argmax(upper_bounds).item()



    def update(self, arm: int, reward: float):

        """更新"""

        self.counts[arm] += 1

        self.total_counts += 1



        n = self.counts[arm]

        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n



        # 更新置信半径（减半）

        self.confidence[arm] = min(self.confidence[arm], 2 * math.sqrt(

            math.log(self.horizon * self.num_arms / self.delta) / n

        ))





class UCBAnalysis(PACAnalysis):

    """

    UCB的PAC分析

    """



    def __init__(self, num_arms: int, delta: float = 0.1, device: str = 'cpu'):

        super().__init__(num_arms, delta, device)

        self.Q = torch.zeros(num_arms, device=device)

        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

        self.total_counts = 0



    def select_arm(self) -> int:

        """选择臂"""

        if self.total_counts < self.num_arms:

            return self.total_counts



        ucb_values = torch.zeros(self.num_arms, device=self.device)



        for arm in range(self.num_arms):

            if self.counts[arm] > 0:

                exploration = math.sqrt(

                    2 * math.log(1 / self.delta) / self.counts[arm]

                )

                ucb_values[arm] = self.Q[arm] + exploration



        return torch.argmax(ucb_values).item()



    def update(self, arm: int, reward: float):

        """更新"""

        self.counts[arm] += 1

        self.total_counts += 1



        n = self.counts[arm]

        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n



    def sample_complexity_bound(self, epsilon: float) -> float:

        """

        UCB的PAC样本复杂度界



        O((K/epsilon^2) * log(1/delta))

        """

        return (self.num_arms * math.log(1 / self.delta)) / (epsilon ** 2)





class ETC(Explore-Then-Commit):

    """

    ETC (Explore-Then-Commit)



    简单的PAC算法：先均匀探索，再贪婪选择

    """



    def __init__(self, num_arms: int, explore_samples: int, delta: float = 0.1, device: str = 'cpu'):

        """

        参数:

            explore_samples: 每个臂的探索次数

        """

        self.num_arms = num_arms

        self.explore_samples = explore_samples

        self.delta = delta

        self.device = device



        self.Q = torch.zeros(num_arms, device=device)

        self.counts = torch.zeros(num_arms, device=device, dtype=torch.long)

        self.total_counts = 0

        self.explored = torch.zeros(num_arms, device=device, dtype=torch.bool)



    def select_arm(self) -> int:

        """选择臂"""

        # 探索阶段

        if not self.explored.all():

            # 选择未充分探索的臂

            for arm in range(self.num_arms):

                if self.counts[arm] < self.explore_samples:

                    return arm



        # 承诺阶段

        return torch.argmax(self.Q).item()



    def update(self, arm: int, reward: float):

        """更新"""

        self.counts[arm] += 1

        self.total_counts += 1



        n = self.counts[arm]

        self.Q[arm] = self.Q[arm] + (reward - self.Q[arm]) / n



        if self.counts[arm] >= self.explore_samples:

            self.explored[arm] = True



    def sample_complexity_bound(self, epsilon: float) -> int:

        """

        ETC的样本复杂度



        m + K * log(1/delta) / (2 * epsilon^2)

        """

        m = self.explore_samples

        return m + int(self.num_arms * math.log(1 / self.delta) / (2 * epsilon ** 2))





def compute_regret(rewards: List[float], optimal_reward: float) -> float:

    """

    计算总遗憾



    遗憾 = 最优累计奖励 - 实际累计奖励

    """

    return optimal_reward - sum(rewards)





def run_pac_comparison(num_arms: int = 5, horizon: int = 1000,

                      bandit_probs: Optional[np.ndarray] = None, seed: int = 42):

    """

    比较PAC算法的性能

    """

    np.random.seed(seed)



    if bandit_probs is None:

        bandit_probs = np.random.rand(num_arms)



    optimal_prob = max(bandit_probs)



    print(f"真实概率: {bandit_probs}")

    print(f"最优概率: {optimal_prob}")



    results = {}



    # MOSS

    moss = MOSSBandit(num_arms, horizon, delta=0.1)

    moss_rewards = []



    for step in range(horizon):

        arm = moss.select_arm()

        reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0

        moss.update(arm, reward)

        moss_rewards.append(reward)



    moss_regret = optimal_prob * horizon - sum(moss_rewards)

    results['MOSS'] = {

        'total_reward': sum(moss_rewards),

        'regret': moss_regret

    }



    # MOSS-CH

    moss_ch = MOSSCHBandit(num_arms, horizon, delta=0.1)

    moss_ch_rewards = []



    for step in range(horizon):

        arm = moss_ch.select_arm()

        reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0

        moss_ch.update(arm, reward)

        moss_ch_rewards.append(reward)



    moss_ch_regret = optimal_prob * horizon - sum(moss_ch_rewards)

    results['MOSS-CH'] = {

        'total_reward': sum(moss_ch_rewards),

        'regret': moss_ch_regret

    }



    # ETC

    explore_m = int(math.sqrt(horizon))

    etc = ETC(num_arms, explore_m, delta=0.1)

    etc_rewards = []



    for step in range(horizon):

        arm = etc.select_arm()

        reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0

        etc.update(arm, reward)

        etc_rewards.append(reward)



    etc_regret = optimal_prob * horizon - sum(etc_rewards)

    results['ETC'] = {

        'total_reward': sum(etc_rewards),

        'regret': etc_regret

    }



    # 打印结果

    print("\n--- PAC算法比较 ---")

    for name, result in results.items():

        print(f"{name}: 奖励={result['total_reward']}, 遗憾={result['regret']:.2f}")



    # PAC样本复杂度

    epsilon = 0.1

    print(f"\n--- PAC样本复杂度 (epsilon={epsilon}) ---")

    for name, algo in [('MOSS', moss), ('UCB', UCBAnalysis(num_arms))]:

        if hasattr(algo, 'sample_complexity'):

            complexity = algo.sample_complexity(epsilon)

        else:

            complexity = algo.sample_complexity_bound(epsilon)

        print(f"{name}: {complexity}")



    return results





if __name__ == "__main__":

    print("=" * 50)

    print("PAC分析测试（MOSS/MOSS-CH）")

    print("=" * 50)



    run_pac_comparison(num_arms=5, horizon=1000)



    print("\n测试完成！")

