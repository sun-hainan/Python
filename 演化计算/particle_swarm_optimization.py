"""
粒子群优化算法 (Particle Swarm Optimization, PSO)
=================================================

模拟鸟群觅食行为的元启发式优化算法。
每个粒子在解空间中飞行,根据自身历史最优和全局最优来调整位置。

参考: Kennedy, J. and Eberhart, R. (1995). Particle Swarm Optimization.
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# PSO参数配置
# ============================================================

class PSOConfig:
    """PSO算法配置参数"""

    def __init__(self):
        # 种群/粒子数量
        self.swarm_size = 50
        # 搜索空间维度
        self.dimensions = 2
        # 搜索空间下界
        self.lower_bound = -10.0
        # 搜索空间上界
        self.upper_bound = 10.0
        # 惯性权重(控制历史速度影响)
        self.inertia_weight = 0.729
        # 认知系数(自身最优影响力)
        self.cognitive_param = 1.49445
        # 社会系数(全局最优影响力)
        self.social_param = 1.49445
        # 最大速度限制
        self.max_velocity = 2.0
        # 最大迭代次数
        self.max_iterations = 100


# ============================================================
# 粒子类定义
# ============================================================

class Particle:
    """
    粒子类,表示PSO中的单个搜索个体

    属性:
        position: 当前所在位置(解向量)
        velocity: 当前速度向量
        personal_best_position: 个体历史最优位置
        personal_best_fitness: 个体历史最优适应度
    """

    def __init__(self, dimensions, lower, upper):
        """
        初始化粒子

        参数:
            dimensions: 解空间维度
            lower: 搜索下界
            upper: 搜索上界
        """
        # 随机初始化位置(均匀分布)
        self.position = np.random.uniform(lower, upper, dimensions)
        # 随机初始化速度
        self.velocity = np.random.uniform(-1, 1, dimensions)
        # 初始个人最优等于当前位置
        self.personal_best_position = self.position.copy()
        # 初始个人最优适应度设为负无穷
        self.personal_best_fitness = float('-inf')

    def update_velocity(self, global_best, inertia_weight, cognitive, social):
        """
        更新粒子速度

        速度公式:
        v_new = w * v_old
              + c1 * r1 * (pbest - x)
              + c2 * r2 * (gbest - x)

        参数:
            global_best: 全局最优位置
            inertia_weight: 惯性权重w
            cognitive: 认知系数c1
            social: 社会系数c2
        """
        # 随机系数(增强搜索随机性)
        r1 = np.random.random(len(self.velocity))
        r2 = np.random.random(len(self.velocity))

        # 速度更新三部分:
        # 1. 惯性部分:保持原有运动趋势
        inertia = inertia_weight * self.velocity

        # 2. 认知部分:向自身历史最优学习
        cognitive_component = cognitive * r1 * (self.personal_best_position - self.position)

        # 3. 社会部分:向全局最优学习
        social_component = social * r2 * (global_best - self.position)

        # 合成新速度
        self.velocity = inertia + cognitive_component + social_component

    def update_position(self, lower, upper, max_velocity):
        """
        根据速度更新粒子位置

        参数:
            lower: 位置下界
            upper: 位置上界
            max_velocity: 最大速度限制
        """
        # 更新位置
        self.position = self.position + self.velocity

        # 限制速度范围(防止爆炸)
        self.velocity = np.clip(self.velocity, -max_velocity, max_velocity)

        # 边界处理:将超出边界的粒子拉回
        self.position = np.clip(self.position, lower, upper)

    def evaluate(self, fitness_function):
        """
        评估当前适应度并更新个人最优

        参数:
            fitness_function: 适应度函数

        返回:
            当前适应度值
        """
        # 计算当前位置的适应度
        fitness = fitness_function(self.position)

        # 如果当前优于历史,更新个人最优
        if fitness > self.personal_best_fitness:
            self.personal_best_fitness = fitness
            self.personal_best_position = self.position.copy()

        return fitness


# ============================================================
# PSO主算法
# ============================================================

class PSO:
    """
    粒子群优化器

    包含全局版PSO(使用全局最优)和局部版PSO(使用邻居最优)
    """

    def __init__(self, config=None):
        """
        初始化PSO优化器

        参数:
            config: PSOConfig配置对象
        """
        self.config = config if config else PSOConfig()

    def optimize(self, fitness_function, verbose=True):
        """
        执行PSO优化

        参数:
            fitness_function: 待优化的目标函数(最大化)
            verbose: 是否输出迭代信息

        返回:
            global_best_position: 最优解
            global_best_fitness: 最优适应度
            history: 迭代历史
        """
        cfg = self.config

        # 初始化粒子群
        swarm = [
            Particle(cfg.dimensions, cfg.lower_bound, cfg.upper_bound)
            for _ in range(cfg.swarm_size)
        ]

        # 全局最优
        global_best_position = None
        global_best_fitness = float('-inf')

        # 迭代历史
        history = {
            'global_best_fitness': [],
            'avg_fitness': [],
            'global_best_position': []
        }

        # 主循环
        for iteration in range(cfg.max_iterations):
            # 存储当代粒子适应度
            current_fitnesses = []

            # 遍历每个粒子
            for particle in swarm:
                # 评估粒子适应度
                fitness = particle.evaluate(fitness_function)
                current_fitnesses.append(fitness)

                # 更新全局最优
                if fitness > global_best_fitness:
                    global_best_fitness = fitness
                    global_best_position = particle.position.copy()

            # 记录历史
            history['global_best_fitness'].append(global_best_fitness)
            history['avg_fitness'].append(np.mean(current_fitnesses))
            history['global_best_position'].append(global_best_position.copy())

            # 输出进度
            if verbose and iteration % 20 == 0:
                print(f"Iter {iteration:4d}: Best Fitness = {global_best_fitness:.6f} | "
                      f"Best Pos = {global_best_position[:2]}")

            # 更新所有粒子速度与位置
            for particle in swarm:
                # 全局版PSO:向全局最优学习
                particle.update_velocity(
                    global_best_position,
                    cfg.inertia_weight,
                    cfg.cognitive_param,
                    cfg.social_param
                )
                particle.update_position(
                    cfg.lower_bound,
                    cfg.upper_bound,
                    cfg.max_velocity
                )

        return global_best_position, global_best_fitness, history

    def optimize_local(self, fitness_function, neighbor_size=5, verbose=True):
        """
        局部版PSO:使用环形拓扑的邻居结构

        参数:
            fitness_function: 目标函数
            neighbor_size: 邻居粒子数量
            verbose: 是否输出

        返回:
            最优解和迭代历史
        """
        cfg = self.config

        # 初始化粒子群
        swarm = [
            Particle(cfg.dimensions, cfg.lower_bound, cfg.upper_bound)
            for _ in range(cfg.swarm_size)
        ]

        # 初始化邻居最优(环形拓扑)
        neighborhood_best = [None] * cfg.swarm_size
        neighborhood_fitness = [float('-inf')] * cfg.swarm_size

        # 全局最优
        global_best_position = None
        global_best_fitness = float('-inf')

        history = {'global_best_fitness': [], 'avg_fitness': []}

        for iteration in range(cfg.max_iterations):
            current_fitnesses = []

            # 更新邻居最优
            for i in range(cfg.swarm_size):
                # 环形邻居:前后各取neighbor_size/2个
                neighbors = []
                for offset in range(-neighbor_size // 2, neighbor_size // 2 + 1):
                    idx = (i + offset) % cfg.swarm_size
                    neighbors.append((idx, swarm[idx].personal_best_fitness))

                # 找邻居中最优的
                best_neighbor = max(neighbors, key=lambda x: x[1])
                neighborhood_best[i] = swarm[best_neighbor[0]].personal_best_position.copy()
                neighborhood_fitness[i] = best_neighbor[1]

            # 评估和更新
            for i, particle in enumerate(swarm):
                fitness = particle.evaluate(fitness_function)
                current_fitnesses.append(fitness)

                if fitness > global_best_fitness:
                    global_best_fitness = fitness
                    global_best_position = particle.position.copy()

            # 记录
            history['global_best_fitness'].append(global_best_fitness)
            history['avg_fitness'].append(np.mean(current_fitnesses))

            if verbose and iteration % 20 == 0:
                print(f"Iter {iteration:4d} [Local]: Best = {global_best_fitness:.6f}")

            # 更新速度(使用邻居最优而非全局最优)
            for i, particle in enumerate(swarm):
                particle.update_velocity(
                    neighborhood_best[i],
                    cfg.inertia_weight,
                    cfg.cognitive_param,
                    cfg.social_param
                )
                particle.update_position(
                    cfg.lower_bound,
                    cfg.upper_bound,
                    cfg.max_velocity
                )

        return global_best_position, global_best_fitness, history


# ============================================================
# 测试函数
# ============================================================

def sphere_function(x):
    """球形函数(单峰测试函数)"""
    return -np.sum(x ** 2)


def rastrigin_function(x):
    """Rastrigin函数(多峰测试函数)"""
    n = len(x)
    return -10 * n - np.sum(x ** 2) + 10 * np.sum(np.cos(2 * np.pi * x))


# ============================================================
# 程序入口:测试PSO
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("粒子群优化算法 (PSO) 测试")
    print("=" * 60)

    # 创建PSO配置
    config = PSOConfig()
    config.swarm_size = 30
    config.max_iterations = 100
    config.dimensions = 5  # 5维搜索空间

    # 创建优化器
    pso = PSO(config)

    # 测试球形函数
    print("\n【测试1】球形函数 f(x) = -sum(x^2)")
    print("维度: 5, 搜索范围: [-10, 10]")

    best_pos, best_fit, history = pso.optimize(sphere_function, verbose=True)

    print(f"\n最优位置: {best_pos}")
    print(f"最优适应度: {best_fit:.6f}")
    print(f"理论最优: 0.0")

    # 测试Rastrigin函数
    print("\n" + "-" * 60)
    print("\n【测试2】Rastrigin函数(多峰)")
    print("维度: 3, 搜索范围: [-5, 5]")

    config2 = PSOConfig()
    config2.dimensions = 3
    config2.lower_bound = -5
    config2.upper_bound = 5
    config2.max_iterations = 150

    pso2 = PSO(config2)
    best_pos2, best_fit2, _ = pso2.optimize(rastrigin_function, verbose=False)

    print(f"最优适应度: {best_fit2:.6f}")
    print(f"理论最优: 0.0")

    # 对比全局版和局部版
    print("\n" + "-" * 60)
    print("\n【测试3】全局版 vs 局部版 PSO 对比")
    print("目标函数: 5维球形函数")

    config3 = PSOConfig()
    config3.dimensions = 5
    config3.swarm_size = 40

    pso3 = PSO(config3)

    # 全局版
    _, fit_global, _ = pso3.optimize(sphere_function, verbose=False)
    print(f"全局版PSO最优适应度: {fit_global:.6f}")

    # 局部版
    _, fit_local, _ = pso3.optimize_local(sphere_function, neighbor_size=5, verbose=False)
    print(f"局部版PSO最优适应度: {fit_local:.6f}")

    print("\n" + "=" * 60)
    print("PSO算法测试完成")
    print("=" * 60)