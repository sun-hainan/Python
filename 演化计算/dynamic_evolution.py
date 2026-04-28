"""
动态环境演化 (Dynamic EA)
==========================================

【原理】
在动态环境中优化，环境随时间变化。需要：
- 检测变化
- 维持多样性
- 追踪移动最优

【时间复杂度】O(population × dim × generations)
【空间复杂度】O(population × dim)
"""

import random
import numpy as np


class DynamicEnvironment:
    """动态环境模拟器"""

    def __init__(self, func, change_interval=50):
        self.func = func
        self.change_interval = change_interval
        self.time = 0
        self.optimum = np.array([0.0])

    def get_fitness(self, x):
        """获取适应度（可能变化）"""
        return self.func(x, self.time)

    def step(self):
        """环境变化"""
        self.time += 1
        if self.time % self.change_interval == 0:
            # 移动最优位置
            self.optimum += np.random.randn(len(self.optimum)) * 0.5


class DynamicEA:
    """
    动态环境进化算法

    【策略】
    1. 多样性维护：保持种群多样性应对变化
    2. 记忆策略：保留历史最优解
    3. 变化检测：检测环境变化后重新初始化部分个体
    """

    def __init__(self, func, dim, low, high, pop_size=50, change_interval=50):
        self.dim = dim
        self.low = low
        self.high = high
        self.pop_size = pop_size
        self.env = DynamicEnvironment(func, change_interval)

        # 初始化种群
        self.pop = np.random.uniform(low, high, (pop_size, dim))
        self.best_ever = None
        self.best_ever_fitness = float('inf')

    def evaluate(self):
        """评估种群"""
        return np.array([self.env.get_fitness(x) for x in self.pop])

    def detect_change(self, old_fitness, new_fitness):
        """检测环境变化"""
        # 方法1：最优适应度显著下降
        if min(new_fitness) > min(old_fitness) + 0.1:
            return True
        return False

    def reinitialize_partially(self, proportion=0.3):
        """部分重新初始化以增加多样性"""
        n_replace = int(self.pop_size * proportion)
        indices = random.sample(range(self.pop_size), n_replace)
        for i in indices:
            self.pop[i] = np.random.uniform(self.low, self.high, self.dim)

    def optimize(self, max_iter=500, verbose=True):
        """优化"""
        old_fitness = self.evaluate()

        for it in range(max_iter):
            new_fitness = self.evaluate()

            # 检测变化
            if self.detect_change(old_fitness, new_fitness):
                if verbose:
                    print(f"Iter {it}: 环境变化！重新初始化部分种群")
                self.reinitialize_partially()
                new_fitness = self.evaluate()

            # 选择
            sorted_idx = np.argsort(new_fitness)
            self.pop = self.pop[sorted_idx[:self.pop_size // 2]]

            # 多样性增强：保留较差个体
            n_keep = self.pop_size // 3
            worst_indices = sorted_idx[-n_keep:]
            for i, idx in enumerate(worst_indices):
                self.pop = np.vstack([self.pop, self.pop[idx] + np.random.randn(self.dim) * 0.5])

            # 生成新个体
            while len(self.pop) < self.pop_size:
                p1, p2 = random.choices(self.pop, k=2)
                child = (p1 + p2) / 2 + np.random.randn(self.dim) * 0.2
                child = np.clip(child, self.low, self.high)
                self.pop = np.vstack([self.pop, child])

            self.pop = self.pop[:self.pop_size]

            # 更新历史最优
            current_best = min(new_fitness)
            if current_best < self.best_ever_fitness:
                self.best_ever = self.pop[np.argmin(new_fitness)].copy()
                self.best_ever_fitness = current_best

            old_fitness = new_fitness

            # 环境变化
            self.env.step()

            if verbose and it % 50 == 0:
                print(f"Iter {it}: best={current_best:.4f}, ever_best={self.best_ever_fitness:.4f}")

        return self.best_ever, self.best_ever_fitness


if __name__ == "__main__":
    print("动态环境演化测试")

    def dynamic_sphere(x, t):
        """动态球函数：最优位置随时间移动"""
        optimum = np.array([np.sin(t * 0.1), np.cos(t * 0.1)] + [0] * (len(x) - 2))
        return np.sum((x - optimum)**2)

    dea = DynamicEA(dynamic_sphere, dim=5, low=-10, high=10,
                   pop_size=50, change_interval=30)
    best, fitness = dea.optimize(max_iter=200)
    print(f"最终最优适应度: {fitness:.4f}")
