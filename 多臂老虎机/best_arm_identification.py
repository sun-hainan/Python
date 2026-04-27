# -*- coding: utf-8 -*-

"""

算法实现：多臂老虎机 / best_arm_identification



本文件实现 best_arm_identification 相关的算法功能。

"""



import numpy as np

import torch

import math

from typing import List, Tuple, Optional, Dict

from dataclasses import dataclass





@dataclass

class ArmStats:

    """臂的统计信息"""

    sum_rewards: float = 0.0

    count: int = 0



    @property

    def mean(self) -> float:

        return self.sum_rewards / self.count if self.count > 0 else 0.0





class SuccessiveRejects:

    """

    Successive Rejects算法



    固定预算下的最佳臂识别

    参考文献：AUDER et al. "Best Arm Identification in Multi-Armed Bandits" (NIPS 2011)

    """



    def __init__(self, num_arms: int, budget: int, device: str = 'cpu'):

        """

        参数:

            budget: 总采样预算

            device: 计算设备

        """

        self.num_arms = num_arms

        self.budget = budget

        self.device = device



        self.arm_stats = [ArmStats() for _ in range(num_arms)]

        self.active_arms = set(range(num_arms))



        # 计算每个阶段的预算

        self.log_k = [1 / (i + 1) for i in range(num_arms - 1)]

        self.log_k_sum = sum(self.log_k)



        self.stage_budgets = [

            int(budget * log_i / self.log_k_sum)

            for log_i in self.log_k

        ]



        self.current_stage = 0

        self.stage_pulls = 0



    def select_arm(self) -> int:

        """选择臂"""

        if not self.active_arms:

            return -1



        # 当前阶段：对所有活跃臂均匀采样

        active_list = list(self.active_arms)

        return active_list[self.stage_pulls % len(active_list)]



    def update(self, arm: int, reward: float):

        """更新统计"""

        self.arm_stats[arm].sum_rewards += reward

        self.arm_stats[arm].count += 1

        self.stage_pulls += 1



        # 检查是否需要进入下一阶段

        if self._should_advance_stage():

            self._advance_stage()



    def _should_advance_stage(self) -> bool:

        """判断是否应进入下一阶段"""

        return self.stage_pulls >= self.stage_budgets[min(self.current_stage, len(self.stage_budgets) - 1)]



    def _advance_stage(self):

        """进入下一阶段，淘汰最差臂"""

        self.current_stage += 1

        self.stage_pulls = 0



        if len(self.active_arms) <= 1:

            return



        # 找到均值最低的臂

        active_list = list(self.active_arms)

        means = [self.arm_stats[arm].mean for arm in active_list]

        worst_arm = active_list[argmin(means)]



        self.active_arms.remove(worst_arm)



    def get_best_arm(self) -> int:

        """返回识别到的最佳臂"""

        if len(self.active_arms) == 1:

            return list(self.active_arms)[0]



        # 返回均值最高的

        active_list = list(self.active_arms)

        means = [self.arm_stats[arm].mean for arm in active_list]

        return active_list[argmax(means)]





