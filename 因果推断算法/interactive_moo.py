# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / interactive_moo



本文件实现 interactive_moo 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Callable, Optional

from dataclasses import dataclass

import random





@dataclass

class Solution:

    """解"""

    x: np.ndarray  # 决策变量

    objectives: np.ndarray  # 目标值

    fitness: float = 0.0





class InteractiveMOO:

    """

    交互式多目标优化框架

    """

    

    def __init__(self, objectives: List[Callable], bounds: List[Tuple[float, float]]):

        """

        初始化

        

        Args:

            objectives: 目标函数列表（最小化）

            bounds: 决策变量范围

        """

        self.objectives = objectives

        self.bounds = bounds

        self.n_objectives = len(objectives)

        self.n_variables = len(bounds)

        

        # Pareto前沿

        self.pareto_front: List[Solution] = []

        

        # 偏好信息

        self.preference_weights: np.ndarray = None

    

    def _evaluate(self, x: np.ndarray) -> np.ndarray:

        """评估目标"""

        return np.array([obj(x) for obj in self.objectives])

    

    def _is_dominated(self, obj1: np.ndarray, obj2: np.ndarray) -> bool:

        """检查obj1是否被obj2支配"""

        # obj2在所有目标上不差于obj1，且至少一个严格更好

        better = False

        for i in range(self.n_objectives):

            if obj2[i] > obj1[i]:  # 最小化

                return False

            if obj2[i] < obj1[i]:

                better = True

        return better

    

    def generate_random_solutions(self, n: int) -> List[Solution]:

        """生成随机解"""

        solutions = []

        

        for _ in range(n):

            x = np.array([random.uniform(low, high) 

                         for low, high in self.bounds])

            obj = self._evaluate(x)

            solutions.append(Solution(x, obj))

        

        return solutions

    

    def find_pareto_front(self, solutions: List[Solution]) -> List[Solution]:

        """找到Pareto最优解"""

        pareto = []

        

        for s in solutions:

            is_pareto = True

            for other in solutions:

                if self._is_dominated(s.objectives, other.objectives):

                    is_pareto = False

                    break

            

            if is_pareto:

                pareto.append(s)

        

        self.pareto_front = pareto

        return pareto

    

    def apply_preference_weights(self, weights: np.ndarray) -> List[Solution]:

        """

        根据权重筛选解

        

        Args:

            weights: 目标权重（归一化）

        

        Returns:

            满足偏好的解

        """

        self.preference_weights = weights

        

        if not self.pareto_front:

            return []

        

        # 计算加权得分

        scored = []

        for s in self.pareto_front:

            score = np.dot(s.objectives, weights)

            scored.append((score, s))

        

        # 按得分排序

        scored.sort(key=lambda x: x[0])

        

        return [s for _, s in scored]

    

    def reference_point_method(self, reference_point: np.ndarray) -> Solution:

        """

        参考点法

        

        Args:

            reference_point: 参考点（希望达到的目标值）

        

        Returns:

            最接近参考点的Pareto解

        """

        if not self.pareto_front:

            return None

        

        best_sol = None

        min_dist = float('inf')

        

        for s in self.pareto_front:

            dist = np.linalg.norm(s.objectives - reference_point)

            if dist < min_dist:

                min_dist = dist

                best_sol = s

        

        return best_sol





class InteractiveNSGAII:

    """

    交互式NSGA-II

    

    结合NSGA-II和人类偏好

    """

    

    def __init__(self, objectives: List[Callable], n_generations: int = 100,

                 population_size: int = 100):

        self.objectives = objectives

        self.n_generations = n_generations

        self.population_size = population_size

        self.pareto_front = []

    

    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> np.ndarray:

        """交叉"""

        alpha = random.random()

        return alpha * parent1 + (1 - alpha) * parent2

    

    def _mutate(self, x: np.ndarray, mutation_rate: float = 0.1) -> np.ndarray:

        """变异"""

        x_mut = x.copy()

        for i in range(len(x)):

            if random.random() < mutation_rate:

                x_mut[i] += np.random.randn() * 0.1

        return x_mut

    

    def _crowding_distance(self, front: List[Solution]) -> List[float]:

        """计算拥挤距离"""

        n = len(front)

        if n <= 2:

            return [float('inf')] * n

        

        distances = [0.0] * n

        

        for m in range(self.n_objectives):

            # 按目标m排序

            sorted_front = sorted(enumerate(front), 

                              key=lambda x: x[1].objectives[m])

            

            # 边界解距离无穷

            distances[sorted_front[0][0]] = float('inf')

            distances[sorted_front[-1][0]] = float('inf')

            

            # 中间解

            obj_range = (sorted_front[-1][1].objectives[m] - 

                        sorted_front[0][1].objectives[m])

            

            if obj_range > 0:

                for i in range(1, n - 1):

                    idx = sorted_front[i][0]

                    distances[idx] += (

                        sorted_front[i+1][1].objectives[m] - 

                        sorted_front[i-1][1].objectives[m]

                    ) / obj_range

        

        return distances

    

    def _non_dominated_sort(self, population: List[Solution]) -> List[List[Solution]]:

        """非支配排序"""

        n = len(population)

        domination_count = [0] * n

        dominated_set = [[] for _ in range(n)]

        

        fronts = [[]]

        

        for i in range(n):

            for j in range(n):

                if i == j:

                    continue

                

                if population[i].objectives[0] <= population[j].objectives[0]:  # 简化

                    domination_count[i] += 1

                    dominated_set[i].append(j)

            

            if domination_count[i] == 0:

                fronts[0].append(population[i])

        

        k = 0

        while fronts[k]:

            next_front = []

            for i, sol in enumerate(fronts[k]):

                for j in dominated_set[self._get_index(population, sol)]:

                    domination_count[j] -= 1

                    if domination_count[j] == 0:

                        next_front.append(population[j])

            k += 1

            fronts.append(next_front)

        

        return fronts[:-1]





