"""
协同进化算法
==========================================

【原理】
多个种群共同进化，分为合作型和竞争型。

【时间复杂度】O(population_size × species × dim)
【空间复杂度】O(population_size × species × dim)
"""

import random
import numpy as np


class Coevolution:
    """
    协同进化算法

    【两种类型】
    1. 合作协同：多个物种各自适应，共同完成任务
    2. 竞争协同：捕食者-猎物种群相互进化
    """

    def __init__(self, n_species, func, dim, low, high, pop_size=50):
        self.n_species = n_species
        self.func = func
        self.dim = dim
        self.low = low
        self.high = high
        self.pop_size = pop_size

        # 初始化多个种群
        self.populations = [
            np.random.uniform(low, high, (pop_size, dim // n_species))
            for _ in range(n_species)
        ]
        self.best_per_species = [None] * n_species

    def evaluate_cooperative(self):
        """合作评估：组合所有物种的代表"""
        total_fitness = []

        for i in range(self.pop_size):
            # 随机从每个种群选一个组成完整解
            solution = []
            for pop in self.populations:
                idx = random.randint(0, len(pop) - 1)
                solution.extend(pop[idx])

            # 填充到完整维度
            if len(solution) < self.dim:
                solution.extend([0] * (self.dim - len(solution)))

            total_fitness.append(self.func(np.array(solution)))

        return total_fitness

    def evolve_one_step(self):
        """一步进化"""
        for sp in range(self.n_species):
            # 评估当前种群
            fitness = [self.func(ind) for ind in self.populations[sp]]

            # 简单选择：保留前50%
            sorted_idx = np.argsort(fitness)[:self.pop_size // 2]
            self.populations[sp] = self.populations[sp][sorted_idx]

            # 简单变异
            for i in range(len(self.populations[sp])):
                if random.random() < 0.1:
                    self.populations[sp][i] += np.random.randn(len(self.populations[sp][i])) * 0.1
                    self.populations[sp][i] = np.clip(
                        self.populations[sp][i], self.low, self.high)

    def optimize(self, max_iter=100, verbose=True):
        """优化"""
        for it in range(max_iter):
            self.evolve_one_step()

            if verbose and it % 20 == 0:
                fitness = self.evaluate_cooperative()
                print(f"Iter {it}: best_coop_fitness={min(fitness):.4f}")

        return self.evaluate_cooperative()


if __name__ == "__main__":
    print("协同进化测试")

    def sphere(x):
        return np.sum(x**2)

    coevo = Coevolution(n_species=2, func=sphere, dim=10, low=-10, high=10)
    results = coevo.optimize(max_iter=50)
    print(f"最优适应度: {min(results):.4f}")
