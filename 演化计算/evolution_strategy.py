"""
进化策略
==========================================

【算法原理】
以个体适应度和策略参数（通常是步长/协方差矩阵）共同进化。
与GA主要区别：使用实数编码、强调变异、父子竞争机制。

【时间复杂度】O(generations × pop_size × fitness_eval)
【空间复杂度】O(pop_size × dim + cov_matrix)

【应用场景】
- 连续空间优化
- 协方差矩阵自适应（CMA-ES）
- 强化学习策略优化
- 超参数调优

【何时使用】
- 变量连续取值
- 需要自适应步长控制
- 高维非凸优化
"""

import random
import numpy as np
from typing import List, Tuple, Optional


class EvolutionStrategy:
    """
    (μ + λ)-ES 和 (μ, λ)-ES 进化策略

    【参数】
    - μ: 父代个数
    - λ: 子代个数
    - (μ + λ): 父子合并选择（精英保留）
    - (μ, λ): 仅子代选择（不保留父代，更利于逃逸局部最优）
    """

    def __init__(self, func, dim, low, high, mu: int = 10, lambda_: int = 100,
                 sigma: float = 1.0, strategy: str = "plus", verbose: bool = True):
        """
        初始化进化策略

        【参数】
        - mu: 父代种群大小
        - lambda_: 子代种群大小
        - sigma: 全局步长（初始）
        - strategy: "plus"=(μ+λ), "comma"=(μ,λ)
        """
        self.func = func
        self.dim = dim
        self.low = low
        self.high = high
        self.mu = mu
        self.lambda_ = lambda_
        self.sigma = sigma
        self.strategy = strategy
        self.verbose = verbose

        # 初始化父代
        self.population = self._init_population(mu)

    def _init_population(self, size: int) -> List[np.ndarray]:
        """初始化种群"""
        return [np.random.uniform(self.low, self.high, self.dim) for _ in range(size)]

    def _mutate(self, parent: np.ndarray) -> np.ndarray:
        """
        高斯变异

        【原理】x' = x + N(0, σ²·I)
        σ是全局步长，控制搜索半径
        """
        noise = np.random.normal(0, self.sigma, self.dim)
        child = parent + noise
        return np.clip(child, self.low, self.high)

    def _recombine(self, parents: List[np.ndarray]) -> np.ndarray:
        """
        重组操作（离散重组或中间重组）

        【方法】
        - 离散重组：随机选某个父代的基因
        - 中间重组：取父代基因的均值
        """
        if len(parents) < 2:
            return parents[0].copy()

        # 离散重组
        child = np.array([random.choice(parents)[i] for i in range(self.dim)])
        return child

    def _select_plus(self, parents: List[np.ndarray], offspring: List[np.ndarray]) -> List[np.ndarray]:
        """
        (μ + λ) 选择：父子合并，择优取μ个
        """
        combined = parents + offspring
        fitness = [(i, self.func(x)) for i, x in enumerate(combined)]
        # 升序排列（最小化问题）
        fitness.sort(key=lambda x: x[1])
        selected = [combined[fitness[i][0]] for i in range(self.mu)]
        return selected

    def _select_comma(self, offspring: List[np.ndarray]) -> List[np.ndarray]:
        """
        (μ, λ) 选择：仅从子代中选μ个（父代被丢弃）
        """
        fitness = [(i, self.func(x)) for i, x in enumerate(offspring)]
        fitness.sort(key=lambda x: x[1])
        selected = [offspring[fitness[i][0]] for i in range(self.mu)]
        return selected

    def optimize(self, max_generations: int = 500, sigma_decay: float = 0.99,
                tol: float = 1e-10) -> Tuple[np.ndarray, float]:
        """
        执行进化策略优化
        """
        best_history = []

        for gen in range(max_generations):
            # 评估父代
            parent_fitness = [self.func(x) for x in self.population]
            best_idx = np.argmin(parent_fitness)
            best_fitness = parent_fitness[best_idx]
            best_history.append(best_fitness)

            if self.verbose and gen % 50 == 0:
                print(f"Gen {gen:4d}: best_fitness = {best_fitness:.8f}, sigma = {self.sigma:.4f}")

            # 收敛检查
            if best_fitness < tol:
                break

            # 重组：从父代中选若干进行重组生成子代
            # 简化：每个子代由随机选2个父代重组后变异
            offspring = []
            for _ in range(self.lambda_):
                # 随机选2个父代重组
                p1, p2 = random.sample(self.population, 2)
                # 中间重组
                child = (p1 + p2) / 2.0
                # 变异
                child = self._mutate(child)
                offspring.append(child)

            # 选择
            if self.strategy == "plus":
                self.population = self._select_plus(self.population, offspring)
            else:
                self.population = self._select_comma(offspring)

            # 步长衰减
            self.sigma *= sigma_decay

        # 返回最优
        fitness = [self.func(x) for x in self.population]
        best_idx = np.argmin(fitness)
        return self.population[best_idx], fitness[best_idx]


