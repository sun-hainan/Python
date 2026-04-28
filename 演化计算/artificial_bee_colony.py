"""
人工蜂群算法（Artificial Bee Colony, ABC）
==========================================

算法原理：
- 模拟蜜蜂采蜜行为，通过雇佣蜂、观察蜂和侦察蜂三种角色的协作
  来寻找优化问题的最优解。
- 雇佣蜂（Employed Bee）：携带蜜源信息，在邻域内搜索新蜜源
- 观察蜂（Onlooker Bee）：根据雇佣蜂分享的信息选择蜜源进行搜索
- 侦察蜂（Scout Bee）：当蜜源被放弃时，随机搜索新蜜源

特点：
- 参数少（仅需设置蜂群规模、最大迭代次数）
- 全局搜索能力强，不易陷入局部最优
- 适用于连续优化问题

参考文献：
- Karaboga, D. (2005). An idea based on honey bee swarm for numerical optimization.
- Erciyes University, Technical Report-TR06, 2005.
"""

import random
import math


class ArtificialBeeColony:
    """人工蜂群算法核心类"""

    def __init__(self, func, dim, pop_size=50, max_iter=100, bounds=(-5.0, 5.0)):
        # 目标函数句柄
        self.func = func
        # 搜索空间维度
        self.dim = dim
        # 蜂群规模（雇佣蜂数量 = 观察蜂数量）
        self.pop_size = pop_size
        # 最大迭代次数
        self.max_iter = max_iter
        # 搜索边界
        self.lb = bounds[0]  # 下界
        self.ub = bounds[1]  # 上界
        # 蜜源（解）列表
        self.solutions = []
        # 蜜源适应度值（目标函数值）
        self.fitness = []
        # 蜜源被放弃的次数计数器
        self.trial = []
        # 全局最优解
        self.gbest = None
        # 全局最优适应度
        self.gbest_fitness = float('inf')

    def initialize(self):
        """初始化蜂群，随机生成蜜源位置"""
        # 遍历每个蜜源（每个雇佣蜂对应一个蜜源）
        for i in range(self.pop_size):
            # 随机生成维度为dim的解向量
            solution = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
            # 将解添加到蜜源列表
            self.solutions.append(solution)
            # 计算该蜜源的适应度
            fitness = self.func(solution)
            # 添加适应度记录
            self.fitness.append(fitness)
            # 初始化被放弃次数为0
            self.trial.append(0)
            # 更新全局最优
            if fitness < self.gbest_fitness:
                self.gbest_fitness = fitness
                self.gbest = solution[:]

    def employed_phase(self):
        """雇佣蜂阶段：在邻域内搜索新蜜源"""
        # 遍历每个雇佣蜂
        for i in range(self.pop_size):
            # 随机选择另一个蜜源的维度k进行邻域搜索
            k = random.randint(0, self.dim - 1)
            # 随机选择另一个蜜源的索引j（不等于当前蜜源i）
            j = random.randint(0, self.pop_size - 1)
            while j == i:
                j = random.randint(0, self.pop_size - 1)

            # 生成新解：基于当前解和随机选择的另一个解进行搜索
            # phi为[-1,1]之间的随机扰动因子
            phi = random.uniform(-1, 1)
            # 新解的第k维 = 原解第k维 + 扰动 * 差异
            new_solution = self.solutions[i][:]
            new_solution[k] = (self.solutions[i][k] +
                               phi * (self.solutions[i][k] - self.solutions[j][k]))
            # 边界处理：确保新解在搜索范围内
            new_solution[k] = max(self.lb, min(self.ub, new_solution[k]))

            # 计算新解的适应度
            new_fitness = self.func(new_solution)

            # 选择策略：新解更优则替换原蜜源
            if new_fitness < self.fitness[i]:
                # 用更优的新解替换原解
                self.solutions[i] = new_solution
                self.fitness[i] = new_fitness
                # 重置放弃计数器
                self.trial[i] = 0
            else:
                # 解未改进，增加放弃计数
                self.trial[i] += 1

    def calculate_probabilities(self):
        """计算每个蜜源被观察蜂选中的概率（基于适应度）"""
        # 使用适应度比例法计算概率
        # 适应度越好（值越小），被选中的概率越高
        total_fitness = sum(self.fitness)
        # 避免除零错误
        if total_fitness == 0:
            return [1.0 / self.pop_size] * self.pop_size
        # 计算每个蜜源的选中概率
        probabilities = [f / total_fitness for f in self.fitness]
        return probabilities

    def onlooker_phase(self):
        """观察蜂阶段：根据概率选择蜜源并在其邻域搜索"""
        # 计算各蜜源被选中的概率
        probabilities = self.calculate_probabilities()
        # 遍历观察蜂（数量等于蜜源数量）
        i = 0
        t = 0
        while t < self.pop_size:
            # 轮盘赌选择：根据概率选择蜜源
            r = random.random()
            if r < probabilities[i]:
                t += 1
                # 对选中的蜜源进行邻域搜索（与雇佣蜂阶段相同）
                k = random.randint(0, self.dim - 1)
                j = random.randint(0, self.pop_size - 1)
                while j == i:
                    j = random.randint(0, self.pop_size - 1)

                phi = random.uniform(-1, 1)
                new_solution = self.solutions[i][:]
                new_solution[k] = (self.solutions[i][k] +
                                   phi * (self.solutions[i][k] - self.solutions[j][k]))
                new_solution[k] = max(self.lb, min(self.ub, new_solution[k]))

                new_fitness = self.func(new_solution)

                if new_fitness < self.fitness[i]:
                    self.solutions[i] = new_solution
                    self.fitness[i] = new_fitness
                    self.trial[i] = 0
                else:
                    self.trial[i] += 1
            # 循环选择蜜源索引
            i = (i + 1) % self.pop_size

    def scout_phase(self):
        """侦察蜂阶段：放弃被停滞的蜜源，随机生成新蜜源"""
        # 遍历所有蜜源
        for i in range(self.pop_size):
            # 如果蜜源被放弃次数超过阈值（设为pop_size/2）
            if self.trial[i] > self.pop_size // 2:
                # 随机生成一个新的蜜源位置
                new_solution = [random.uniform(self.lb, self.ub) for _ in range(self.dim)]
                self.solutions[i] = new_solution
                self.fitness[i] = self.func(new_solution)
                self.trial[i] = 0
                # 更新全局最优
                if self.fitness[i] < self.gbest_fitness:
                    self.gbest_fitness = self.fitness[i]
                    self.gbest = new_solution[:]

    def optimize(self):
        """执行完整的ABC算法优化流程"""
        # 阶段1：初始化蜂群
        self.initialize()
        # 记录初始最优适应度
        best_fitness = self.gbest_fitness
        # 记录迭代历史
        history = [best_fitness]

        # 主循环：迭代优化
        for iteration in range(self.max_iter):
            # 阶段2：雇佣蜂阶段
            self.employed_phase()
            # 阶段3：观察蜂阶段
            self.onlooker_phase()
            # 阶段4：侦察蜂阶段
            self.scout_phase()

            # 记录当前最优适应度
            best_fitness = self.gbest_fitness
            history.append(best_fitness)

            # 打印迭代进度
            if (iteration + 1) % 20 == 0:
                print(f"  迭代 {iteration + 1:3d} | 最优适应度: {best_fitness:.8f}")

        return self.gbest, self.gbest_fitness, history


