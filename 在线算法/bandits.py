# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / bandits



本文件实现 bandits 相关的算法功能。

"""



import random

import numpy as np

from typing import List, Tuple





class MultiArmedBandit:

    """多臂老虎机"""



    def __init__(self, arms: int, epsilon: float = 0.1):

        """

        参数：

            arms: 臂数

            epsilon: 探索概率

        """

        self.arms = arms

        self.epsilon = epsilon



        # 真实奖励概率（隐藏）

        self.true_probs = [random.random() for _ in range(arms)]



        # 估计的奖励

        self.estimates = [0.0] * arms

        self.counts = [0] * arms



    def pull(self, arm: int) -> int:

        """

        拉臂



        参数：

            arm: 臂索引



        返回：奖励（0或1）

        """

        self.counts[arm] += 1



        reward = 1 if random.random() < self.true_probs[arm] else 0



        # 更新估计

        n = self.counts[arm]

        self.estimates[arm] = (self.estimates[arm] * (n - 1) + reward) / n



        return reward



    def epsilon_greedy(self, n_steps: int) -> Tuple[List[int], float]:

        """

        Epsilon-Greedy算法



        参数：

            n_steps: 步数



        返回：(选择的臂序列, 总奖励)

        """

        choices = []

        total_reward = 0



        for _ in range(n_steps):

            if random.random() < self.epsilon:

                # 探索

                arm = random.randint(0, self.arms - 1)

            else:

                # 利用

                arm = int(np.argmax(self.estimates))



            reward = self.pull(arm)

            choices.append(arm)

            total_reward += reward



        return choices, total_reward



    def ucb(self, n_steps: int, c: float = 2.0) -> Tuple[List[int], float]:

        """

        UCB算法



        参数：

            n_steps: 步数

            c: 置信度参数



        返回：(选择的臂序列, 总奖励)

        """

        choices = []

        total_reward = 0



        for t in range(n_steps):

            # UCB公式

            ucb_values = []

            for arm in range(self.arms):

                if self.counts[arm] == 0:

                    ucb_values.append(float('inf'))

                else:

                    bonus = c * np.sqrt(np.log(t) / self.counts[arm])

                    ucb_values.append(self.estimates[arm] + bonus)



            arm = int(np.argmax(ucb_values))



            reward = self.pull(arm)

            choices.append(arm)

            total_reward += reward



        return choices, total_reward





def bandit_analysis():

    """Bandit分析"""

    print("=== Bandit分析 ===")

    print()

    print("Epsilon-Greedy：")

    print("  - 简单但有效")

    print("  - 需要调参 epsilon")

    print()

    print("UCB：")

    print("  - 无需调参")

    print("  - 有理论保证")

    print()

    print("Thompson Sampling：")

    print("  - 贝叶斯方法")

    print("  - 通常最好")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 多臂老虎机测试 ===\n")



    random.seed(42)



    # 创建老虎机

    bandit = MultiArmedBandit(arms=5, epsilon=0.1)



    print(f"臂数: 5")

    print(f"真实奖励概率: {[f'{p:.2f}' for p in bandit.true_probs]}")

    print()



    # Epsilon-Greedy

    n_steps = 1000

    choices_eps, reward_eps = bandit.epsilon_greedy(n_steps)



    print(f"Epsilon-Greedy (ε=0.1):")

    print(f"  总奖励: {reward_eps}")

    print(f"  平均奖励: {reward_eps / n_steps:.4f}")



    # 重置并用UCB

    bandit2 = MultiArmedBandit(arms=5)

    choices_ucb, reward_ucb = bandit2.ucb(n_steps)



    print(f"\nUCB:")

    print(f"  总奖励: {reward_ucb}")

    print(f"  平均奖励: {reward_ucb / n_steps:.4f}")



    print()

    bandit_analysis()



    print()

    print("说明：")

    print("  - Bandit是在线学习的经典问题")

    print("  - 探索-利用权衡是核心")

    print("  - 应用于推荐系统、广告投放")