class LUCB:

    """

    LUCB (Lower Upper Confidence Bound) 算法



    固定置信度下的最佳臂识别

    """



    def __init__(self, num_arms: int, epsilon: float = 0.1, delta: float = 0.1, device: str = 'cpu'):

        """

        参数:

            epsilon: 近似误差

            delta: 失败概率

        """

        self.num_arms = num_arms

        self.epsilon = epsilon

        self.delta = delta

        self.device = device



        self.arm_stats = [ArmStats() for _ in range(num_arms)]

        self.total_pulls = 0



    def _compute_ucb(self, arm: int) -> float:

        """计算UCB"""

        stats = self.arm_stats[arm]

        if stats.count == 0:

            return float('inf')



        n = stats.count

        exploration = math.sqrt(2 * math.log(1 / self.delta) / n)

        return stats.mean + exploration



    def _compute_lcb(self, arm: int) -> float:

        """计算LCB"""

        stats = self.arm_stats[arm]

        if stats.count == 0:

            return -float('inf')



        n = stats.count

        exploration = math.sqrt(2 * math.log(1 / self.delta) / n)

        return stats.mean - exploration



    def select_arms(self) -> Tuple[int, int]:

        """

        选择两个臂进行对比



        返回:

            (arm1, arm2): 要对比的两个臂

        """

        self.total_pulls += 1



        # 计算所有臂的UCB

        ucb_values = [self._compute_ucb(arm) for arm in range(self.num_arms)]



        # UCB最高的臂

        top_arm = argmax(ucb_values)



        # 找到LCB与top_arm的UCB差距最大的臂

        top_ucb = ucb_values[top_arm]

        max_gap = -float('inf')

        challenger = -1



        for arm in range(self.num_arms):

            if arm == top_arm:

                continue



            lcb = self._compute_lcb(arm)

            gap = top_ucb - lcb



            if gap > max_gap:

                max_gap = gap

                challenger = arm



        return top_arm, challenger



    def update(self, arm: int, reward: float):

        """更新统计"""

        self.arm_stats[arm].sum_rewards += reward

        self.arm_stats[arm].count += 1



    def is_converged(self) -> bool:

        """检查是否已识别最佳臂"""

        if self.total_pulls < self.num_arms:

            return False



        # 找到当前最好的两个臂

        means = [(arm, self.arm_stats[arm].mean) for arm in range(self.num_arms)]

        means.sort(key=lambda x: x[1], reverse=True)



        best, second = means[0], means[1]



        # 检查差距是否大于epsilon

        best_ucb = self._compute_ucb(best[0])

        second_lcb = self._compute_lcb(second[0])



        return best_ucb - second_lcb <= self.epsilon



    def get_best_arm(self) -> int:

        """获取最佳臂"""

        means = [(arm, self.arm_stats[arm].mean) for arm in range(self.num_arms)]

        return max(means, key=lambda x: x[1])[0]





class FixedBudgetIdentification:

    """

    固定预算最佳臂识别



    在固定采样次数下最大化识别正确率

    """



    def __init__(self, num_arms: int, budget: int, device: str = 'cpu'):

        self.num_arms = num_arms

        self.budget = budget

        self.device = device



        self.arm_stats = [ArmStats() for _ in range(num_arms)]

        self.total_pulls = 0



    def select_arm(self) -> int:

        """选择臂（均匀采样）"""

        arm = self.total_pulls % self.num_arms

        self.total_pulls += 1

        return arm



    def update(self, arm: int, reward: float):

        """更新"""

        self.arm_stats[arm].sum_rewards += reward

        self.arm_stats[arm].count += 1



    def get_best_arm(self) -> int:

        """返回样本均值最高的臂"""

        means = [s.mean for s in self.arm_stats]

        return argmax(means)





class Racing:

    """

    Racing算法



    对每个臂进行多次采样，直到有足够信心淘汰

    """



    def __init__(self, num_arms: int, max_samples: int = 100, confidence: float = 0.95, device: str = 'cpu'):

        self.num_arms = num_arms

        self.max_samples = max_samples

        self.confidence = confidence

        self.device = device



        self.arm_stats = [ArmStats() for _ in range(num_arms)]

        self.active_arms = set(range(num_arms))

        self.eliminated = set()



    def select_arm(self) -> int:

        """选择要采样的臂（优先选择样本少的活跃臂）"""

        if not self.active_arms:

            return -1



        active_list = list(self.active_arms)

        # 选择样本最少的臂

        counts = [(arm, self.arm_stats[arm].count) for arm in active_list]

        counts.sort(key=lambda x: x[1])



        return counts[0][0]



    def update(self, arm: int, reward: float):

        """更新并可能淘汰"""

        self.arm_stats[arm].sum_rewards += reward

        self.arm_stats[arm].count += 1



        # 检查是否应淘汰

        self._check_elimination(arm)



    def _check_elimination(self, arm: int):

        """检查是否应淘汰该臂"""

        if arm not in self.active_arms:

            return



        # 计算与最佳活跃臂的差距

        active_list = list(self.active_arms)

        means = {a: self.arm_stats[a].mean for a in active_list}

        best_arm = max(means, key=means.get)

        best_mean = means[best_arm]



        current_mean = means[arm]

        current_count = self.arm_stats[arm].count



        # 简单淘汰规则：如果当前臂的均值低于最佳臂超过阈值

        if best_mean - current_mean > 0.1 and current_count >= 10:

            self.active_arms.remove(arm)

            self.eliminated.add(arm)



    def get_best_arm(self) -> int:

        """获取最佳臂"""

        if len(self.active_arms) == 1:

            return list(self.active_arms)[0]



        active_list = list(self.active_arms)

        means = [(arm, self.arm_stats[arm].mean) for arm in active_list]

        return max(means, key=lambda x: x[1])[0]





