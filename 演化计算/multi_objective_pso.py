"""
多目标PSO (MOPSO)
==========================================

【原理】
将PSO扩展到多目标问题，使用帕累托存档和全球最佳选择。

【时间复杂度】O(generations × population_size)
【空间复杂度】O(archive_size × dim)
"""

import random
import numpy as np


class MOPSO:
    """
    多目标粒子群优化

    【核心机制】
    1. 帕累托存档：存储非支配解
    2. 领导者选择：从存档中选最优
    3. 速度更新：标准PSO + 领导者引导
    """

    def __init__(self, funcs, dim, low, high, n_particles=100,
                 max_iter=200, archive_size=100):
        self.funcs = funcs
        self.dim = dim
        self.low = low
        self.high = high
        self.n = n_particles
        self.max_iter = max_iter
        self.archive_size = archive_size
        self.M = len(funcs)

    def dominates(self, p, q):
        """判断p支配q"""
        better = False
        for i in range(self.M):
            if p[i] > q[i]:
                return False
            elif p[i] < q[i]:
                better = True
        return better

    def update_archive(self, archive, new_particles, new_fitness):
        """更新帕累托存档"""
        for i, p in enumerate(new_particles):
            dominated = False
            to_remove = []

            for j, a in enumerate(archive):
                if self.dominates(p, a):
                    to_remove.append(j)
                elif self.dominates(a, p):
                    dominated = True

            if not dominated:
                archive.append(p)
                for j in sorted(to_remove, reverse=True):
                    archive.pop(j)

                if len(archive) > self.archive_size:
                    # 拥挤距离修剪
                    archive.pop(random.randint(0, len(archive) - 1))

        return archive

    def optimize(self, verbose=True):
        """执行MOPSO"""
        # 初始化
        X = np.random.uniform(self.low, self.high, (self.n, self.dim))
        V = np.zeros((self.n, self.dim))
        pbest = X.copy()
        pbest_fitness = np.array([[f(x) for f in self.funcs] for x in X])

        archive = []
        archive_fitness = []

        for iter in range(self.max_iter):
            # 评估
            fitness = np.array([[f(x) for f in self.funcs] for x in X])

            # 更新个人最佳
            for i in range(self.n):
                if self.dominates(fitness[i], pbest_fitness[i]):
                    pbest[i] = X[i].copy()
                    pbest_fitness[i] = fitness[i]

            # 更新存档
            archive = self.update_archive(archive, X, fitness)

            if len(archive) == 0:
                continue

            # 速度更新参数
            w = 0.4
            c1, c2 = 2, 2

            # 选择领导者
            leader_idx = random.randint(0, len(archive) - 1)
            leader = archive[leader_idx]

            # 更新速度和位置
            r1, r2 = np.random.rand(self.dim), np.random.rand(self.dim)
            V = w * V + c1 * r1 * (pbest - X) + c2 * r2 * (leader - X)
            X = X + V
            X = np.clip(X, self.low, self.high)

            if verbose and iter % 50 == 0:
                print(f"Iter {iter}: 存档大小={len(archive)}")

        return np.array(archive)


if __name__ == "__main__":
    print("MOPSO测试")

    def obj1(x):
        return x[0]**2 + x[1]**2

    def obj2(x):
        return (x[0] - 5)**2 + (x[1] - 5)**2

    mopso = MOPSO([obj1, obj2], dim=2, low=-10, high=10)
    pareto = mopso.optimize(verbose=True)
    print(f"帕累托前沿解数: {len(pareto)}")
