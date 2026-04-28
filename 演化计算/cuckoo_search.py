"""
布谷鸟搜索算法（Cuckoo Search, CS）
=====================================

算法原理：
- 模拟布谷鸟（Cuckoo）鸟类的寄生孵化行为
- 布谷鸟将蛋产在其他鸟巢中，让其他鸟类代为孵化
- 鸟巢主人可能发现外来蛋并抛弃，或孵化出雏鸟
- 布谷鸟雏鸟通过模仿宿主雏鸟的行为来获得食物

核心机制：
- Lévy飞行：布谷鸟使用Lévy分布进行长距离随机搜索
- 寄生巢穴：解表示为鸟巢/宿主巢穴，布谷鸟寄生产卵
- 保留最优：保留当前发现的最优解（ nests_best ）

特点：
- Lévy飞行使搜索具有长距离跳跃能力
- 参数少，仅需设置种群规模和发现概率
- 全局搜索能力强，收敛速度较快

参考文献：
- Yang, X.-S., & Deb, S. (2009). Cuckoo search via Lévy flights.
- Nature & Biologically Inspired Computing, 2009.
"""

import random
import math
import numpy as np


class CuckooSearch:
    """布谷鸟搜索算法核心类"""

    def __init__(self, func, dim, n_nests=25, max_iter=100, bounds=(-5.0, 5.0),
                 pa=0.25, levy_factor=1.5):
        # 目标函数句柄
        self.func = func
        # 搜索空间维度
        self.dim = dim
        # 鸟巢数量（种群规模）
        self.n_nests = n_nests
        # 最大迭代次数
        self.max_iter = max_iter
        # 搜索边界
        self.lb = bounds[0]  # 下界
        self.ub = bounds[1]  # 上界
        # 发现概率（宿主发现布谷鸟蛋的概率）
        self.pa = pa
        # Lévy飞行的稳定参数（通常取1.0~2.0）
        self.levy_factor = levy_factor
        # 鸟巢位置列表
        self.nests = []
        # 鸟巢的适应度值
        self.fitness = []
        # 全局最优鸟巢
        self.gbest = None
        # 全局最优适应度
        self.gbest_fitness = float('inf')

    def initialize(self):
        """初始化鸟巢种群"""
        # 遍历每个鸟巢
        for _ in range(self.n_nests):
            # 随机生成维度为dim的解向量
            nest = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
            # 添加到鸟巢列表
            self.nests.append(nest)
            # 计算该鸟巢的适应度
            fitness = self.func(nest)
            self.fitness.append(fitness)
            # 更新全局最优
            if fitness < self.gbest_fitness:
                self.gbest_fitness = fitness
                self.gbest = nest[:]

    def levy_flight(self, step_size=0.01):
        """
        Lévy飞行：生成符合Lévy分布的随机步长
        使用Mantegna算法近似模拟Lévy分布
        """
        # 随机选择Lévy飞行参数（稳定分布参数）
        beta = self.levy_factor
        # 计算σ_u（标准差相关参数）
        sigma_u = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2) /
                   (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
        # 生成两个标准正态随机数
        u = random.gauss(0, sigma_u)
        v = random.gauss(0, 1)
        # 计算Lévy步长
        step = u / (abs(v) ** (1 / beta))
        return step

    def get_cuckoo(self, nest, step_size=0.01):
        """
        通过Lévy飞行从给定鸟巢产生新的布谷鸟解
        """
        # 记录原始位置用于后续更新
        new_nest = nest[:]
        # 对每个维度进行Lévy飞行扰动
        for j in range(self.dim):
            # 生成Lévy飞行步长
            step = self.levy_flight(step_size)
            # 新位置 = 原位置 + Lévy步长 * 随机缩放因子
            new_nest[j] = nest[j] + step * step_size * random.uniform(-1, 1)
        return new_nest

    def evaluate_and_update(self, new_nest):
        """
        评估新解并在必要时更新种群
        """
        # 计算新解的适应度
        new_fitness = self.func(new_nest)
        # 随机选择一个鸟巢进行贪婪选择
        k = random.randint(0, self.n_nests - 1)
        # 如果新解更优，则替换原鸟巢
        if new_fitness < self.fitness[k]:
            self.nests[k] = new_nest[:]
            self.fitness[k] = new_fitness
            # 更新全局最优
            if new_fitness < self.gbest_fitness:
                self.gbest_fitness = new_fitness
                self.gbest = new_nest[:]

    def abandon_nests(self):
        """
        发现阶段：部分较差的鸟巢被抛弃，重新随机生成
        模拟宿主发现外来蛋并抛弃的行为
        """
        # 按发现概率随机抛弃部分鸟巢
        for i in range(self.n_nests):
            # 生成[0,1]之间的随机数，决定是否抛弃该鸟巢
            if random.random() < self.pa:
                # 随机生成一个新的鸟巢位置
                new_nest = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
                # 评估并更新
                new_fitness = self.func(new_nest)
                if new_fitness < self.fitness[i]:
                    self.nests[i] = new_nest
                    self.fitness[i] = new_fitness
                    if new_fitness < self.gbest_fitness:
                        self.gbest_fitness = new_fitness
                        self.gbest = new_nest[:]

    def optimize(self):
        """执行完整的布谷鸟搜索优化流程"""
        # 阶段1：初始化鸟巢种群
        self.initialize()
        # 记录初始最优适应度
        best_fitness = self.gbest_fitness
        # 记录迭代历史
        history = [best_fitness]

        print("  迭代   0 | 最优适应度: {:.8f}".format(best_fitness))

        # 主循环：迭代优化
        for iteration in range(self.max_iter):
            # 阶段2：让每个布谷鸟通过Lévy飞行搜索新解
            for nest in self.nests:
                # 通过Lévy飞行生成新的布谷鸟解
                new_nest = self.get_cuckoo(nest)
                # 边界处理：确保解在搜索范围内
                new_nest = [max(self.lb, min(self.ub, x)) for x in new_nest]
                # 评估并贪婪选择更新
                self.evaluate_and_update(new_nest)

            # 阶段3：发现阶段 - 抛弃部分较差的鸟巢
            self.abandon_nests()

            # 阶段4：按适应度排序，保留最优的鸟巢
            # 将适应度和鸟巢配对
            paired = list(zip(self.fitness, self.nests))
            # 按适应度升序排序（越小越优）
            paired.sort(key=lambda x: x[0])
            # 更新记录
            self.fitness = [p[0] for p in paired]
            self.nests = [p[1][:] for p in paired]
            # 更新全局最优
            if self.fitness[0] < self.gbest_fitness:
                self.gbest_fitness = self.fitness[0]
                self.gbest = self.nests[0][:]

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


def griewank(x):
    """测试函数：Griewank函数（多峰函数，具有大量局部最优）"""
    sum_term = sum(xi ** 2 for xi in x) / 4000
    prod_term = 1
    for i, xi in enumerate(x):
        prod_term *= math.cos(xi / math.sqrt(i + 1))
    return sum_term - prod_term + 1


def rosenbrock(x):
    """测试函数：Rosenbrock函数（经典优化测试函数）"""
    total = 0
    for i in range(len(x) - 1):
        total += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
    return total


if __name__ == "__main__":
    # 设置随机种子以保证结果可复现
    random.seed(42)
    np.random.seed(42)

    print("=" * 60)
    print("布谷鸟搜索算法（CS）测试")
    print("=" * 60)

    # 测试函数列表
    test_functions = [
        ("Sphere函数", sphere, 30),       # 单峰函数
        ("Griewank函数", griewank, 20),    # 多峰函数
        ("Rosenbrock函数", rosenbrock, 10),  # 病态函数
    ]

    # 算法参数设置
    n_nests = 25  # 鸟巢数量
    max_iter = 100  # 最大迭代次数
    pa = 0.25  # 发现概率

    # 对每个测试函数运行CS算法
    for name, func, dim in test_functions:
        print(f"\n测试函数: {name} (维度={dim})")
        print("-" * 40)

        # 创建CS算法实例
        cs = CuckooSearch(
            func=func,
            dim=dim,
            n_nests=n_nests,
            max_iter=max_iter,
            bounds=(-5.0, 5.0),
            pa=pa
        )

        # 执行优化
        best_solution, best_fitness, history = cs.optimize()

        # 输出结果
        print(f"\n  最优适应度: {best_fitness:.8f}")
        print(f"  解向量前5维: {[f'{v:.4f}' for v in best_solution[:5]]}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