# ========================================
# CMA-ES（协方差矩阵适应进化策略）
# ========================================

class CMAES:
    """
    CMA-ES: Covariance Matrix Adaptation Evolution Strategy

    【核心思想】
    1. 维护均值向量m和协方差矩阵C
    2. 协方差矩阵自适应：学习搜索空间的曲面结构
    3. 步长控制（σ）：基于PC路径长度
    4. 效率远超简单ES，尤其在病态条件数问题上

    【关键参数】
    - n: 维度
    - λ: 子代数量（种群大小）
    - m: 均值向量
    - σ: 全局步长
    - C: 协方差矩阵
    - pc: 进化路径（用于更新σ）
    - ps: 协方差矩阵路径
    """

    def __init__(self, func, dim, low, high, pop_size: Optional[int] = None,
                 seed: int = 42, verbose: bool = True):
        random.seed(seed)
        np.random.seed(seed)

        self.func = func
        self.dim = dim
        self.low = low
        self.high = high
        self.verbose = verbose

        # 建议种群大小：4 + floor(3*log(n))
        self.lambda_ = pop_size or (4 + int(3 * np.log(dim)))
        self.mu = self.lambda_ // 2  # 父代数

        # 权重（用于重组）
        self.weights = np.array([np.log(self.lambda_ / 2 + 0.5) - np.log(i + 1)
                                 for i in range(self.mu)])
        self.weights = self.weights / sum(self.weights)  # 归一化
        self.mu_eff = 1.0 / sum(self.weights ** 2)  # 有效μ

        # 均值
        self.mean = np.random.uniform(low, high, dim)

        # 步长
        self.sigma = 0.3 * (high - low)

        # 协方差矩阵初始化（单位阵）
        self.C = np.eye(dim)
        # 进化路径
        self.pc = np.zeros(dim)
        self.ps = np.zeros(dim)

        # 学习率
        self.cc = 4.0 / (dim + 4.0)  # pc学习率
        self.c_cov = 1.0 / (dim ** 2 + 6.0 / (dim ** 2 + 10.0))  # C学习率
        self.c_sigma = (self.mu_eff + 2.0) / (dim + self.mu_eff + 5.0)  # σ学习率
        self.d_sigma = 1.0 + self.c_sigma  # σ衰减因子

        # 常量
        self.chi_n = dim ** 0.5 * (1 - 1.0 / (4 * dim) + 1.0 / (21 * dim ** 2))

    def _sample_multivariate_normal(self) -> List[np.ndarray]:
        """从N(0, C)采样λ个个体"""
        samples = []
        for _ in range(self.lambda_):
            # Cholesky分解：C = A·A^T
            A = np.linalg.cholesky(self.C)
            z = np.random.randn(self.dim)
            sample = self.mean + self.sigma * A @ z
            sample = np.clip(sample, self.low, self.high)
            samples.append(sample)
        return samples

    def _update_hypothesis(self, samples: List[np.ndarray], fitness: List[float]):
        """更新均值、步长、协方差矩阵"""
        # 第1步：加权重组得到新均值
        sorted_idx = np.argsort(fitness)
        selected = [samples[i] for i in sorted_idx[:self.mu]]

        # 均值更新
        old_mean = self.mean.copy()
        self.mean = sum(w * x for w, x in zip(self.weights, selected))

        # 第2步：更新步长σ
        # 进化路径ps
        A_inv = np.linalg.inv(np.linalg.cholesky(self.C))
        self.ps = (1 - self.c_sigma) * self.ps + \
                  np.sqrt(self.c_sigma * (2 - self.c_sigma) * self.mu_eff) * \
                  A_inv @ (self.mean - old_mean) / self.sigma

        # σ更新
        self.sigma *= np.exp((self.c_sigma / self.d_sigma) *
                            (np.linalg.norm(self.ps) / self.chi_n - 1))

        # 第3步：更新协方差矩阵C
        # 进化路径pc
        self.pc = (1 - self.cc) * self.pc + \
                  np.sqrt(self.cc * (2 - self.cc) * self.mu_eff) * \
                  (self.mean - old_mean) / self.sigma

        # C更新（rank-μ更新）
        delta = (np.array(selected) - old_mean) / self.sigma
        rank_mu_update = sum(w * np.outer(delta[i], delta[i])
                            for i, w in enumerate(self.weights))
        self.C = (1 - self.c_cov) * self.C + \
                self.c_cov * (np.outer(self.pc, self.pc) +
                             (2 - self.c_cov) * rank_mu_update)

        # 确保对称正定
        self.C = (self.C + self.C.T) / 2
        eigvals = np.linalg.eigvalsh(self.C)
        if np.any(eigvals <= 0):
            self.C += np.eye(self.dim) * abs(min(eigvals)) * 1.1

    def optimize(self, max_generations: int = 500,
                tol: float = 1e-10) -> Tuple[np.ndarray, float]:
        """CMA-ES优化"""
        for gen in range(max_generations):
            # 采样
            samples = self._sample_multivariate_normal()
            fitness = [self.func(x) for x in samples]

            best_idx = np.argmin(fitness)
            best_fitness = fitness[best_idx]
            best_sample = samples[best_idx]

            if self.verbose and gen % 50 == 0:
                print(f"Gen {gen:4d}: best_fitness = {best_fitness:.8f}, "
                      f"sigma = {self.sigma:.4f}")

            if best_fitness < tol:
                break

            # 更新假设
            self._update_hypothesis(samples, fitness)

            # 步长边界
            range_ = self.high - self.low
            self.sigma = max(self.sigma, 1e-10)
            self.sigma = min(self.sigma, range_)

        return best_sample, best_fitness


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("进化策略 - 测试")
    print("=" * 50)

    # Sphere函数
    def sphere(x):
        return sum(xi**2 for xi in x)

    # Ellipsoid函数（病态）
    def ellipsoid(x):
        return sum((1000 ** (i / (len(x) - 1))) * x[i]**2 for i in range(len(x)))

    # Rosenbrock
    def rosenbrock(x):
        return sum(100 * (x[i+1] - x[i]**2)**2 + (x[i] - 1)**2 for i in range(len(x)-1))

    # 测试 (μ+λ)-ES
    print("\n【测试1】(10+100)-ES 优化Sphere (n=10)")
    es = EvolutionStrategy(func=sphere, dim=10, low=-100, high=100,
                          mu=10, lambda_=100, sigma=5.0, strategy="plus", verbose=True)
    best, fitness = es.optimize(max_generations=200)
    print(f"最优适应度: {fitness:.8f}")

    # 测试 CMA-ES
    print("\n【测试2】CMA-ES 优化Ellipsoid (n=10, 病态问题)")
    cma = CMAES(func=ellipsoid, dim=10, low=-10, high=10, verbose=True)
    best2, fitness2 = cma.optimize(max_generations=300)
    print(f"最优适应度: {fitness2:.8f}")

    # 测试 CMA-ES on Rosenbrock
    print("\n【测试3】CMA-ES 优化Rosenbrock (n=10)")
    cma2 = CMAES(func=rosenbrock, dim=10, low=-10, high=10, verbose=True)
    best3, fitness3 = cma2.optimize(max_generations=500)
    print(f"最优适应度: {fitness3:.6f}")

    print("\n" + "=" * 50)
    print("进化策略测试完成！")
    print("=" * 50)
