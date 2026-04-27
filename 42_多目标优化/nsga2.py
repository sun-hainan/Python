# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / nsga2



本文件实现 nsga2 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Callable, Optional

from dataclasses import dataclass

import random





@dataclass

class Individual:

    """个体"""

    variables: np.ndarray       # 决策变量

    objectives: np.ndarray      # 目标函数值

    rank: int = 0              # 非支配层级

    crowding_distance: float = 0.0  # 拥挤距离





class NSGA2:

    """

    NSGA-II算法

    

    参数:

        n_vars: 决策变量维度

        n_objectives: 目标数量

        pop_size: 种群大小

        crossover_prob: 交叉概率

        mutation_prob: 变异概率

        eta: 模拟二进制交叉参数

        bounds: 变量边界 (min, max)

    """

    

    def __init__(self,

                 n_vars: int,

                 n_objectives: int,

                 pop_size: int = 100,

                 crossover_prob: float = 0.9,

                 mutation_prob: float = 0.1,

                 eta: float = 20.0,

                 bounds: Tuple[float, float] = (0, 1)):

        self.n_vars = n_vars

        self.n_objectives = n_objectives

        self.pop_size = pop_size

        self.crossover_prob = crossover_prob

        self.mutation_prob = mutation_prob

        self.eta = eta

        self.bounds = bounds

        

        # 评估函数（需要外部提供）

        self.evaluate_func = None

    

    def _initialize_population(self) -> List[Individual]:

        """初始化种群"""

        population = []

        

        for _ in range(self.pop_size):

            # 随机初始化变量

            variables = np.random.uniform(

                self.bounds[0], self.bounds[1], self.n_vars

            )

            

            # 创建个体

            ind = Individual(variables=variables, objectives=np.zeros(self.n_objectives))

            population.append(ind)

        

        return population

    

    def _evaluate(self, population: List[Individual]):

        """评估种群"""

        for ind in population:

            if self.evaluate_func:

                ind.objectives = np.array(self.evaluate_func(ind.variables))

    

    def _non_dominated_sort(self, population: List[Individual]) -> List[List[int]]:

        """非支配排序"""

        n = len(population)

        

        domination_count = [0] * n  # 支配该个体的数量

        dominated_set = [[] for _ in range(n)]  # 该个体支配的集合

        fronts = [[]]  # 第一层

        

        for i in range(n):

            for j in range(i + 1, n):

                # 比较i和j

                if self._dominates(population[i], population[j]):

                    dominated_set[i].append(j)

                    domination_count[j] += 1

                elif self._dominates(population[j], population[i]):

                    dominated_set[j].append(i)

                    domination_count[i] += 1

            

            if domination_count[i] == 0:

                fronts[0].append(i)

        

        # 逐层构建

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

        

        return fronts[:-1]  # 去掉最后的空层

    

    def _dominates(self, ind1: Individual, ind2: Individual) -> bool:

        """判断ind1是否支配ind2"""

        obj1 = ind1.objectives

        obj2 = ind2.objectives

        

        # 不差于

        not_worse = np.all(obj1 <= obj2)

        # 至少一个严格优

        strictly_better = np.any(obj1 < obj2)

        

        return not_worse and strictly_better

    

    def _crowding_distance(self, population: List[Individual], front: List[int]):

        """计算拥挤距离"""

        n_front = len(front)

        

        if n_front <= 2:

            for i in front:

                population[i].crowding_distance = np.inf

            return

        

        # 初始化

        for i in front:

            population[i].crowding_distance = 0.0

        

        # 对每个目标计算

        for m in range(self.n_objectives):

            # 按当前目标排序

            sorted_front = sorted(front, key=lambda x: population[x].objectives[m])

            

            # 边界给予无限距离

            population[sorted_front[0]].crowding_distance = np.inf

            population[sorted_front[-1]].crowding_distance = np.inf

            

            # 范围

            obj_range = (population[sorted_front[-1]].objectives[m] - 

                        population[sorted_front[0]].objectives[m])

            

            if obj_range > 0:

                for i in range(1, n_front - 1):

                    distance = (population[sorted_front[i + 1]].objectives[m] - 

                               population[sorted_front[i - 1]].objectives[m]) / obj_range

                    population[sorted_front[i]].crowding_distance += distance

    

    def _selection(self, population: List[Individual]) -> List[Individual]:

        """二元锦标赛选择"""

        selected = []

        

        while len(selected) < self.pop_size:

            # 随机选两个

            idx1, idx2 = random.sample(range(len(population)), 2)

            ind1, ind2 = population[idx1], population[idx2]

            

            # 比较

            if ind1.rank < ind2.rank:

                selected.append(Individual(

                    variables=ind1.variables.copy(),

                    objectives=ind1.objectives.copy(),

                    rank=ind1.rank,

                    crowding_distance=ind1.crowding_distance

                ))

            elif ind1.rank > ind2.rank:

                selected.append(Individual(

                    variables=ind2.variables.copy(),

                    objectives=ind2.objectives.copy(),

                    rank=ind2.rank,

                    crowding_distance=ind2.crowding_distance

                ))

            else:

                # 同层级，选拥挤距离大的

                if ind1.crowding_distance >= ind2.crowding_distance:

                    selected.append(Individual(

                        variables=ind1.variables.copy(),

                        objectives=ind1.objectives.copy(),

                        rank=ind1.rank,

                        crowding_distance=ind1.crowding_distance

                    ))

                else:

                    selected.append(Individual(

                        variables=ind2.variables.copy(),

                        objectives=ind2.objectives.copy(),

                        rank=ind2.rank,

                        crowding_distance=ind2.crowding_distance

                    ))

        

        return selected

    

    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """模拟二进制交叉 (SBX)"""

        child1 = parent1.copy()

        child2 = parent2.copy()

        

        if random.random() > self.crossover_prob:

            return child1, child2

        

        for i in range(self.n_vars):

            if random.random() < 0.5:

                # SBX

                u = random.random()

                

                if u <= 0.5:

                    beta = (2 * u) ** (1 / (self.eta + 1))

                else:

                    beta = (1 / (2 * (1 - u))) ** (1 / (self.eta + 1))

                

                x1 = parent1[i]

                x2 = parent2[i]

                

                child1[i] = 0.5 * ((1 + beta) * x1 + (1 - beta) * x2)

                child2[i] = 0.5 * ((1 - beta) * x1 + (1 + beta) * x2)

            else:

                child1[i] = parent2[i]

                child2[i] = parent1[i]

        

        return child1, child2

    

    def _mutate(self, variables: np.ndarray) -> np.ndarray:

        """多项式变异"""

        mutated = variables.copy()

        

        for i in range(self.n_vars):

            if random.random() < self.mutation_prob:

                x = variables[i]

                x_min, x_max = self.bounds

                

                u = random.random()

                

                if u < 0.5:

                    delta = (2 * u) ** (1 / (self.eta + 1)) - 1

                else:

                    delta = 1 - (2 * (1 - u)) ** (1 / (self.eta + 1))

                

                mutated[i] = x + delta * (x_max - x_min)

                mutated[i] = np.clip(mutated[i], x_min, x_max)

        

        return mutated

    

    def _create_offspring(self, parents: List[Individual]) -> List[Individual]:

        """创建子代"""

        offspring = []

        

        for i in range(0, self.pop_size, 2):

            parent1 = parents[i % len(parents)].variables

            parent2 = parents[(i + 1) % len(parents)].variables

            

            child1_vars, child2_vars = self._crossover(parent1, parent2)

            

            child1_vars = self._mutate(child1_vars)

            child2_vars = self._mutate(child2_vars)

            

            offspring.append(Individual(variables=child1_vars))

            offspring.append(Individual(variables=child2_vars))

        

        return offspring[:self.pop_size]

    

    def _environmental_selection(self, 

                                 combined: List[Individual]) -> List[Individual]:

        """环境选择：选择下一代"""

        # 非支配排序

        fronts = self._non_dominated_sort(combined)

        

        new_population = []

        

        for front in fronts:

            # 计算拥挤距离

            self._crowding_distance(combined, front)

            

            # 如果加入会超过种群大小

            if len(new_population) + len(front) <= self.pop_size:

                for idx in front:

                    new_population.append(combined[idx])

            else:

                # 按拥挤距离排序

                front_sorted = sorted(front, 

                                     key=lambda x: combined[x].crowding_distance,

                                     reverse=True)

                

                remaining = self.pop_size - len(new_population)

                for i in range(remaining):

                    new_population.append(combined[front_sorted[i]])

                

                break

        

        return new_population

    

    def optimize(self, 

                 evaluate_func: Callable,

                 n_generations: int = 100,

                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:

        """

        运行NSGA-II优化

        

        参数:

            evaluate_func: 评估函数 f(x) -> [f1, f2, ...]

            n_generations: 迭代代数

            verbose: 是否打印进度

        

        返回:

            (最优解变量, Pareto前沿)

        """

        self.evaluate_func = evaluate_func

        

        # 初始化

        population = self._initialize_population()

        self._evaluate(population)

        

        # 世代迭代

        for gen in range(n_generations):

            # 非支配排序

            fronts = self._non_dominated_sort(population)

            

            # 计算拥挤距离

            for front in fronts:

                self._crowding_distance(population, front)

            

            # 选择

            selected = self._selection(population)

            

            # 交叉变异

            offspring = self._create_offspring(selected)

            self._evaluate(offspring)

            

            # 合并父子代

            combined = population + offspring

            

            # 环境选择

            population = self._environmental_selection(combined)

            

            if verbose and (gen + 1) % 20 == 0:

                # 获取当前Pareto前沿

                fronts = self._non_dominated_sort(population)

                pareto_front = [population[i].objectives for i in fronts[0]]

                print(f"Generation {gen + 1}: Best objectives = {pareto_front[0]}")

        

        # 最终排序

        fronts = self._non_dominated_sort(population)

        self._crowding_distance(population, fronts[0])

        

        # 返回结果

        pareto_vars = np.array([population[i].variables for i in fronts[0]])

        pareto_front = np.array([population[i].objectives for i in fronts[0]])

        

        return pareto_vars, pareto_front





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("NSGA-II 非支配排序遗传算法测试")

    print("=" * 50)

    

    random.seed(42)

    np.random.seed(42)

    

    # 测试函数：ZDT1

    def zdt1(x):

        f1 = x[0]

        g = 1 + 9 * np.sum(x[1:]) / 9

        f2 = g * (1 - np.sqrt(x[0] / g))

        return [f1, f2]

    

    # 测试函数：ZDT2

    def zdt2(x):

        f1 = x[0]

        g = 1 + 9 * np.sum(x[1:]) / 9

        f2 = g * (1 - (x[0] / g) ** 2)

        return [f1, f2]

    

    # 测试函数：Schaffer

    def schaffer(x):

        f1 = x[0] ** 2

        f2 = (x[0] - 2) ** 2

        return [f1, f2]

    

    print("\n--- ZDT1 问题 ---")

    nsga = NSGA2(n_vars=10, n_objectives=2, pop_size=100, n_generations=200)

    pareto_vars, pareto_front = nsga.optimize(zdt1, n_generations=200)

    

    print(f"Pareto前沿点数: {len(pareto_front)}")

    print(f"部分解: {pareto_front[:3]}")

    

    print("\n--- ZDT2 问题 ---")

    nsga2 = NSGA2(n_vars=10, n_objectives=2, pop_size=100)

    pareto_vars2, pareto_front2 = nsga2.optimize(zdt2, n_generations=200)

    

    print(f"Pareto前沿点数: {len(pareto_front2)}")

    print(f"部分解: {pareto_front2[:3]}")

    

    print("\n--- Schaffer 问题 ---")

    nsga3 = NSGA2(n_vars=1, n_objectives=2, pop_size=100, bounds=(-10, 10))

    pareto_vars3, pareto_front3 = nsga3.optimize(schaffer, n_generations=100)

    

    print(f"Pareto前沿点数: {len(pareto_front3)}")

    print(f"最优解变量: {pareto_vars3[0]}")

    print(f"最优目标值: {pareto_front3[0]}")

    

    print("\n" + "=" * 50)

    print("测试完成")

