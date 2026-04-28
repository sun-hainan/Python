"""
差分进化
==========================================

【算法原理】
基于差分变异的进化算法。核心思想是利用种群中个体间的差分向量
来引导搜索方向，适合连续空间优化。

【时间复杂度】O(generations × population_size × dim)
【空间复杂度】O(population_size × dim)

【应用场景】
- 全局优化
- 约束优化
- 多模态优化
- 超参数调优

【何时使用】
- 目标函数不连续、不可微
- 需要强全局搜索能力
- 比GA更鲁棒
"""

import random
import numpy as np
from typing import List, Callable, Tuple


class DifferentialEvolution:
    """
    差分进化算法

    【核心操作：差分变异】
    v = x_r1 + F * (x_r2 - x_r3)
    其中F是缩放因子（通常0-2），r1,r2,r3随机选取且互不相同

    【常用策略】
    - DE/rand/1/bin: 随机基向量，二项式交叉
    - DE/best/1/bin: 最优基向量，二项式交叉
    - DE/rand-to-best/1/bin: 混合策略
    """

    def __init__(self, func: Callable, dim: int, low: float, high: float,
                 pop_size: int = 20, F: float = 0.8, CR: float = 0.9,
                 strategy: str = "rand/1/bin", verbose: bool = True):
        """
        初始化差分进化

        【参数】
        - func: 目标函数（最小化）
        - dim: 决策变量维度
        - low/high: 变量边界
        - pop_size: 种群大小（建议≥5×dim）
        - F: 缩放因子（0-2，典型0.5-1.0）
        - CR: 交叉概率（0-1，典型0.3-0.9）
        - strategy: DE策略
        """
        self.func = func
        self.dim = dim
        self.low = low
        self.high = high
        self.pop_size = pop_size
        self.F = F
        self.CR = CR
        self.strategy = strategy
        self.verbose = verbose

        # 初始化种群
        self.population = self._init_population()

    def _init_population(self) -> List[np.ndarray]:
        """初始化种群"""
        pop = []
        for _ in range(self.pop_size):
            # 均匀随机初始化
            ind = np.random.uniform(self.low, self.high, self.dim)
            pop.append(ind)
        return pop

    def _mutate(self, idx: int) -> np.ndarray:
        """
        差分变异操作

        【策略DE/rand/1】
        v_i = x_r1 + F * (x_r2 - x_r3)
        """
        # 随机选3个不同于idx的个体
        candidates = list(range(self.pop_size))
        candidates.remove(idx)
        r1, r2, r3 = random.sample(candidates, 3)

        if self.strategy == "rand/1/bin":
            # 随机基向量
            v = self.population[r1] + self.F * (self.population[r2] - self.population[r3])
        elif self.strategy == "best/1/bin":
            # 最优基向量
            best_idx = min(range(self.pop_size),
                          key=lambda i: self.func(self.population[i]))
            v = self.population[best_idx] + self.F * (self.population[r2] - self.population[r3])
        elif self.strategy == "rand-to-best/1/bin":
            best_idx = min(range(self.pop_size),
                          key=lambda i: self.func(self.population[i]))
            v = self.population[idx] + 0.5 * self.F * (self.population[best_idx] - self.population[idx]) \
                + self.F * (self.population[r1] - self.population[r2])
        else:
            v = self.population[r1] + self.F * (self.population[r2] - self.population[r3])

        # 边界处理
        v = np.clip(v, self.low, self.high)
        return v

    def _crossover(self, target: np.ndarray, mutant: np.ndarray) -> np.ndarray:
        """
        二项式交叉（Binomial Crossover）

        【原理】
        - 以概率CR选择mutant基因
        - 否则继承target基因
        - 确保至少选一个mutant基因（增强开发）
        """
        trial = target.copy()
        j_rand = random.randint(0, self.dim - 1)  # 强制至少一个位置用mutant

        for j in range(self.dim):
            if random.random() < self.CR or j == j_rand:
                trial[j] = mutant[j]

        return trial

    def _select(self, target: np.ndarray, trial: np.ndarray) -> np.ndarray:
        """
        选择操作（贪心）

        【原理】trial适应度若优于target则替换
        """
        f_target = self.func(target)
        f_trial = self.func(trial)

        if f_trial <= f_target:
            return trial
        else:
            return target

    def optimize(self, max_generations: int = 500,
                 tol: float = 1e-10) -> Tuple[np.ndarray, float]:
        """
        执行差分进化优化

        【流程】
        for gen in generations:
            for each target vector x_i:
                1. 变异 -> mutant vector v_i
                2. 交叉 -> trial vector u_i
                3. 选择 -> 贪心选择x_i或u_i进入下一代
        """
        best_history = []

        for gen in range(max_generations):
            fitness_values = [self.func(x) for x in self.population]
            best_idx = min(range(self.pop_size), key=lambda i: fitness_values[i])
            best_fitness = fitness_values[best_idx]
            best_history.append(best_fitness)

            if self.verbose and gen % 50 == 0:
                print(f"Gen {gen:4d}: best_fitness = {best_fitness:.8f}")

            # 检查收敛
            if best_fitness < tol:
                if self.verbose:
                    print(f"收敛于第{gen}代")
                break

            # 代际更新
            new_population = []
            for i in range(self.pop_size):
                # 变异
                mutant = self._mutate(i)
                # 交叉
                trial = self._crossover(self.population[i], mutant)
                # 选择
                new_ind = self._select(self.population[i], trial)
                new_population.append(new_ind)

            self.population = new_population

        # 返回最优
        best_idx = min(range(self.pop_size), key=lambda i: self.func(self.population[i]))
        return self.population[best_idx], self.func(self.population[best_idx])


