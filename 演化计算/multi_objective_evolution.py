"""
NSGA-II 多目标进化
==========================================

【原理】
非支配排序遗传算法，通过非支配排序和拥挤距离保持多样性。

【时间复杂度】O(MN²) 其中M为目标数
【空间复杂度】O(MN)
"""

import random
import numpy as np


class NSGAII:
    """
    NSGA-II

    【核心机制】
    1. 快速非支配排序
    2. 拥挤距离计算
    3. 精英保留策略
    """

    def __init__(self, funcs, dim, low, high, pop_size=100, max_iter=200):
        self.funcs = funcs  # 多个目标函数
        self.dim = dim
        self.low = low
        self.high = high
        self.n = pop_size
        self.max_iter = max_iter
        self.M = len(funcs)

    def dominates(self, p, q):
        """判断p是否支配q"""
        better = False
        for i in range(self.M):
            if p[i] > q[i]:
                return False
            elif p[i] < q[i]:
                better = True
        return better

    def fast_non_dominated_sort(self, pop_obj):
        """快速非支配排序"""
        n = len(pop_obj)
        domination_count = [0] * n
        dominated_set = [[] for _ in range(n)]
        fronts = [[]]

        for i in range(n):
            for j in range(n):
                if i != j and self.dominates(pop_obj[i], pop_obj[j]):
                    dominated_set[i].append(j)
                elif i != j and self.dominates(pop_obj[j], pop_obj[i]):
                    domination_count[i] += 1

            if domination_count[i] == 0:
                fronts[0].append(i)

        k = 0
        while fronts[k]:
            next_front = []
            for i in fronts[k]:
                for j in dominated_set[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            k += 1
            fronts.append(next_front)

        return fronts[:-1]

    def crowding_distance(self, pop_obj, front):
        """计算拥挤距离"""
        n = len(front)
        if n <= 2:
            return [float('inf')] * n

        distances = [0.0] * n
        for m in range(self.M):
            front_sorted = sorted(front, key=lambda x: pop_obj[x][m])
            distances[0] = distances[-1] = float('inf')

            f_range = pop_obj[front_sorted[-1]][m] - pop_obj[front_sorted[0]][m]
            if f_range == 0:
                f_range = 1

            for i in range(1, n - 1):
                distances[i] += (pop_obj[front_sorted[i+1]][m] -
                               pop_obj[front_sorted[i-1]][m]) / f_range

        return distances

    def optimize(self, verbose=True):
        """执行NSGA-II"""
        # 初始化
        pop = np.random.uniform(self.low, self.high, (self.n, self.dim))

        for iter in range(self.max_iter):
            # 评估
            pop_obj = np.array([[f(x) for f in self.funcs] for x in pop])

            # 非支配排序
            fronts = self.fast_non_dominated_sort(pop_obj)

            # 选择（基于排名和拥挤距离）
            selected = []
            for front in fronts:
                if len(selected) + len(front) <= self.n:
                    selected.extend(front)
                else:
                    dists = self.crowding_distance(pop_obj, front)
                    remaining = self.n - len(selected)
                    indices = sorted(range(len(front)),
                                   key=lambda i: dists[i], reverse=True)[:remaining]
                    selected.extend([front[i] for i in indices])
                    break

            # 交叉/变异（简化：随机）
            offspring = pop[selected].copy()
            for i in range(0, len(offspring), 2):
                if i + 1 < len(offspring) and random.random() < 0.9:
                    alpha = random.random()
                    offspring[i] = alpha * offspring[i] + (1-alpha) * offspring[i+1]
                    offspring[i+1] = (1-alpha) * offspring[i] + alpha * offspring[i+1]

            pop = offspring

            if verbose and iter % 50 == 0:
                print(f"Iter {iter}: 帕累托前沿大小={len(fronts[0])}")

        # 返回帕累托前沿
        final_obj = np.array([[f(x) for f in self.funcs] for x in pop])
        fronts = self.fast_non_dominated_sort(final_obj)

        return pop[fronts[0]], final_obj[fronts[0]]


if __name__ == "__main__":
    print("NSGA-II测试")

    def obj1(x):
        return x[0]**2 + x[1]**2

    def obj2(x):
        return (x[0] - 2)**2 + (x[1] - 2)**2

    nsga = NSGAII([obj1, obj2], dim=2, low=-10, high=10)
    pareto_x, pareto_f = nsga.optimize(verbose=True)
    print(f"帕累托前沿解数: {len(pareto_x)}")
    print(f"帕累托前沿: {pareto_f[:3]}")