def sphere(x):
    """测试函数：Sphere函数（维度无关）"""
    return sum(xi ** 2 for xi in x)


def rastrigin(x):
    """测试函数：Rastrigin函数（多峰函数，易陷入局部最优）"""
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


if __name__ == "__main__":
    # 设置随机种子以保证结果可复现
    random.seed(42)

    print("=" * 60)
    print("人工蜂群算法（ABC）测试")
    print("=" * 60)

    # 测试函数列表
    test_functions = [
        ("Sphere函数", sphere, 30),       # 单峰函数
        ("Rastrigin函数", rastrigin, 20),  # 多峰函数
    ]

    # 算法参数设置
    pop_size = 40  # 蜂群规模
    max_iter = 100  # 最大迭代次数

    # 对每个测试函数运行ABC算法
    for name, func, dim in test_functions:
        print(f"\n测试函数: {name} (维度={dim})")
        print("-" * 40)

        # 创建ABC算法实例
        abc = ArtificialBeeColony(
            func=func,
            dim=dim,
            pop_size=pop_size,
            max_iter=max_iter,
            bounds=(-5.12, 5.12)
        )

        # 执行优化
        best_solution, best_fitness, history = abc.optimize()

        # 输出结果
        print(f"\n  最优适应度: {best_fitness:.8f}")
        print(f"  解向量前5维: {[f'{v:.4f}' for v in best_solution[:5]]}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
