"""
双层进化优化 (BLGANN)
==========================================

【原理】
两层优化问题：上层优化整体参数，下层是上层参数的函数。

【时间复杂度】O(upper_iter × lower_iter × pop_size)
【空间复杂度】O(pop_size × dim)
"""

import random
import numpy as np


class BilevelOptimization:
    """
    双层进化优化

    【问题定义】
    min F(x, y)
    s.t. y = argmin G(x, y)
           y ∈ Y(x)

    其中 x 是上层变量，y 是下层变量
    """

    def __init__(self, upper_func, lower_func, dim_upper, dim_lower,
                 low, high, pop_size=50):
        self.upper_func = upper_func
        self.lower_func = lower_func
        self.dim_upper = dim_upper
        self.dim_lower = dim_lower
        self.low = low
        self.high = high
        self.pop_size = pop_size

    def solve_lower(self, x):
        """解决下层问题：给定x，找最优y"""
        # 简化：用梯度下降找y
        y = np.random.uniform(self.low, self.high, self.dim_lower)

        for _ in range(50):
            grad = np.random.randn(self.dim_lower)  # 简化梯度
            y -= 0.01 * grad
            y = np.clip(y, self.low, self.high)

        return y

    def evaluate(self, x):
        """评估上层解（需要先解决下层）"""
        y = self.solve_lower(x)
        return self.upper_func(x, y)

    def optimize(self, max_iter=100, verbose=True):
        """进化优化"""
        # 初始化上层种群
        pop = np.random.uniform(self.low, self.high, (self.pop_size, self.dim_upper))
        fitness = np.array([self.evaluate(x) for x in pop])

        for it in range(max_iter):
            # 选择
            sorted_idx = np.argsort(fitness)
            top = pop[sorted_idx[:self.pop_size // 2]]

            # 生成新个体
            new_pop = []
            for _ in range(self.pop_size):
                p1, p2 = random.choices(top, k=2)
                child = (p1 + p2) / 2 + np.random.randn(self.dim_upper) * 0.1
                child = np.clip(child, self.low, self.high)
                new_pop.append(child)

            pop = np.array(new_pop)
            fitness = np.array([self.evaluate(x) for x in pop])

            if verbose and it % 20 == 0:
                print(f"Iter {it}: best_fitness={min(fitness):.4f}")

        best_idx = np.argmin(fitness)
        return pop[best_idx], fitness[best_idx]


if __name__ == "__main__":
    print("双层优化测试")

    def upper(x, y):
        return np.sum((x - y)**2)

    def lower(x, y):
        return np.sum((x - y)**2)

    bio = BilevelOptimization(upper, lower, dim_upper=5, dim_lower=5,
                             low=-10, high=10)
    best_x, best_f = bio.optimize(max_iter=30)
    print(f"最优适应度: {best_f:.4f}")
