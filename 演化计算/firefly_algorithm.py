"""
萤火虫算法（Firefly Algorithm, FA）
====================================

算法原理：
- 模拟萤火虫通过发光吸引同伴的自然行为
- 萤火虫的发光强度与适应度相关（越亮 = 适应度越好）
- 萤火虫会被更亮的同伴吸引而移动
- 光强随距离增加而指数衰减

核心机制：
- 吸引度（Attractiveness）：萤火虫之间的相互吸引程度
- 光强（Light Intensity）：萤火虫的亮度，由适应度决定
- 指数衰减：光强随距离增加而指数衰减

特点：
- 萤火虫之间的相互吸引实现了信息的充分交换
- 适合解决连续优化问题和组合优化问题
- 参数较少，主要有光强吸收系数和最大吸引度

参考文献：
- Yang, X.-S. (2008). Nature-Inspired Metaheuristic Algorithms.
- Luniver Press, 2008.
"""

import random
import math


class FireflyAlgorithm:
    """萤火虫算法核心类"""

    def __init__(self, func, dim, n_fireflies=30, max_iter=100,
                 bounds=(-5.0, 5.0), alpha=0.5, beta0=1.0, gamma=1.0):
        # 目标函数句柄
        self.func = func
        # 搜索空间维度
        self.dim = dim
        # 萤火虫种群数量
        self.n_fireflies = n_fireflies
        # 最大迭代次数
        self.max_iter = max_iter
        # 搜索边界
        self.lb = bounds[0]  # 下界
        self.ub = bounds[1]  # 上界
        # 随机扰动参数（步长因子的衰减系数）
        self.alpha = alpha
        # 最大吸引度（萤火虫间的最大吸引能力）
        self.beta0 = beta0
        # 光强吸收系数（控制光强衰减速度）
        self.gamma = gamma
        # 萤火虫位置列表
        self.fireflies = []
        # 萤火虫的光强（适应度）
        self.light_intensity = []
        # 全局最优萤火虫
        self.gbest = None
        # 全局最优光强
        self.gbest_intensity = float('inf')

    def initialize(self):
        """初始化萤火虫种群"""
        # 遍历每个萤火虫
        for _ in range(self.n_fireflies):
            # 随机生成维度为dim的位置
            position = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
            # 添加到萤火虫列表
            self.fireflies.append(position)
            # 计算该萤火虫的光强（目标函数值）
            light = self.func(position)
            self.light_intensity.append(light)
            # 更新全局最优
            if light < self.gbest_intensity:
                self.gbest_intensity = light
                self.gbest = position[:]

    def get_distance(self, firefly1, firefly2):
        """
        计算两个萤火虫之间的欧氏距离
        """
        # 初始化距离为0
        distance = 0.0
        # 遍历每个维度
        for i in range(self.dim):
            # 累加各维度距离的平方
            diff = firefly1[i] - firefly2[i]
            distance += diff * diff
        # 返回欧氏距离（欧几里得距离的平方根）
        return math.sqrt(distance)

    def get_attractiveness(self, distance):
        """
        计算萤火虫之间的吸引度（基于距离的指数衰减）
        吸引度公式：β = β0 * exp(-γ * r^2)
        """
        # 使用指数衰减模型计算吸引度
        return self.beta0 * math.exp(-self.gamma * distance * distance)

    def move_towards(self, firefly_i, firefly_j):
        """
        萤火虫i被更亮的萤火虫j吸引而移动
        移动公式：xi = xi + β * (xj - xi) + α * (rand - 0.5)
        """
        # 创建新位置副本
        new_firefly = firefly_i[:]
        # 计算萤火虫i和j之间的距离
        distance = self.get_distance(firefly_i, firefly_j)
        # 计算吸引度
        beta = self.get_attractiveness(distance)
        # 对每个维度进行移动
        for k in range(self.dim):
            # 随机扰动因子（-0.5到0.5之间）
            epsilon = random.uniform(-0.5, 0.5)
            # 萤火虫向更亮的萤火虫移动，并加入随机扰动
            new_firefly[k] = (firefly_i[k] +
                             beta * (firefly_j[k] - firefly_i[k]) +
                             self.alpha * epsilon)
        return new_firefly

    def optimize(self):
        """执行完整的萤火虫算法优化流程"""
        # 阶段1：初始化萤火虫种群
        self.initialize()
        # 记录初始最优适应度
        best_intensity = self.gbest_intensity
        # 记录迭代历史
        history = [best_intensity]

        print("  迭代   0 | 最优适应度: {:.8f}".format(best_intensity))

        # 主循环：迭代优化
        for iteration in range(self.max_iter):
            # 当前迭代的随机扰动因子（随迭代递减）
            alpha_t = self.alpha * (0.9 ** iteration)

            # 阶段2：两两比较萤火虫，亮者吸引暗者移动
            for i in range(self.n_fireflies):
                for j in range(self.n_fireflies):
                    # 如果萤火虫j比萤火虫i更亮（适应度更好）
                    if self.light_intensity[j] < self.light_intensity[i]:
                        # 萤火虫i向萤火虫j移动
                        new_firefly = self.move_towards(
                            self.fireflies[i],
                            self.fireflies[j]
                        )
                        # 边界处理：确保新位置在搜索范围内
                        new_firefly = [max(self.lb, min(self.ub, x)) for x in new_firefly]
                        # 计算新位置的光强
                        new_light = self.func(new_firefly)
                        # 如果新位置更优，则更新
                        if new_light < self.light_intensity[i]:
                            self.fireflies[i] = new_firefly
                            self.light_intensity[i] = new_light
                            # 更新全局最优
                            if new_light < self.gbest_intensity:
                                self.gbest_intensity = new_light
                                self.gbest = new_firefly[:]

            # 阶段3：随机扰动阶段（模拟探索新区域）
            for i in range(self.n_fireflies):
                # 以一定概率对萤火虫进行随机扰动
                if random.random() < 0.1:
                    new_firefly = self.fireflies[i][:]
                    k = random.randint(0, self.dim - 1)
                    # 随机选择一个维度进行扰动
                    new_firefly[k] += alpha_t * random.uniform(-0.5, 0.5)
                    # 边界处理
                    new_firefly[k] = max(self.lb, min(self.ub, new_firefly[k]))
                    # 评估并更新
                    new_light = self.func(new_firefly)
                    if new_light < self.light_intensity[i]:
                        self.fireflies[i] = new_firefly
                        self.light_intensity[i] = new_light
                        if new_light < self.gbest_intensity:
                            self.gbest_intensity = new_light
                            self.gbest = new_firefly[:]

            # 记录当前最优光强
            best_intensity = self.gbest_intensity
            history.append(best_intensity)

            # 打印迭代进度
            if (iteration + 1) % 20 == 0:
                print(f"  迭代 {iteration + 1:3d} | 最优适应度: {best_intensity:.8f}")

        return self.gbest, self.gbest_intensity, history


