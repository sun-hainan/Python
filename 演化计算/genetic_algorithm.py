"""
遗传算法
==========================================

【算法原理】
模拟自然选择和遗传机制的优化算法。通过种群迭代，利用选择、交叉、变异
操作逐代进化出更优解。

【时间复杂度】O(generations × population_size × fitness_eval)
【空间复杂度】O(population_size × chromosome_length)

【应用场景】
- 函数优化（连续/离散）
- 组合优化（TSP、排程）
- 机器学习超参数调优
- 工程设计优化

【何时使用】
- 目标函数复杂、不可微
- 解空间大、搜索困难
- 需要全局最优而非局部
"""

import random
import numpy as np
from typing import List, Callable, Tuple


# ========================================
# 第1步：编码与初始化
# ========================================

def init_population(size: int, chrom_length: int, low: float, high: float) -> List[List[float]]:
    """
    随机初始化种群

    【参数】
    - size: 种群个体数
    - chrom_length: 染色体长度（决策变量数）
    - low/high: 变量取值范围
    """
    pop = []
    for _ in range(size):
        # 随机生成染色体（实数编码）
        chrom = [random.uniform(low, high) for _ in range(chrom_length)]
        pop.append(chrom)
    return pop


# ========================================
# 第2步：适应度评估
# ========================================

def evaluate(chrom: List[float], func: Callable) -> float:
    """
    计算个体适应度

    【注意】假设优化目标为最小化；若最大化则取负
    """
    return func(chrom)


def evaluate_population(population: List[List[float]], func: Callable) -> List[float]:
    """
    评估整个种群的适应度
    """
    return [evaluate(chrom, func) for chrom in population]


# ========================================
# 第3步：选择操作
# ========================================

def tournament_select(population: List[List[float]], fitness: List[float],
                    tournament_size: int = 3) -> List[float]:
    """
    锦标赛选择

    【原理】随机选k个个体， fitness最好的被选中
    - 优点：无需全局排序，适合并行
    - 参数tournament_size越大，选择压力越大
    """
    # 随机选择tournament_size个个体索引
    indices = random.sample(range(len(population)), tournament_size)
    # 找出其中适应度最好的
    best_idx = min(indices, key=lambda i: fitness[i])
    return population[best_idx]


def roulette_wheel_select(population: List[List[float]], fitness: List[float]) -> List[float]:
    """
    轮盘赌选择（Fitness Proportionate Selection）

    【原理】个体被选概率 ∝ 1/fitness（最小化问题）
    - 适应度越小（越优）被选概率越大
    """
    # 计算每个个体的选择权重（适应度取倒数）
    inv_fitness = [1.0 / max(f, 1e-10) for f in fitness]
    total = sum(inv_fitness)
    # 计算累积概率
    cumsum = 0.0
    r = random.random()
    for i, w in enumerate(inv_fitness):
        cumsum += w / total
        if r <= cumsum:
            return population[i]
    return population[-1]


# ========================================
# 第4步：交叉操作
# ========================================

def crossover(parent1: List[float], parent2: List[float],
             crossover_rate: float = 0.8) -> Tuple[List[float], List[float]]:
    """
    模拟二进制交叉（SBX, Simulated Binary Crossover）

    【原理】模拟连续空间中的单点交叉
    - 对于每个变量，用SBX公式产生两个子代
    """
    child1, child2 = parent1[:], parent2[:]

    if random.random() < crossover_rate:
        # 随机选择一个交叉点
        point = random.randint(0, len(parent1) - 1)
        # 单点交叉
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]

    return child1, child2


def blend_crossover(parent1: List[float], parent2: List[float],
                   alpha: float = 0.5) -> Tuple[List[float], List[float]]:
    """
    BLX-α混合交叉

    【原理】子代取值范围扩展到父代区间外
    [min(p1,p2)-α·d, max(p1,p2)+α·d]，d为父代距离
    """
    child1, child2 = [], []
    for i in range(len(parent1)):
        lo = min(parent1[i], parent2[i])
        hi = max(parent1[i], parent2[i])
        d = hi - lo
        # 扩展区间
        lo -= alpha * d
        hi += alpha * d
        child1.append(random.uniform(lo, hi))
        child2.append(random.uniform(lo, hi))
    return child1, child2


# ========================================
# 第5步：变异操作
# ========================================

def gaussian_mutate(chrom: List[float], mutation_rate: float = 0.1,
                   sigma: float = 0.1, low: float = -5.0, high: float = 5.0) -> List[float]:
    """
    高斯变异

    【原理】对每个基因以mutation_rate概率加高斯噪声
    噪声N(0, σ²)使解在邻域内扰动
    """
    mutated = chrom[:]
    for i in range(len(chrom)):
        if random.random() < mutation_rate:
            # 添加高斯噪声
            mutated[i] += random.gauss(0, sigma)
            # 边界处理
            mutated[i] = max(low, min(high, mutated[i]))
    return mutated


