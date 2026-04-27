# -*- coding: utf-8 -*-

"""

算法实现：多臂老虎机 / bandit_benchmark



本文件实现 bandit_benchmark 相关的算法功能。

"""



import numpy as np

import torch

from typing import List, Dict, Callable

import time





class BanditBenchmark:

    """

    老虎机算法基准测试

    """



    def __init__(self, name: str, num_arms: int, reward_generator: Callable):

        """

        参数:

            name: 算法名称

            num_arms: 臂数量

            reward_generator: 生成奖励的函数 reward(arm) -> float

        """

        self.name = name

        self.num_arms = num_arms

        self.reward_generator = reward_generator



    def run(self, horizon: int, seed: int = None) -> Dict:

        """

        运行算法



        返回:

            results: 包含总奖励、遗憾等

        """

        raise NotImplementedError





class EpsilonGreedyBenchmark(BanditBenchmark):

    """Epsilon-Greedy基准"""



    def __init__(self, num_arms: int, epsilon: float = 0.1):

        super().__init__(f"epsilon-greedy-{epsilon}", num_arms, None)

        self.epsilon = epsilon

        self.Q = np.zeros(num_arms)

        self.counts = np.zeros(num_arms)



    def run(self, horizon: int, seed: int = None) -> Dict:

        if seed is not None:

            np.random.seed(seed)



        total_reward = 0

        cumulative_rewards = []



        for _ in range(horizon):

            # 选择臂

            if np.random.rand() < self.epsilon:

                arm = np.random.randint(self.num_arms)

            else:

                arm = np.argmax(self.Q)



            # 获取奖励

            reward = self.reward_generator(arm)



            # 更新

            self.counts[arm] += 1

            self.Q[arm] += (reward - self.Q[arm]) / self.counts[arm]



            total_reward += reward

            cumulative_rewards.append(total_reward)



        return {

            'name': self.name,

            'total_reward': total_reward,

            'cumulative_rewards': cumulative_rewards,

            'counts': self.counts

        }





class UCB1Benchmark(BanditBenchmark):

    """UCB1基准"""



    def __init__(self, num_arms: int):

        super().__init__("UCB1", num_arms, None)

        self.Q = np.zeros(num_arms)

        self.counts = np.zeros(num_arms, dtype=int)

        self.total_counts = 0



    def run(self, horizon: int, seed: int = None) -> Dict:

        if seed is not None:

            np.random.seed(seed)



        total_reward = 0

        cumulative_rewards = []



        for t in range(horizon):

            # 初始化

            if t < self.num_arms:

                arm = t

            else:

                ucb_values = self.Q + np.sqrt(2 * np.log(t) / (self.counts + 1e-10))

                arm = np.argmax(ucb_values)



            reward = self.reward_generator(arm)



            self.counts[arm] += 1

            self.total_counts += 1

            self.Q[arm] += (reward - self.Q[arm]) / self.counts[arm]



            total_reward += reward

            cumulative_rewards.append(total_reward)



        return {

            'name': self.name,

            'total_reward': total_reward,

            'cumulative_rewards': cumulative_rewards,

            'counts': self.counts

        }





class ThompsonSamplingBenchmark(BanditBenchmark):

    """Thompson Sampling基准"""



    def __init__(self, num_arms: int):

        super().__init__("Thompson", num_arms, None)

        self.alpha = np.ones(num_arms)

        self.beta = np.ones(num_arms)



    def run(self, horizon: int, seed: int = None) -> Dict:

        if seed is not None:

            np.random.seed(seed)



        total_reward = 0

        cumulative_rewards = []



        for _ in range(horizon):

            # 采样

            samples = np.random.beta(self.alpha, self.beta)

            arm = np.argmax(samples)



            reward = self.reward_generator(arm)



            # 更新

            self.alpha[arm] += reward

            self.beta[arm] += (1 - reward)



            total_reward += reward

            cumulative_rewards.append(total_reward)



        return {

            'name': self.name,

            'total_reward': total_reward,

            'cumulative_rewards': cumulative_rewards,

            'alpha': self.alpha,

            'beta': self.beta

        }





def run_benchmark_suite(num_arms: int = 5, horizon: int = 1000,

                        num_trials: int = 10,

                        true_probs: np.ndarray = None) -> Dict:

    """

    运行基准测试套件

    """

    if true_probs is None:

        true_probs = np.random.rand(num_arms)



    def reward_generator(arm):

        return 1.0 if np.random.rand() < true_probs[arm] else 0.0



    algorithms = [

        EpsilonGreedyBenchmark(num_arms, epsilon=0.1),

        EpsilonGreedyBenchmark(num_arms, epsilon=0.01),

        UCB1Benchmark(num_arms),

        ThompsonSamplingBenchmark(num_arms)

    ]



    results = []



    for algo in algorithms:

        algo.reward_generator = reward_generator



        trial_results = []

        for trial in range(num_trials):

            result = algo.run(horizon, seed=trial)

            trial_results.append(result)



        # 汇总

        avg_reward = np.mean([r['total_reward'] for r in trial_results])

        std_reward = np.std([r['total_reward'] for r in trial_results])



        results.append({

            'name': algo.name,

            'avg_reward': avg_reward,

            'std_reward': std_reward,

            'avg_cumulative': np.mean([r['cumulative_rewards'] for r in trial_results], axis=0)

        })



    return {

        'true_probs': true_probs,

        'results': results

    }





def print_benchmark_results(results: Dict):

    """打印基准测试结果"""

    print(f"真实概率: {results['true_probs']}")

    print(f"最优臂: {np.argmax(results['true_probs'])}, 概率: {max(results['true_probs']):.4f}")



    print("\n--- 基准测试结果 ---")

    print(f"{'算法':<20} {'平均奖励':>12} {'标准差':>12}")

    print("-" * 50)



    for result in results['results']:

        print(f"{result['name']:<20} {result['avg_reward']:>12.2f} {result['std_reward']:>12.2f}")





if __name__ == "__main__":

    print("=" * 50)

    print("老虎机算法基准测试")

    print("=" * 50)



    np.random.seed(42)

    true_probs = np.random.rand(5)



    print(f"\n真实概率: {true_probs}")



    results = run_benchmark_suite(

        num_arms=5,

        horizon=500,

        num_trials=5,

        true_probs=true_probs

    )



    print_benchmark_results(results)



    print("\n测试完成！")

