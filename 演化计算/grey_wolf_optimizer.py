"""
灰狼优化算法（Grey Wolf Optimizer, GWO）
==========================================

算法原理：
- 模拟灰狼（Grey Wolf）的社会等级和捕猎行为
- 灰狼群体具有严格的社会等级：α（首领）> β（副首领）> δ（侦察兵）> ω（普通狼）
- α、β、δ领导整个群体的捕猎活动
- ω狼跟随前三者行动

核心机制：
- αβδ狼群结构：保留当前种群中最好的三只狼作为领导
- 包围（Encircling）猎物：狼群逐渐包围猎物
- 攻击（Attacking）猎物：狼群发起最终攻击
- 搜索（Searching）猎物：寻找并追踪猎物

特点：
- 参数少，仅需设置种群规模和最大迭代次数
- 结构简单，易于理解和实现
- 全局搜索能力强，收敛速度较快

参考文献：
- Mirjalili, S., Mirjalili, S. M., & Lewis, A. (2014).
  Grey Wolf Optimizer. Advances in Engineering Software, 69, 46-61.
"""

import random
import math


class GreyWolfOptimizer:
    """灰狼优化算法核心类"""

    def __init__(self, func, dim, n_wolves=30, max_iter=100, bounds=(-5.0, 5.0)):
        # 目标函数句柄
        self.func = func
        # 搜索空间维度
        self.dim = dim
        # 灰狼种群数量
        self.n_wolves = n_wolves
        # 最大迭代次数
        self.max_iter = max_iter
        # 搜索边界
        self.lb = bounds[0]  # 下界
        self.ub = bounds[1]  # 上界
        # 灰狼位置列表
        self.wolves = []
        # 灰狼适应度值列表
        self.fitness = []
        # α狼（最优解）
        self.alpha = None
        # α适应度
        self.alpha_fitness = float('inf')
        # β狼（次优解）
        self.beta = None
        # β适应度
        self.beta_fitness = float('inf')
        # δ狼（第三优解）
        self.delta = None
        # δ适应度
        self.delta_fitness = float('inf')

    def initialize(self):
        """初始化灰狼种群"""
        # 遍历每个灰狼
        for _ in range(self.n_wolves):
            # 随机生成维度为dim的位置
            position = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
            # 添加到灰狼列表
            self.wolves.append(position)
            # 计算该灰狼的适应度
            fitness = self.func(position)
            self.fitness.append(fitness)

        # 初始化后选择α、β、δ
        self.update_alpha_beta_delta()

    def update_alpha_beta_delta(self):
        """
        更新α、β、δ狼
        按适应度排序，选择最优的三只作为领导者
        """
        # 将适应度和灰狼配对
        paired = list(zip(self.fitness, self.wolves))
        # 按适应度升序排序
        paired.sort(key=lambda x: x[0])

        # 更新α狼（最优）
        self.alpha_fitness = paired[0][0]
        self.alpha = paired[0][1][:]
        # 更新β狼（次优）
        if len(paired) > 1:
            self.beta_fitness = paired[1][0]
            self.beta = paired[1][1][:]
        # 更新δ狼（第三优）
        if len(paired) > 2:
            self.delta_fitness = paired[2][0]
            self.delta = paired[2][1][:]

    def update_position(self, wolf, leader, a, c):
        """
        根据领导狼更新灰狼位置
        位置更新公式：
        D = |C * Leader_pos - wolf_pos|
        wolf_pos = Leader_pos - A * D
        """
        # 创建新位置副本
        new_position = wolf[:]
        # 对每个维度进行更新
        for j in range(self.dim):
            # 计算距离：Dj = |Cj * Leaderj - xij|
            r1 = random.random()  # [0,1]随机数
            r2 = random.random()  # [0,1]随机数
            # 位置更新
            new_position[j] = leader[j] - a * (2 * r1 - 1) * (leader[j] - wolf[j])
        return new_position

    def optimize(self):
        """执行完整的灰狼优化流程"""
        # 阶段1：初始化灰狼种群
        self.initialize()
        # 记录初始最优适应度
        best_fitness = self.alpha_fitness
        # 记录迭代历史
        history = [best_fitness]

        print("  迭代   0 | 最优适应度: {:.8f}".format(best_fitness))

        # 主循环：迭代优化
        for iteration in range(self.max_iter):
            # 阶段2：线性递减参数a（从2递减到0）
            # a从2线性递减到0，控制探索与开发平衡
            a = 2 - 2 * (iteration / self.max_iter)

            # 阶段3：更新每只灰狼的位置
            for i in range(self.n_wolves):
                # 获取当前灰狼位置
                wolf = self.wolves[i]

                # 更新位置受α影响
                new_pos_alpha = self.update_position(wolf, self.alpha, a, 0)
                # 更新位置受β影响
                new_pos_beta = self.update_position(wolf, self.beta, a, 0)
                # 更新位置受δ影响
                new_pos_delta = self.update_position(wolf, self.delta, a, 0)

                # 综合三种影响，计算最终位置
                new_position = wolf[:]
                for j in range(self.dim):
                    # 取三个方向向量的平均值
                    new_position[j] = ((new_pos_alpha[j] + new_pos_beta[j] + new_pos_delta[j]) / 3.0)

                # 边界处理
                new_position = [max(self.lb, min(self.ub, x)) for x in new_position]

                # 计算新位置的适应度
                new_fitness = self.func(new_position)

                # 如果新位置更优，则更新
                if new_fitness < self.fitness[i]:
                    self.wolves[i] = new_position
                    self.fitness[i] = new_fitness

            # 阶段4：更新α、β、δ狼
            self.update_alpha_beta_delta()

            # 记录当前最优适应度
            best_fitness = self.alpha_fitness
            history.append(best_fitness)

            # 打印迭代进度
            if (iteration + 1) % 20 == 0:
                print(f"  迭代 {iteration + 1:3d} | 最优适应度: {best_fitness:.8f}")

        return self.alpha, self.alpha_fitness, history