def polynomial_mutate(chrom: List[float], mutation_rate: float = 0.1,
                     eta: float = 20.0, low: float = -5.0, high: float = 5.0) -> List[float]:
    """
    多项式变异（用于模拟离散交叉如SBX配套）

    【原理】使用多项式概率分布生成变异偏移
    """
    mutated = chrom[:]
    for i in range(len(chrom)):
        if random.random() < mutation_rate:
            y = chrom[i]
            yl, yu = low, high
            # 计算delta
            if y > yl and y < yu:
                u = random.random()
                delta_l = (y - yl) / (yu - yl)
                delta_r = (yu - y) / (yu - yl)
                # 多项式变换
                if u <= 0.5:
                    delta = (2 * u + (1 - 2 * u) * (1 - delta_l) ** (eta + 1)) ** (1 / (eta + 1)) - 1
                else:
                    delta = 1 - (2 * (1 - u) + 2 * (u - 0.5) * (1 - delta_r) ** (eta + 1)) ** (1 / (eta + 1))
                y = y + delta * (yu - yl)
            mutated[i] = max(yl, min(yu, y))
    return mutated


# ========================================
# 第6步：GA主循环
# ========================================

def genetic_algorithm(func: Callable, dim: int, low: float = -5.0, high: float = 5.0,
                     pop_size: int = 100, generations: int = 500,
                     crossover_rate: float = 0.8, mutation_rate: float = 0.1,
                     elite_size: int = 2, tournament_size: int = 3,
                     verbose: bool = True) -> Tuple[List[float], float]:
    """
    遗传算法主流程

    【流程】
    1. 初始化种群
    2. 迭代generations代：
       a. 评估适应度
       b. 精英保留
       c. 锦标赛选择
       d. 交叉
       e. 变异
       f. 产生新种群
    3. 返回最优解

    【返回】最优解向量及其适应度
    """
    # 第1步：初始化
    population = init_population(pop_size, dim, low, high)

    # 记录最优
    best_chrom = None
    best_fitness = float('inf')

    for gen in range(generations):
        # 第2步：评估适应度
        fitness = evaluate_population(population, func)

        # 找当前代最优
        gen_best_idx = min(range(len(fitness)), key=lambda i: fitness[i])
        if fitness[gen_best_idx] < best_fitness:
            best_fitness = fitness[gen_best_idx]
            best_chrom = population[gen_best_idx][:]

        if verbose and gen % 50 == 0:
            print(f"Gen {gen:4d}: best_fitness = {best_fitness:.6f}")

        # 第3步：精英保留（保留最优个体直接进入下一代）
        elite = [population[i][:] for i in sorted(range(len(fitness)),
                                                  key=lambda i: fitness[i])[:elite_size]]

        # 第4步：生成新种群
        new_population = elite[:]

        while len(new_population) < pop_size:
            # 选择父代
            parent1 = tournament_select(population, fitness, tournament_size)
            parent2 = tournament_select(population, fitness, tournament_size)

            # 交叉
            child1, child2 = crossover(parent1, parent2, crossover_rate)

            # 变异
            child1 = gaussian_mutate(child1, mutation_rate, sigma=0.1, low=low, high=high)
            child2 = gaussian_mutate(child2, mutation_rate, sigma=0.1, low=low, high=high)

            new_population.extend([child1, child2])

        # 截断到pop_size
        population = new_population[:pop_size]

    return best_chrom, best_fitness


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("遗传算法 - 测试")
    print("=" * 50)

    # 测试函数1：Sphere函数（最小值在原点为0）
    def sphere(x):
        return sum(xi ** 2 for xi in x)

    # 测试函数2：Rosenbrock香蕉函数
    def rosenbrock(x):
        return sum(100 * (x[i+1] - x[i]**2)**2 + (x[i] - 1)**2 for i in range(len(x)-1))

    # 测试函数3： Rastrigrin函数（多峰）
    def rastrigrin(x):
        return 10 * len(x) + sum(xi**2 - 10 * np.cos(2 * np.pi * xi) for xi in x)

    # 优化Rosenbrock
    print("\n【测试】优化Rosenbrock函数 (n=10)")
    best, fitness = genetic_algorithm(
        func=rosenbrock,
        dim=10,
        low=-10.0,
        high=10.0,
        pop_size=100,
        generations=300,
        crossover_rate=0.9,
        mutation_rate=0.1,
        elite_size=2,
        tournament_size=3,
        verbose=True
    )
    print(f"\n最优解: {[f'{x:.4f}' for x in best[:5]]}...")
    print(f"最优适应度: {fitness:.6f}")

    # 优化Sphere
    print("\n【测试】优化Sphere函数 (n=5)")
    best2, fitness2 = genetic_algorithm(
        func=sphere,
        dim=5,
        low=-100.0,
        high=100.0,
        pop_size=50,
        generations=100,
        verbose=False
    )
    print(f"最优适应度: {fitness2:.6f} (理论最优=0)")

    print("\n" + "=" * 50)
    print("遗传算法测试完成！")
    print("=" * 50)
