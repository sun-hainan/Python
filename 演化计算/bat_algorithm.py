"""
蝙蝠算法（Bat Algorithm, BA）
==============================

算法原理：
- 模拟蝙蝠回声定位（echolocation）行为进行优化搜索
- 蝙蝠通过发出超声波并接收回声来探测猎物和导航
- 算法结合了频率调节、响度控制和脉冲发射率自适应

核心机制：
- 频率调节：每只蝙蝠有自己的飞行频率，调节搜索范围
- 响度（ Loudness ）：蝙蝠发出声音的响度，随迭代递减
- 脉冲率（Pulse Rate）：蝙蝠发射脉冲的频率，随迭代递增
- 局部搜索：当蝙蝠接近猎物时进行精细搜索

特点：
- 结合了粒子群优化的速度更新和遗传算法的选择机制
- 参数自适应：响度和脉冲率随迭代动态调整
- 全局搜索与局部搜索平衡

参考文献：
- Yang, X.-S. (2010). A New Metaheuristic Bat-Inspired Algorithm.
- Nature Inspired Cooperative Strategies for Optimization (NICSO 2010).
"""

import random
import math


class BatAlgorithm:
    """蝙蝠算法核心类"""

    def __init__(self, func, dim, n_bats=30, max_iter=100,
                 bounds=(-5.0, 5.0), f_min=0.0, f_max=2.0,
                 A0=0.9, r0=0.5, alpha=0.9, gamma=0.9):
        # 目标函数句柄
        self.func = func
        # 搜索空间维度
        self.dim = dim
        # 蝙蝠种群数量
        self.n_bats = n_bats
        # 最大迭代次数
        self.max_iter = max_iter
        # 搜索边界
        self.lb = bounds[0]  # 下界
        self.ub = bounds[1]  # 上界
        # 最小频率
        self.f_min = f_min
        # 最大频率
        self.f_max = f_max
        # 初始响度（最大响度）
        self.A0 = A0
        # 初始脉冲率（最小脉冲率）
        self.r0 = r0
        # 响度衰减系数（每代递减）
        self.alpha = alpha
        # 脉冲率增强系数（每代递增）
        self.gamma = gamma
        # 蝙蝠位置列表
        self.bats = []
        # 蝙蝠速度列表
        self.velocities = []
        # 蝙蝠频率列表
        self.frequencies = []
        # 蝙蝠响度列表
        self.A = []
        # 蝙蝠脉冲率列表
        self.r = []
        # 适应度值列表
        self.fitness = []
        # 全局最优解
        self.gbest = None
        # 全局最优适应度
        self.gbest_fitness = float('inf')

    def initialize(self):
        """初始化蝙蝠种群"""
        # 遍历每个蝙蝠
        for i in range(self.n_bats):
            # 随机生成维度为dim的位置
            position = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
            # 添加到蝙蝠列表
            self.bats.append(position)
            # 随机生成初始速度（用于频率调节）
            velocity = [0.0] * self.dim
            self.velocities.append(velocity)
            # 初始化频率（均匀分布在[f_min, f_max]）
            frequency = self.f_min + (self.f_max - self.f_min) * random.uniform(0, 1)
            self.frequencies.append(frequency)
            # 初始化响度
            self.A.append(self.A0)
            # 初始化脉冲率
            self.r.append(self.r0)
            # 计算该蝙蝠的适应度
            fitness = self.func(position)
            self.fitness.append(fitness)
            # 更新全局最优
            if fitness < self.gbest_fitness:
                self.gbest_fitness = fitness
                self.gbest = position[:]

    def update_frequency(self, i, gbest):
        """
        更新蝙蝠i的频率
        频率更新公式：fi = fmin + (fmax - fmin) * β
        其中β为[0,1]之间的随机数
        """
        # 生成[0,1]之间的随机数
        beta = random.uniform(0, 1)
        # 更新频率：基于当前最优解的位置更新
        self.frequencies[i] = self.f_min + (self.f_max - self.f_min) * beta

    def update_velocity_and_position(self, i, gbest):
        """
        更新蝙蝠i的速度和位置
        速度更新公式：vi(t+1) = vi(t) + (xi(t) - gbest) * fi
        位置更新公式：xi(t+1) = xi(t) + vi(t+1)
        """
        # 获取当前蝙蝠位置和速度
        bat = self.bats[i]
        velocity = self.velocities[i]
        # 获取当前频率
        freq = self.frequencies[i]

        # 临时新位置
        new_bat = bat[:]
        # 对每个维度更新速度和位置
        for j in range(self.dim):
            # 速度更新
            velocity[j] += (bat[j] - gbest[j]) * freq
            # 位置更新
            new_bat[j] += velocity[j]

        return new_bat

    def local_search(self, i, gbest):
        """
        局部搜索：在当前最优解附近进行精细搜索
        使用脉冲率来决定是否执行局部搜索
        """
        # 当前蝙蝠的平均响度（用于衡量搜索精度）
        avg_loudness = sum(self.A) / self.n_bats

        # 生成新解
        new_bat = self.bats[i][:]
        # 在当前最优解附近随机生成新位置
        for j in range(self.dim):
            # 局部搜索公式：xi = gbest + ε * A_i
            epsilon = random.uniform(-1, 1)
            new_bat[j] = gbest[j] + epsilon * self.A[i]

        return new_bat

    def optimize(self):
        """执行完整的蝙蝠算法优化流程"""
        # 阶段1：初始化蝙蝠种群
        self.initialize()
        # 记录初始最优适应度
        best_fitness = self.gbest_fitness
        # 记录迭代历史
        history = [best_fitness]

        print("  迭代   0 | 最优适应度: {:.8f}".format(best_fitness))

        # 主循环：迭代优化
        for iteration in range(self.max_iter):
            # 阶段2：遍历所有蝙蝠进行位置更新
            for i in range(self.n_bats):
                # 更新频率
                self.update_frequency(i, self.gbest)
                # 更新速度和位置得到新解
                new_bat = self.update_velocity_and_position(i, self.gbest)

                # 边界处理：确保新位置在搜索范围内
                new_bat = [max(self.lb, min(self.ub, x)) for x in new_bat]

                # 生成随机数决定是否进行局部搜索
                rand = random.random()
                # 如果随机数大于当前脉冲率，执行局部搜索
                if rand > self.r[i]:
                    new_bat = self.local_search(i, self.gbest)
                    # 边界处理
                    new_bat = [max(self.lb, min(self.ub, x)) for x in new_bat]

                # 计算新解的适应度
                new_fitness = self.func(new_bat)

                # 选择策略：基于响度和适应度进行贪婪选择
                # 响度越大（A_i越大），越容易接受较差的解
                if new_fitness < self.fitness[i] and random.random() < self.A[i]:
                    # 更新蝙蝠位置
                    self.bats[i] = new_bat
                    self.fitness[i] = new_fitness
                    # 响度衰减
                    self.A[i] *= self.alpha
                    # 脉冲率增强
                    self.r[i] = self.r0 * (1 - math.exp(-self.gamma * iteration))

                    # 更新全局最优
                    if new_fitness < self.gbest_fitness:
                        self.gbest_fitness = new_fitness
                        self.gbest = new_bat[:]

            # 记录当前最优适应度
            best_fitness = self.gbest_fitness
            history.append(best_fitness)

            # 打印迭代进度
            if (iteration + 1) % 20 == 0:
                print(f"  迭代 {iteration + 1:3d} | 最优适应度: {best_fitness:.8f}")

        return self.gbest, self.gbest_fitness, history


