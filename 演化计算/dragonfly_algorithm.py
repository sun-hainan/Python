"""
蜻蜓算法 (DA)
==========================================

【算法原理】
模拟蜻蜓的静态和动态群集行为：
- 静态行为（Separation/Alineation/Cohesion）用于探索
- 动态行为（聚集、觅食）用于开发

【时间复杂度】O(generations × population_size × dim)
【空间复杂度】O(population_size × dim)
"""

import random
import numpy as np


class DragonflyAlgorithm:
    """
    蜻蜓算法

    【蜻蜓行为】
    1. Separation: 避免碰撞 s = -Σ(X - X_i)
    2. Alignment: 速度对齐 a = Σ(V_i) / N
    3. Cohesion: 飞向群体中心 c = Σ(X_i) / N - X
    4. Attraction to food: f = X_food - X
    5. Distraction from enemy: e = X_enemy + X
    """

    def __init__(self, func, dim, low, high, n_dragonflies=20, max_iter=500):
        self.func = func
        self.dim = dim
        self.low = low
        self.high = high
        self.n = n_dragonflies
        self.max_iter = max_iter

        # 初始化种群
        self.pos = np.random.uniform(low, high, (n_dragonflies, dim))
        self.vel = np.zeros((n_dragonflies, dim))
        self.fitness = np.array([func(x) for x in self.pos])

        # 最佳
        self.best_pos = None
        self.best_fitness = float('inf')
        self._update_best()

    def _update_best(self):
        """更新最优"""
        for i in range(self.n):
            if self.fitness[i] < self.best_fitness:
                self.best_fitness = self.fitness[i]
                self.best_pos = self.pos[i].copy()

    def optimize(self, verbose=True):
        """执行DA优化"""
        w_max, w_min = 0.9, 0.4

        for iter in range(self.max_iter):
            # 惯性权重衰减
            w = w_max - (w_max - w_min) * iter / self.max_iter

            # 随机步长
            r = np.random.rand(self.dim) * 2 - 1

            # 更新每个蜻蜓
            for i in range(self.n):
                S = np.zeros(self.dim)  # Separation
                A = np.zeros(self.dim)  # Alignment
                C = np.zeros(self.dim)  # Cohesion
                F = np.zeros(self.dim)  # Food attraction
                E = np.zeros(self.dim)  # Enemy distraction

                for j in range(self.n):
                    if i != j:
                        d = self.pos[i] - self.pos[j]
                        S += d / (np.linalg.norm(d) + 1e-10)
                        A += self.vel[j]
                        C += self.pos[j]
                        F = self.best_pos - self.pos[i]
                        E = self.pos[j] + self.pos[i]

                C = C / (self.n - 1) - self.pos[i]

                # 合并行为
                step = (S + A + C + F + E) / self.n + w * self.vel[i] + r * 0.2

                # 更新速度和位置
                self.vel[i] = w * self.vel[i] + step
                self.pos[i] += self.vel[i]

                # 边界处理
                self.pos[i] = np.clip(self.pos[i], self.low, self.high)
                self.fitness[i] = self.func(self.pos[i])

            self._update_best()

            if verbose and iter % 50 == 0:
                print(f"Iter {iter}: best_fitness={self.best_fitness:.6f}")

        return self.best_pos, self.best_fitness


if __name__ == "__main__":
    print("蜻蜓算法测试")

    def sphere(x):
        return np.sum(x**2)

    da = DragonflyAlgorithm(sphere, dim=10, low=-100, high=100)
    best, fitness = da.optimize(verbose=True)
    print(f"最优适应度: {fitness:.6f}")
