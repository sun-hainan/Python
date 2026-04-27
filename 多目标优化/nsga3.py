# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / nsga3



本文件实现 nsga3 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Callable, Optional

import random





class ReferencePoint:

    """参考点类"""

    def __init__(self, coordinates: np.ndarray):

        self.coordinates = coordinates  # 参考点坐标

        self.associated_individuals = []  # 关联的个体索引

        self.aspiration_trajectory = None  # 期望轨迹





class NSGA3:

    """

    NSGA-III算法

    

    参数:

        n_vars: 决策变量维度

        n_objectives: 目标数量

        pop_size: 种群大小

        n_divisions: 生成参考点的分割数

    """

    

    def __init__(self, n_vars: int, n_objectives: int, 

                 pop_size: int = 100, n_divisions: int = 12):

        self.n_vars = n_vars

        self.n_objectives = n_objectives

        self.pop_size = pop_size

        self.n_divisions = n_divisions

        

        # 生成参考点

        self.reference_points = self._generate_reference_points()

        

        # 算法参数

        self.crossover_prob = 0.9

        self.mutation_prob = 0.1

        self.eta = 20.0

        self.bounds = (0, 1)

        

        self.evaluate_func = None

    

    def _generate_reference_points(self) -> List[ReferencePoint]:

        """生成Das-Dennis风格的参考点"""

        n_obj = self.n_objectives

        n_points = self.n_divisions

        

        # 使用递归方式生成分层参考点

        def generate_recursive(n_obj, depth, current):

            if depth == n_obj - 1:

                return [current + [1.0]]

            else:

                result = []

                for i in range(n_points + 1):

                    frac = i / n_points

                    result.extend(generate_recursive(n_obj, depth + 1, current + [frac]))

                return result

        

        coords = generate_recursive(n_obj, 0, [])

        

        # 归一化

        ref_points = []

        for coord in coords:

            coord = np.array(coord)

            coord = coord / (np.sum(coord) + 1e-10)

            ref_points.append(ReferencePoint(coord))

        

        return ref_points

    

    def _initialize_population(self) -> np.ndarray:

        """初始化种群"""

        return np.random.uniform(self.bounds[0], self.bounds[1], 

                               (self.pop_size, self.n_vars))

    

    def _evaluate(self, population: np.ndarray) -> np.ndarray:

        """评估种群"""

        objectives = np.zeros((len(population), self.n_objectives))

        for i, ind in enumerate(population):

            objectives[i] = self.evaluate_func(ind)

        return objectives

    

    def _normalize_objectives(self, objectives: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

        """

        归一化目标

        

        Returns:

            normalized_objectives: 归一化后的目标

            ideal_point: 理想点

            nadir_point: 最差点

        """

        # 理想点：每个目标的最小值

        ideal_point = np.min(objectives, axis=0)

        

        # 最差点：每个目标的最大值

        nadir_point = np.max(objectives, axis=0)

        

        # 避免除零

        range_obj = nadir_point - ideal_point

        range_obj[range_obj == 0] = 1.0

        

        # 归一化

        normalized = (objectives - ideal_point) / range_obj

        

        return normalized, ideal_point, nadir_point

    

    def _associate(self, normalized_obj: np.ndarray) -> List[int]:

        """

        将个体关联到参考点

        

        Returns:

            每个个体关联的参考点索引

        """

        n_pop = len(normalized_obj)

        association = [-1] * n_pop

        

        for i in range(n_pop):

            min_dist = np.inf

            best_ref = 0

            

            for j, ref in enumerate(self.reference_points):

                # 计算到参考线的垂直距离

                # 简化：使用点到参考点的距离

                dist = np.linalg.norm(normalized_obj[i] - ref.coordinates)

                

                if dist < min_dist:

                    min_dist = dist

                    best_ref = j

            

            association[i] = best_ref

            self.reference_points[best_ref].associated_individuals.append(i)

        

        return association

    

    def _select_niche(self, n_needed: int, association: List[int]) -> List[int]:

        """

        选择需要保留的个体（基于小生境）

        

        Returns:

            选中的个体索引

        """

        selected = []

        

        # 统计每个参考点关联的个体数

        ref_counts = [len(ref.associated_individuals) for ref in self.reference_points]

        

        # 清空关联

        for ref in self.reference_points:

            ref.associated_individuals = []

        

        # 优先级队列：按关联数升序

        priorities = sorted(range(len(ref_counts)), key=lambda x: ref_counts[x])

        

        for ref_idx in priorities:

            if len(selected) >= n_needed:

                break

            

            # 找到该参考点

            ref = self.reference_points[ref_idx]

            

            # 检查该参考点是否有未选中的关联个体

            for ind_idx in association:

                if association[ind_idx] == ref_idx and ind_idx not in selected:

                    selected.append(ind_idx)

                    break

        

        return selected

    

    def _non_dominated_sort(self, objectives: np.ndarray) -> List[List[int]]:

        """非支配排序"""

        n = len(objectives)

        

        domination_count = [0] * n

        dominated_set = [[] for _ in range(n)]

        fronts = [[]]

        

        for i in range(n):

            for j in range(i + 1, n):

                if np.all(objectives[i] <= objectives[j]) and np.any(objectives[i] < objectives[j]):

                    dominated_set[i].append(j)

                    domination_count[j] += 1

                elif np.all(objectives[j] <= objectives[i]) and np.any(objectives[j] < objectives[i]):

                    dominated_set[j].append(i)

                    domination_count[i] += 1

            

            if domination_count[i] == 0:

                fronts[0].append(i)

        

        current = 0

        while fronts[current]:

            next_front = []

            for i in fronts[current]:

                for j in dominated_set[i]:

                    domination_count[j] -= 1

                    if domination_count[j] == 0:

                        next_front.append(j)

            

            if next_front:

                fronts.append(next_front)

            current += 1

        

        return fronts[:-1]

    

    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """模拟二进制交叉"""

        child1 = parent1.copy()

        child2 = parent2.copy()

        

        if random.random() > self.crossover_prob:

            return child1, child2

        

        for i in range(self.n_vars):

            if random.random() < 0.5:

                u = random.random()

                

                if u <= 0.5:

                    beta = (2 * u) ** (1 / (self.eta + 1))

                else:

                    beta = (1 / (2 * (1 - u))) ** (1 / (self.eta + 1))

                

                child1[i] = 0.5 * ((1 + beta) * parent1[i] + (1 - beta) * parent2[i])

                child2[i] = 0.5 * ((1 - beta) * parent1[i] + (1 + beta) * parent2[i])

        

        return child1, child2

    

    def _mutate(self, variables: np.ndarray) -> np.ndarray:

        """多项式变异"""

        mutated = variables.copy()

        

        for i in range(self.n_vars):

            if random.random() < self.mutation_prob:

                u = random.random()

                

                if u < 0.5:

                    delta = (2 * u) ** (1 / (self.eta + 1)) - 1

                else:

                    delta = 1 - (2 * (1 - u)) ** (1 / (self.eta + 1))

                

                mutated[i] += delta * (self.bounds[1] - self.bounds[0])

                mutated[i] = np.clip(mutated[i], self.bounds[0], self.bounds[1])

        

        return mutated

    

    def _environmental_selection(self, combined_pop: np.ndarray, 

                                 combined_obj: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """环境选择"""

        # 非支配排序

        fronts = self._non_dominated_sort(combined_obj)

        

        new_pop = []

        new_obj = []

        

        for front in fronts:

            if len(new_pop) + len(front) <= self.pop_size:

                for idx in front:

                    new_pop.append(combined_pop[idx])

                    new_obj.append(combined_obj[idx])

            else:

                # 需要选择一部分

                n_needed = self.pop_size - len(new_pop)

                

                # 清空参考点

                for ref in self.reference_points:

                    ref.associated_individuals = []

                

                # 归一化

                norm_obj, ideal, nadir = self._normalize_objectives(np.array(new_obj + [combined_obj[i] for i in front]))

                

                # 关联

                association = self._associate(norm_obj)

                

                # 选择小生境

                selected_indices = self._select_niche(n_needed, association[:len(new_obj)] + association[len(new_obj):])

                

                for i, idx in enumerate(selected_indices[:n_needed]):

                    if idx < len(new_pop):

                        continue

                    else:

                        actual_idx = front[idx - len(new_pop)]

                        new_pop.append(combined_pop[actual_idx])

                        new_obj.append(combined_obj[actual_idx])

                

                break

        

        return np.array(new_pop), np.array(new_obj)

    

    def optimize(self, evaluate_func: Callable, 

                 n_generations: int = 100,

                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:

        """运行NSGA-III优化"""

        self.evaluate_func = evaluate_func

        

        # 初始化

        population = self._initialize_population()

        objectives = self._evaluate(population)

        

        for gen in range(n_generations):

            # 创建子代

            parents = population

            offspring = []

            

            for i in range(0, self.pop_size, 2):

                p1, p2 = parents[i], parents[(i + 1) % self.pop_size]

                c1, c2 = self._crossover(p1, p2)

                offspring.append(self._mutate(c1))

                offspring.append(self._mutate(c2))

            

            offspring = np.array(offspring[:self.pop_size])

            offspring_obj = self._evaluate(offspring)

            

            # 合并

            combined_pop = np.vstack([population, offspring])

            combined_obj = np.vstack([objectives, offspring_obj])

            

            # 环境选择

            population, objectives = self._environmental_selection(combined_pop, combined_obj)

            

            if verbose and (gen + 1) % 20 == 0:

                print(f"Generation {gen + 1}: Best objectives = {objectives[0]}")

        

        return population, objectives





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("NSGA-III 基于参考点的多目标优化测试")

    print("=" * 50)

    

    random.seed(42)

    np.random.seed(42)

    

    # ZDT1

    def zdt1(x):

        f1 = x[0]

        g = 1 + 9 * np.sum(x[1:]) / 9

        f2 = g * (1 - np.sqrt(x[0] / g))

        return np.array([f1, f2])

    

    # ZDT3

    def zdt3(x):

        f1 = x[0]

        g = 1 + 9 * np.sum(x[1:]) / 9

        f2 = g * (1 - np.sqrt(x[0] / g) - x[0] / g * np.sin(10 * np.pi * x[0]))

        return np.array([f1, f2])

    

    print("\n--- ZDT1 问题 (10变量, 2目标) ---")

    nsga3 = NSGA3(n_vars=10, n_objectives=2, pop_size=100, n_divisions=12)

    pareto_vars, pareto_front = nsga3.optimize(zdt1, n_generations=200)

    

    print(f"Pareto前沿点数: {len(pareto_front)}")

    print(f"前5个解的目标值:")

    for i, obj in enumerate(pareto_front[:5]):

        print(f"  解{i+1}: f1={obj[0]:.4f}, f2={obj[1]:.4f}")

    

    print("\n--- ZDT3 问题（不连续Pareto前沿） ---")

    nsga3_2 = NSGA3(n_vars=10, n_objectives=2, pop_size=100)

    pareto_vars3, pareto_front3 = nsga3_2.optimize(zdt3, n_generations=200)

    

    print(f"Pareto前沿点数: {len(pareto_front3)}")

    

    # 三目标测试

    print("\n--- 三目标测试问题 ---")

    

    def three_objective(x):

        f1 = x[0]

        f2 = x[1]

        f3 = (1 + x[2]) * np.exp(-x[0] / (x[1] + 1e-10))

        return np.array([f1, f2, f3])

    

    nsga3_3 = NSGA3(n_vars=3, n_objectives=3, pop_size=100, n_divisions=8)

    pareto_vars3, pareto_front3 = nsga3_3.optimize(three_objective, n_generations=150)

    

    print(f"Pareto前沿点数: {len(pareto_front3)}")

    print(f"前3个解: {pareto_front3[:3]}")

    

    print("\n" + "=" * 50)

    print("测试完成")