def sphere(x):
    """测试函数：Sphere函数（最简单的单峰测试函数）"""
    return sum(xi ** 2 for xi in x)


def rastrigin(x):
    """测试函数：Rastrigin函数（多峰函数，具有大量局部最优）"""
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


def zakharov(x):
    """测试函数：Zakharov函数（低维多峰函数）"""
    n = len(x)
    sum1 = sum(xi ** 2 for xi in x)
    sum2 = sum(0.5 * (i + 1) * xi for i, xi in enumerate(x))
    return sum1 + sum2 ** 2 + sum2 ** 4


if __name__ == "__main__":
    # 设置随机种子以保证结果可复现
    random.seed(42)

    print("=" * 60)
    print("蝙蝠算法（BA）测试")
    print("=" * 60)

    # 测试函数列表
    test_functions = [
        ("Sphere函数", sphere, 30),       # 单峰函数
        ("Rastrigin函数", rastrigin, 20),  # 多峰函数
        ("Zakharov函数", zakharov, 20),   # 多峰函数
    ]

    # 算法参数设置
    n_bats = 30  # 蝙蝠数量
    max_iter = 100  # 最大迭代次数
    f_min = 0.0  # 最小频率
    f_max = 2.0  # 最大频率
    A0 = 0.9  # 初始响度
    r0 = 0.5  # 初始脉冲率
    alpha = 0.9  # 响度衰减系数
    gamma = 0.9  # 脉冲率增强系数

    # 对每个测试函数运行BA算法
    for name, func, dim in test_functions:
        print(f"\n测试函数: {name} (维度={dim})")
        print("-" * 40)

        # 创建BA算法实例
        ba = BatAlgorithm(
            func=func,
            dim=dim,
            n_bats=n_bats,
            max_iter=max_iter,
            bounds=(-5.0, 5.0),
            f_min=f_min,
            f_max=f_max,
            A0=A0,
            r0=r0,
            alpha=alpha,
            gamma=gamma
        )

        # 执行优化
        best_solution, best_fitness, history = ba.optimize()

        # 输出结果
        print(f"\n  最优适应度: {best_fitness:.8f}")
        print(f"  解向量前5维: {[f'{v:.4f}' for v in best_solution[:5]]}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