# ========================================
# 自适应DE变体
# ========================================

class AdaptiveDE(DifferentialEvolution):
    """
    自适应差分进化（JADE风格）

    【改进】
    1. 自适应F和CR：每个个体有独立的F和CR
    2. current-to-pbest/1 变异策略
    3. 可选外部存档存储失败个体
    """

    def __init__(self, *args, c: float = 0.1, p: float = 0.05, **kwargs):
        super().__init__(*args, **kwargs)
        # 自适应参数
        self.c = c  # F均值更新学习率
        self.p = p  # top-p比例
        # 初始化F和CR
        self.F_i = [0.5] * self.pop_size
        self.CR_i = [0.5] * self.pop_size
        # 存档
        self.archive = []

    def _mutate_adaptive(self, idx: int) -> np.ndarray:
        """
        Current-to-pbest/1 with Archive
        v_i = x_i + F_i * (x_best^p - x_i) + F_i * (x_r1 - x_r2_archive)
        """
        # 选最优p%个体
        sorted_idx = sorted(range(self.pop_size),
                          key=lambda i: self.func(self.population[i]))
        pbest_idx = sorted_idx[random.randint(0, max(1, int(self.p * self.pop_size)) - 1)]
        x_pbest = self.population[pbest_idx]

        # 随机选当前种群中一个
        candidates = list(range(self.pop_size))
        candidates.remove(idx)
        r1 = random.choice(candidates)

        # 加上存档
        all_candidates = candidates + self.archive if self.archive else candidates
        r2 = random.choice(all_candidates)

        x_i = self.population[idx]
        F_i = self.F_i[idx]

        v = x_i + F_i * (x_pbest - x_i) + F_i * (self.population[r1] - self.population[r2])
        v = np.clip(v, self.low, self.high)
        return v

    def _update_adaptive_params(self, success_F: List[float], success_CR: List[float]):
        """更新自适应参数均值"""
        if success_F:
            # Lehmer mean for F
            self.F_i = [random.gauss(
                (1 - self.c) * f + self.c * (sum(sf**2 for sf in success_F) / sum(success_F)),
                0.1
            ) for f in self.F_i]
            self.F_i = [max(0, min(2, f)) for f in self.F_i]

            # Arithmetic mean for CR
            self.CR_i = [random.gauss(
                (1 - self.c) * cr + self.c * (sum(success_CR) / len(success_CR)),
                0.1
            ) for cr in self.CR_i]
            self.CR_i = [max(0, min(1, cr)) for cr in self.CR_i]

    def optimize(self, max_generations: int = 500, tol: float = 1e-10) -> Tuple[np.ndarray, float]:
        """自适应DE优化"""
        success_F, success_CR = [], []

        for gen in range(max_generations):
            fitness_values = [self.func(x) for x in self.population]
            best_idx = min(range(self.pop_size), key=lambda i: fitness_values[i])
            best_fitness = fitness_values[best_idx]

            if self.verbose and gen % 50 == 0:
                print(f"Gen {gen:4d}: best_fitness = {best_fitness:.8f}, F_mean = {np.mean(self.F_i):.3f}")

            if best_fitness < tol:
                break

            new_population = []
            for i in range(self.pop_size):
                # 使用自适应变异
                if hasattr(self, 'c'):
                    mutant = self._mutate_adaptive(i)
                else:
                    mutant = self._mutate(i)

                # 自适应CR
                trial = self._crossover_with_adaptive(self.population[i], mutant, i)
                f_old = fitness_values[i]
                f_new = self.func(trial)

                # 贪心选择
                if f_new <= f_old:
                    new_population.append(trial)
                    success_F.append(self.F_i[i])
                    success_CR.append(self.CR_i[i])
                    # 加入存档
                    if len(self.archive) > self.pop_size:
                        remove_idx = random.randint(0, len(self.archive) - 1)
                        self.archive.pop(remove_idx)
                    self.archive.append(self.population[i])
                else:
                    new_population.append(self.population[i])

            self.population = new_population

            # 更新参数
            if success_F:
                self._update_adaptive_params(success_F, success_CR)
            success_F, success_CR = [], []

        best_idx = min(range(self.pop_size), key=lambda i: self.func(self.population[i]))
        return self.population[best_idx], self.func(self.population[best_idx])

    def _crossover_with_adaptive(self, target: np.ndarray, mutant: np.ndarray, idx: int) -> np.ndarray:
        """带自适应CR的交叉"""
        trial = target.copy()
        j_rand = random.randint(0, self.dim - 1)
        CR_i = self.CR_i[idx]

        for j in range(self.dim):
            if random.random() < CR_i or j == j_rand:
                trial[j] = mutant[j]

        return trial


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("差分进化算法 - 测试")
    print("=" * 50)

    # Sphere函数
    def sphere(x):
        return sum(xi**2 for xi in x)

    # Rastrigrin函数
    def rastrigrin(x):
        return 10 * len(x) + sum(xi**2 - 10*np.cos(2*np.pi*xi) for xi in x)

    # Ackley函数
    def ackley(x):
        a, b, c = 20, 0.2, 2*np.pi
        n = len(x)
        s1 = sum(xi**2 for xi in x)
        s2 = sum(np.cos(c*xi) for xi in x)
        return -a * np.exp(-b * np.sqrt(s1/n)) - np.exp(s2/n) + a + np.e

    # 测试标准DE
    print("\n【测试1】标准DE/rand/1/bin 优化Sphere (n=10)")
    de = DifferentialEvolution(
        func=sphere, dim=10, low=-100, high=100,
        pop_size=50, F=0.8, CR=0.9, verbose=True
    )
    best, fitness = de.optimize(max_generations=200)
    print(f"最优适应度: {fitness:.8f}")

    # 测试自适应DE
    print("\n【测试2】自适应DE(JADE) 优化Ackley (n=10)")
    ade = AdaptiveDE(
        func=ackley, dim=10, low=-32, high=32,
        pop_size=50, c=0.1, p=0.05, verbose=True
    )
    best2, fitness2 = ade.optimize(max_generations=300)
    print(f"最优适应度: {fitness2:.8f}")

    print("\n" + "=" * 50)
    print("差分进化测试完成！")
    print("=" * 50)