def sphere(x):
    """测试函数：Sphere函数（最简单的单峰测试函数）"""
    return sum(xi ** 2 for xi in x)


def rastrigin(x):
    """测试函数：Rastrigin函数（多峰函数，具有大量局部最优）"""
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


def ackley(x):
    """测试函数：Ackley函数（广泛使用的多峰测试函数）"""
    n = len(x)
    # 第一项
    sum1 = sum(xi ** 2 for xi in x)
    # 第二项
    sum2 = sum(math.cos(2 * math.pi * xi) for xi in x)
    # Ackley函数公式
    return (-20 * math.exp(-0.2 * math.sqrt(sum1 / n)) -
            math.exp(sum2 / n) + 20 + math.e)


if __name__ == "__main__":
    # 设置随机种子以保证结果可复现
    random.seed(42)

    print("=" * 60)
    print("萤火虫算法（FA）测试")
    print("=" * 60)

    # 测试函数列表
    test_functions = [
        ("Sphere函数", sphere, 30),       # 单峰函数
        ("Rastrigin函数", rastrigin, 20),  # 多峰函数
        ("Ackley函数", ackley, 20),       # 多峰函数
    ]

    # 算法参数设置
    n_fireflies = 30  # 萤火虫数量
    max_iter = 100  # 最大迭代次数
    alpha = 0.5  # 随机扰动参数
    beta0 = 1.0  # 最大吸引度
    gamma = 1.0  # 光强吸收系数

    # 对每个测试函数运行FA算法
    for name, func, dim in test_functions:
        print(f"\n测试函数: {name} (维度={dim})")
        print("-" * 40)

        # 创建FA算法实例
        fa = FireflyAlgorithm(
            func=func,
            dim=dim,
            n_fireflies=n_fireflies,
            max_iter=max_iter,
            bounds=(-5.12, 5.12),
            alpha=alpha,
            beta0=beta0,
            gamma=gamma
        )

        # 执行优化
        best_solution, best_fitness, history = fa.optimize()

        # 输出结果
        print(f"\n  最优适应度: {best_fitness:.8f}")
        print(f"  解向量前5维: {[f'{v:.4f}' for v in best_solution[:5]]}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