def demo_interactive_preference():

    """演示交互式偏好"""

    print("=== 交互式偏好演示 ===\n")

    

    # 定义双目标问题

    # min f1 = x^2, min f2 = (x-2)^2

    

    objectives = [

        lambda x: x[0] ** 2,

        lambda x: (x[0] - 2) ** 2

    ]

    

    bounds = [(-5, 5)]

    

    # 创建优化器

    opt = InteractiveMOO(objectives, bounds)

    

    # 生成解

    solutions = opt.generate_random_solutions(100)

    

    # 找Pareto前沿

    pareto = opt.find_pareto_front(solutions)

    

    print(f"生成 {len(solutions)} 个解")

    print(f"找到 {len(pareto)} 个Pareto最优解")

    

    print("\nPareto前沿:")

    for s in pareto[:5]:

        print(f"  f₁={s.objectives[0]:.2f}, f₂={s.objectives[1]:.2f}")

    

    # 应用偏好

    weights = np.array([0.7, 0.3])  # 更看重f1

    preferred = opt.apply_preference_weights(weights)

    

    print(f"\n偏好权重: {weights}")

    print("推荐解:")

    for s in preferred[:3]:

        print(f"  f₁={s.objectives[0]:.2f}, f₂={s.objectives[1]:.2f}, "

              f"加权得分={np.dot(s.objectives, weights):.2f}")

    

    # 参考点法

    ref_point = np.array([1.0, 1.0])

    best_ref = opt.reference_point_method(ref_point)

    

    print(f"\n参考点: {ref_point}")

    print(f"最接近的Pareto解: f₁={best_ref.objectives[0]:.2f}, f₂={best_ref.objectives[1]:.2f}")





def demo_pareto_navigation():

    """演示Pareto导航"""

    print("\n=== Pareto导航 ===\n")

    

    print("决策者交互方式:")

    print()

    

    print("1. 权重指定:")

    print("   - 给每个目标分配权重")

    print("   - 加权求和后排序")

    

    print("\n2. 参考点:")

    print("   - 指定理想目标值")

    print("   - 找最接近的Pareto解")

    

    print("\n3. 目标分级:")

    print("   - 先优化最重要的目标")

    print("   - 然后在约束下优化其他")

    

    print("\n4. 渐进偏好:")

    print("   - 逐步调整偏好")

    print("   - 观察Pareto前沿变化")





def demo_visualization():

    """演示可视化"""

    print("\n=== Pareto前沿可视化 ===\n")

    

    print("二维目标Pareto前沿:")

    print()

    print("    f₂")

    print("     ↑")

    print("    3|    * Pareto最优点")

    print("     |   *")

    print("    2|  *")

    print("     | *")

    print("    1|*")

    print("     |________________→ f₁")

    print("      0   1   2   3")

    print()

    print("特点:")

    print("  - 权衡曲线")

    print("  - 斜率大处表示边际替代率高")





if __name__ == "__main__":

    print("=" * 60)

    print("交互式多目标优化")

    print("=" * 60)

    

    # 交互式偏好

    demo_interactive_preference()

    

    # Pareto导航

    demo_pareto_navigation()

    

    # 可视化

    demo_visualization()

    

    print("\n" + "=" * 60)

    print("交互式MOO方法总结:")

    print("=" * 60)

    print("""

1. 基本框架:

   - 展示Pareto前沿给决策者

   - 收集偏好信息

   - 根据偏好筛选或指导搜索



2. 偏好表示方法:

   - 权重向量

   - 参考点

   - 目标等级

   - 目标间权衡率



3. 常用算法:

   - Weighted Sum

   - Tchebychev

   - Reference Point (AISM)

   - GRA (Grey Relational Analysis)



4. 挑战:

   - 偏好表达困难

   - 决策者疲劳

   - 高维目标可视化

""")

