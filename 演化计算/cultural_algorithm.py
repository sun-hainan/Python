"""
文化算法
==========================================

【原理】
双层进化：种群层 + 信仰空间层。
信仰空间记录经验知识，引导种群进化。

【时间复杂度】O(population_size × belief_size)
【空间复杂度】O(population + belief)
"""

import random
import numpy as np


class BeliefSpace:
    """信仰空间：存储领域知识"""

    def __init__(self, dim, low, high):
        self.dim = dim
        self.low = low
        self.high = high

        # 情境知识：最优解
        self.situation = None
        self.situation_fitness = float('inf')

        # 规范知识：可行区间
        self.min_bounds = np.full(dim, low)
        self.max_bounds = np.full(dim, high)

        # 领域知识：多个好解
        self.elite_solutions = []
        self.max_elite = 10

    def update_situation(self, solution, fitness):
        """更新情境"""
        if fitness < self.situation_fitness:
            self.situation = solution.copy()
            self.situation_fitness = fitness

    def update_normative(self, solutions, fitnesses):
        """更新规范知识"""
        # 更新每个维度的上下界
        for d in range(self.dim):
            values = [s[d] for s in solutions]
            # 只更新好的解的边界
            sorted_idx = np.argsort(fitnesses)
            top_half = sorted_idx[:len(sorted_idx) // 2]

            self.min_bounds[d] = min(solutions[i][d] for i in top_half)
            self.max_bounds[d] = max(solutions[i][d] for i in top_half)

    def update_elite(self, solution, fitness):
        """更新精英解"""
        self.elite_solutions.append((solution, fitness))
        self.elite_solutions.sort(key=lambda x: x[1])
        if len(self.elite_solutions) > self.max_elite:
            self.elite_solutions.pop()


class CulturalAlgorithm:
    """
    文化算法

    【种群进化循环】
    1. 初始化种群
    2. 评估适应度
    3. 更新信仰空间（accept）
    4. 利用信仰空间引导进化（influence）
    5. 选择
    """

    def __init__(self, func, dim, low, high, pop_size=50, max_iter=200):
        self.func = func
        self.dim = dim
        self.low = low
        self.high = high
        self.pop_size = pop_size
        self.max_iter = max_iter

        self.population = np.random.uniform(low, high, (pop_size, dim))
        self.belief = BeliefSpace(dim, low, high)

    def accept(self, solutions, fitnesses):
        """接受操作：更新信仰空间"""
        # 更新情境
        best_idx = np.argmin(fitnesses)
        self.belief.update_situation(solutions[best_idx], fitnesses[best_idx])

        # 更新规范知识
        self.belief.update_normative(solutions, fitnesses)

        # 更新精英
        self.belief.update_elite(solutions[best_idx], fitnesses[best_idx])

    def influence(self, individual):
        """影响操作：信仰空间引导变异"""
        influenced = individual.copy()

        # 情境引导：向最优解移动
        if self.belief.situation is not None:
            r = random.random()
            if r < 0.3:
                influenced += 0.1 * (self.belief.situation - influenced)

        # 规范引导：在边界内变异
        for d in range(self.dim):
            if random.random() < 0.1:
                lo, hi = self.belief.min_bounds[d], self.belief.max_bounds[d]
                influenced[d] = random.uniform(lo, hi)

        return np.clip(influenced, self.low, self.high)

    def optimize(self, verbose=True):
        """优化"""
        for it in range(self.max_iter):
            # 评估
            fitnesses = np.array([self.func(x) for x in self.population])

            # 接受
            self.accept(self.population, fitnesses)

            # 影响 + 选择
            new_population = []
            for i in range(self.pop_size):
                # 变异
                mutated = self.population[i] + np.random.randn(self.dim) * 0.1
                # 信仰空间影响
                influenced = self.influence(mutated)
                new_population.append(influenced)

            self.population = np.array(new_population)

            if verbose and it % 50 == 0:
                print(f"Iter {it}: best_fitness={min(fitnesses):.6f}")

        fitnesses = [self.func(x) for x in self.population]
        best_idx = np.argmin(fitnesses)
        return self.population[best_idx], min(fitnesses)


if __name__ == "__main__":
    print("文化算法测试")

    def sphere(x):
        return np.sum(x**2)

    ca = CulturalAlgorithm(sphere, dim=10, low=-100, high=100)
    best, fitness = ca.optimize(verbose=True)
    print(f"最优适应度: {fitness:.6f}")