def argmax(values: List[float]) -> int:

    """返回最大值的索引"""

    return max(range(len(values)), key=lambda i: values[i])





def argmin(values: List[float]) -> int:

    """返回最小值的索引"""

    return min(range(len(values)), key=lambda i: values[i])





def run_best_arm_comparison(num_arms: int = 10, budget: int = 1000,

                            num_trials: int = 100,

                            bandit_probs: Optional[np.ndarray] = None,

                            seed: int = 42):

    """

    最佳臂识别算法比较

    """

    np.random.seed(seed)



    if bandit_probs is None:

        bandit_probs = np.random.rand(num_arms)



    optimal_arm = np.argmax(bandit_probs)



    print(f"真实最优臂: {optimal_arm}, 概率: {bandit_probs[optimal_arm]}")

    print(f"所有概率: {bandit_probs}")



    algorithms = {

        'SuccessiveRejects': SuccessiveRejects(num_arms, budget),

        'FixedBudget': FixedBudgetIdentification(num_arms, budget),

        'Racing': Racing(num_arms, max_samples=budget // num_arms)

    }



    results = {}



    for name, algo in algorithms.items():

        correct = 0



        for trial in range(num_trials):

            # 重置算法

            if name == 'SuccessiveRejects':

                algo = SuccessiveRejects(num_arms, budget)

            elif name == 'FixedBudget':

                algo = FixedBudgetIdentification(num_arms, budget)

            else:

                algo = Racing(num_arms, max_samples=budget // num_arms)



            # 运行算法

            pulls = 0

            while pulls < budget:

                arm = algo.select_arm()

                if arm < 0:

                    break



                reward = 1.0 if np.random.rand() < bandit_probs[arm] else 0.0

                algo.update(arm, reward)

                pulls += 1



            # 检查是否正确识别

            best = algo.get_best_arm()

            if best == optimal_arm:

                correct += 1



        accuracy = correct / num_trials

        results[name] = accuracy

        print(f"{name}: 准确率={accuracy:.2%}")



    return results





if __name__ == "__main__":

    print("=" * 50)

    print("最佳臂识别测试")

    print("=" * 50)



    # 测试

    print("\n--- Successive Rejects ---")

    num_arms = 5

    probs = np.array([0.1, 0.3, 0.5, 0.8, 0.9])



    sr = SuccessiveRejects(num_arms, budget=200)



    for step in range(200):

        arm = sr.select_arm()

        if arm < 0:

            break



        reward = 1.0 if np.random.rand() < probs[arm] else 0.0

        sr.update(arm, reward)



    print(f"识别结果: {sr.get_best_arm()}")

    print(f"真实最优: {np.argmax(probs)}")

    print(f"活跃臂: {sr.active_arms}")



    # 比较

    print("\n--- 算法比较 ---")

    run_best_arm_comparison(num_arms=8, budget=500, num_trials=50)



    print("\n测试完成！")

