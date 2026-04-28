"""
鲸鱼优化算法（Whale Optimization Algorithm, WOA）
==================================================

算法原理：
- 模拟座头鲸（Humpback Whale）的捕食行为——气泡网捕食法（Bubble-net foraging）
- 座头鲸会绕着猎物旋转并吐出气泡，形成螺旋气泡网将猎物逼至水面
- 鲸鱼群通过收缩包围和螺旋上升两种策略协同捕猎

核心机制：
- 包围（Encircling）猎物：鲸鱼群包围猎物
- 气泡网捕食（ Bubble-net attacking ）：
  - 收缩包围：通过减小参数a来缩小包围圈
  - 螺旋位置更新：模拟鲸鱼的螺旋运动
- 搜索（Search for prey）：随机搜索猎物

特点：
- 参数少，仅需设置种群规模和最大迭代次数
- 收缩包围和螺旋机制平衡全局与局部搜索
- 实现简单，效果良好

参考文献：
- Mirjalili, S., & Lewis, A. (2016).
  The Whale Optimization Algorithm. Advances in Engineering Software, 95, 51-67.
"""

import random
import math


class WhaleOptimizationAlgorithm:
    """鲸鱼优化算法核心类"""

    def __init__(self, func, dim, n_whales=30, max_iter=100, bounds=(-5.0, 5.0)):
        # 目标函数句柄
        self.func = func
        # 搜索空间维度
        self.dim = dim
        # 鲸鱼种群数量
        self.n_whales = n_whales
        # 最大迭代次数
        self.max_iter = max_iter
        # 搜索边界
        self.lb = bounds[0]  # 下界
        self.ub = bounds[1]  # 上界
        # 鲸鱼位置列表
        self.whales = []
        # 鲸鱼适应度值列表
        self.fitness = []
        # 全局最优解（最佳鲸鱼位置）
        self.gbest = None
        # 全局最优适应度
        self.gbest_fitness = float('inf')

    def initialize(self):
        """初始化鲸鱼种群"""
        # 遍历每个鲸鱼
        for _ in range(self.n_whales):
            # 随机生成维度为dim的位置
            position = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
            # 添加到鲸鱼列表
            self.whales.append(position)
            # 计算该鲸鱼的适应度
            fitness = self.func(position)
            self.fitness.append(fitness)
            # 更新全局最优
            if fitness < self.gbest_fitness:
                self.gbest_fitness = fitness
                self.gbest = position[:]

    def update_position(self, whale, leader, a, p, b=1.0):
        """
        根据鲸鱼角色（搜索或包围）更新位置
        """
        # 获取当前鲸鱼位置
        current = whale[:]
        # 获取领导者位置
        X_star = leader[:]

        # 生成[0,1]之间的随机数
        r = random.random()
        # 计算距离 |X* - X|
        distance = [X_star[j] - current[j] for j in range(self.dim)]

        if p < 0.5:
            # 包围阶段：基于参数a进行位置更新
            if abs(a) < 1:
                # 收缩包围：X(t+1) = X* - A * D
                A = 2 * a * random.random() - a
                C = 2 * random.random()
                new_whale = whale[:]
                for j in range(self.dim):
                    D = abs(C * X_star[j] - whale[j])
                    new_whale[j] = X_star[j] - A * D
            else:
                # 搜索阶段：随机选择一个鲸鱼作为领导者
                random_whale = random.choice(self.whales)
                A = 2 * a * random.random() - a
                C = 2 * random.random()
                new_whale = whale[:]
                for j in range(self.dim):
                    D = abs(C * random_whale[j] - whale[j])
                    new_whale[j] = random_whale[j] - A * D
        else:
            # 螺旋位置更新阶段：X(t+1) = D' * e^{bl} * cos(2πl) + X*
            l = random.uniform(-1, 1)  # 螺旋参数
            new_whale = whale[:]
            for j in range(self.dim):
                D_prime = abs(X_star[j] - whale[j])
                new_whale[j] = D_prime * math.exp(b * l) * math.cos(2 * math.pi * l) + X_star[j]

        return new_whale

    def optimize(self):
        """执行完整的鲸鱼优化流程"""
        # 阶段1：初始化鲸鱼种群
        self.initialize()
        # 记录初始最优适应度
        best_fitness = self.gbest_fitness
        # 记录迭代历史
        history = [best_fitness]

        print("  迭代   0 | 最优适应度: {:.8f}".format(best_fitness))

        # 主循环：迭代优化
        for iteration in range(self.max_iter):
            # 阶段2：更新参数a（从2线性递减到0）
            a = 2 - 2 * (iteration / self.max_iter)

            # 阶段3：遍历所有鲸鱼更新位置
            for i in range(self.n_whales):
                # 生成随机数决定是包围还是螺旋
                p = random.random()
                # 更新位置
                new_whale = self.update_position(
                    self.whales[i],
                    self.gbest,
                    a,
                    p
                )
                # 边界处理
                new_whale = [max(self.lb, min(self.ub, x)) for x in new_whale]
                # 计算新位置的适应度
                new_fitness = self.func(new_whale)

                # 贪婪选择：如果新位置更优则更新
                if new_fitness < self.fitness[i]:
                    self.whales[i] = new_whale
                    self.fitness[i] = new_fitness
                    # 更新全局最优
                    if new_fitness < self.gbest_fitness:
                        self.gbest_fitness = new_fitness
                        self.gbest = new_whale[:]

            # 记录当前最优适应度
            best_finess = self.gbest_fitness
            history.append(best_finess)

            # 打印迭代进度
            if (iteration + 1) % 20 == 0:
                print(f"  迭代 {iteration + 1:3d} | 最优适应度: {best_finess:.8f}")

        return self.gbest, self.gbest_fitness, history


def sphere(x):
    """测试函数：Sphere函数（最简单的单峰测试函数）"""
    return sum(xi ** 2 for xi in x)


def rosenbrock(x):
    """测试函数：Rosenbrock函数（经典的病态测试函数）"""
    total = 0
    for i in range(len(x) - 1):
        total += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
    return total


def zakharov(x):
    """测试函数：Zakharov函数（多峰函数）"""
    n = len(x)
    sum1 = sum(xi ** 2 for xi in x)
    sum2 = sum(0.5 * (i + 1) * xi for i, xi in enumerate(x))
    return sum1 + sum2 ** 2 + sum2 ** 4


if __name__ == "__main__":
    # 设置随机种子以保证结果可复现
    random.seed(42)

    print("=" * 60)
    print("鲸鱼优化算法（WOA）测试")
    print("=" * 60)

    # 测试函数列表
    test_functions = [
        ("Sphere函数", sphere, 30),         # 单峰函数
        ("Rosenbrock函数", rosenbrock, 10),  # 病态函数
        ("Zakharov函数", zakharov, 20),    # 多峰函数
    ]

    # 算法参数设置
    n_whales = 30  # 鲸鱼数量
    max_iter = 100  # 最大迭代次数

    # 对每个测试函数运行WOA算法
    for name, func, dim in test_functions:
        print(f"\n测试函数: {name} (维度={dim})")
        print("-" * 40)

        # 创建WOA算法实例
        woa = WhaleOptimizationAlgorithm(
            func=func,
            dim=dim,
            n_whales=n_whales,
            max_iter=max_iter,
            bounds=(-5.0, 5.0)
        )

        # 执行优化
        best_solution, best_fitness, history = woa.optimize()

        # 输出结果
        print(f"\n  最优适应度: {best_fitness:.8f}")
        print(f"  解向量前5维: {[f'{v:.4f}' for v in best_solution[:5]]}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