def sphere(x):
    """测试函数：Sphere函数（最简单的单峰测试函数）"""
    return sum(xi ** 2 for xi in x)


def rastrigin(x):
    """测试函数：Rastrigin函数（多峰函数，具有大量局部最优）"""
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


def schwefel(x):
    """测试函数：Schwefel函数（复杂的山谷形函数）"""
    n = len(x)
    return 418.9829 * n - sum(xi * math.sin(math.sqrt(abs(xi))) for xi in x)


if __name__ == "__main__":
    # 设置随机种子以保证结果可复现
    random.seed(42)

    print("=" * 60)
    print("灰狼优化算法（GWO）测试")
    print("=" * 60)

    # 测试函数列表
    test_functions = [
        ("Sphere函数", sphere, 30),       # 单峰函数
        ("Rastrigin函数", rastrigin, 20),  # 多峰函数
        ("Schwefel函数", schwefel, 10),   # 复杂函数
    ]

    # 算法参数设置
    n_wolves = 30  # 灰狼数量
    max_iter = 100  # 最大迭代次数

    # 对每个测试函数运行GWO算法
    for name, func, dim in test_functions:
        print(f"\n测试函数: {name} (维度={dim})")
        print("-" * 40)

        # 创建GWO算法实例
        gwo = GreyWolfOptimizer(
            func=func,
            dim=dim,
            n_wolves=n_wolves,
            max_iter=max_iter,
            bounds=(-5.12, 5.12)
        )

        # 执行优化
        best_solution, best_fitness, history = gwo.optimize()

        # 输出结果
        print(f"\n  最优适应度: {best_fitness:.8f}")
        print(f"  解向量前5维: {[f'{v:.4f}' for v in best_solution[:5]]}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
