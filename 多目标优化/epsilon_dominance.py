# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / epsilon_dominance



本文件实现 epsilon_dominance 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Callable, Optional

import random





def epsilon_dominance(obj1: np.ndarray, obj2: np.ndarray, 

                      epsilon: np.ndarray, minimize: bool = True) -> bool:

    """

    ε-支配判断

    

    obj1 ε-支配 obj2 当且仅当:

    - 对于所有目标: obj1[i] <= obj2[i] + ε[i]

    - 至少存在一个目标: obj1[i] < obj2[i] - ε[i]

    

    参数:

        obj1, obj2: 目标向量

        epsilon: ε容忍向量

        minimize: 是否最小化

    

    返回:

        True如果obj1 ε-支配obj2

    """

    if minimize:

        # 检查是否满足ε-支配条件

        not_worse = np.all(obj1 <= obj2 + epsilon)

        strictly_better = np.any(obj1 < obj2 - epsilon)

    else:

        not_worse = np.all(obj1 >= obj2 - epsilon)

        strictly_better = np.any(obj1 > obj2 + epsilon)

    

    return not_worse and strictly_better





def epsilon_dominance_sort(objectives: np.ndarray, 

                          epsilon: np.ndarray,

                          minimize: bool = True) -> List[List[int]]:

    """

    ε-非支配排序

    

    将目标空间划分为ε-等级

    """

    n = len(objectives)

    assigned = np.zeros(n, dtype=bool)

    fronts = []

    

    while not np.all(assigned):

        current_front = []

        

        for i in range(n):

            if assigned[i]:

                continue

            

            is_non_dominated = True

            for j in range(n):

                if i != j and not assigned[j]:

                    if epsilon_dominance(objectives[j], objectives[i], epsilon, minimize):

                        is_non_dominated = False

                        break

            

            if is_non_dominated:

                current_front.append(i)

                assigned[i] = True

        

        if current_front:

            fronts.append(current_front)

    

    return fronts





def epsilon_clear(objectives: np.ndarray, 

                 epsilon: np.ndarray,

                 minimize: bool = True) -> np.ndarray:

    """

    ε-清理：去除ε-等效解

    

    对于一组ε-等效的解，只保留一个代表

    

    参数:

        objectives: 目标矩阵

        epsilon: ε向量

    

    返回:

        清理后的解索引

    """

    n = len(objectives)

    keep = np.ones(n, dtype=bool)

    

    for i in range(n):

        if not keep[i]:

            continue

        

        for j in range(i + 1, n):

            if not keep[j]:

                continue

            

            # 检查是否ε-等效

            diff = np.abs(objectives[i] - objectives[j])

            

            if minimize:

                # i支配j且差距在ε内

                if np.all(objectives[i] <= objectives[j] + epsilon) and \

                   np.all(diff <= epsilon):

                    keep[j] = False

                elif np.all(objectives[j] <= objectives[i] + epsilon) and \

                     np.all(diff <= epsilon):

                    keep[i] = False

                    break

            else:

                if np.all(objectives[i] >= objectives[j] - epsilon) and \

                   np.all(diff <= epsilon):

                    keep[j] = False

                elif np.all(objectives[j] >= objectives[i] - epsilon) and \

                     np.all(diff <= epsilon):

                    keep[i] = False

                    break

    

    return np.where(keep)[0]





def adaptive_epsilon(objectives: np.ndarray, 

                     target_size: int,

                     minimize: bool = True) -> np.ndarray:

    """

    自适应ε计算

    

    根据目标函数范围和目标大小确定合适的ε

    

    参数:

        objectives: 目标矩阵

        target_size: 期望的解数量

    

    返回:

        ε向量

    """

    n, m = objectives.shape

    

    # 每个目标的范围

    f_range = np.max(objectives, axis=0) - np.min(objectives, axis=0)

    

    # 初始ε设为范围的某个比例

    # 目标：使清理后的解数接近target_size

    scale = (n / target_size) ** (1 / m)

    

    epsilon = f_range * (scale - 1) / scale

    

    return epsilon





class EpsilonMOEA:

    """

    基于ε-支配的多目标优化算法

    

    参数:

        n_vars: 决策变量维度

        n_objectives: 目标数量

        pop_size: 种群大小

        epsilon: 初始ε向量

        bounds: 变量边界

    """

    

    def __init__(self, n_vars: int, n_objectives: int,

                 pop_size: int = 100,

                 epsilon: Optional[np.ndarray] = None,

                 bounds: Tuple[float, float] = (0, 1)):

        self.n_vars = n_vars

        self.n_objectives = n_objectives

        self.pop_size = pop_size

        self.epsilon = epsilon if epsilon is not None else np.ones(n_objectives) * 0.01

        self.bounds = bounds

        

        # 种群

        self.population = []

        self.objectives = []

        

        # 档案

        self.archive = []

        self.archive_objectives = []

        

        self.evaluate_func = None

        

        # 参数

        self.crossover_prob = 0.9

        self.mutation_prob = 0.1

        self.eta = 20.0

    

    def _initialize(self):

        """初始化"""

        self.population = [

            np.random.uniform(self.bounds[0], self.bounds[1], self.n_vars)

            for _ in range(self.pop_size)

        ]

        

        self.archive = self.population.copy()

    

    def _evaluate(self) -> List[np.ndarray]:

        """评估种群"""

        return [np.array(self.evaluate_func(ind)) for ind in self.population]

    

    def _update_archive(self):

        """更新ε-档案"""

        # 合并种群和档案

        combined = self.population + self.archive

        combined_obj = self.objectives + self.archive_objectives

        

        n = len(combined)

        is_epsilon_nondominated = np.ones(n, dtype=bool)

        

        # ε-非支配排序

        for i in range(n):

            if not is_epsilon_nondominated[i]:

                continue

            

            for j in range(n):

                if i != j and is_epsilon_nondominated[j]:

                    if epsilon_dominance(combined_obj[j], combined_obj[i], self.epsilon):

                        is_epsilon_nondominated[i] = False

                        break

        

        # 获取ε-非支配解

        new_archive = [combined[i] for i in range(n) if is_epsilon_nondominated[i]]

        new_archive_obj = [combined_obj[i] for i in range(n) if is_epsilon_nondominated[i]]

        

        # ε-清理

        if len(new_archive_obj) > 0:

            obj_array = np.array(new_archive_obj)

            keep_indices = epsilon_clear(obj_array, self.epsilon)

            

            self.archive = [new_archive[i] for i in keep_indices]

            self.archive_objectives = [new_archive_obj[i] for i in keep_indices]

        else:

            self.archive = []

            self.archive_objectives = []

    

    def _crossover(self, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:

        """SBX交叉"""

        child = p1.copy()

        

        if random.random() > self.crossover_prob:

            return child

        

        for i in range(self.n_vars):

            if random.random() < 0.5:

                u = random.random()

                if u <= 0.5:

                    beta = (2 * u) ** (1 / (self.eta + 1))

                else:

                    beta = (1 / (2 * (1 - u))) ** (1 / (self.eta + 1))

                

                child[i] = 0.5 * ((1 + beta) * p1[i] + (1 - beta) * p2[i])

        

        return np.clip(child, self.bounds[0], self.bounds[1])

    

    def _mutate(self, x: np.ndarray) -> np.ndarray:

        """多项式变异"""

        mutated = x.copy()

        

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

    

    def _select_parents(self) -> List[np.ndarray]:

        """二元锦标赛选择（基于ε-支配）"""

        parents = []

        

        for _ in range(self.pop_size):

            i, j = random.sample(range(len(self.archive)), 2)

            

            obj_i = self.archive_objectives[i]

            obj_j = self.archive_objectives[j]

            

            if epsilon_dominance(obj_i, obj_j, self.epsilon):

                parents.append(self.archive[i].copy())

            elif epsilon_dominance(obj_j, obj_i, self.epsilon):

                parents.append(self.archive[j].copy())

            else:

                # 随机选择

                parents.append(self.archive[i].copy() if random.random() < 0.5 

                             else self.archive[j].copy())

        

        return parents

    

    def optimize(self, evaluate_func: Callable,

                 n_generations: int = 200,

                 adaptive_epsilon: bool = False,

                 target_archive_size: int = 100,

                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:

        """

        运行优化

        """

        self.evaluate_func = evaluate_func

        self._initialize()

        

        for gen in range(n_generations):

            # 选择

            parents = self._select_parents()

            

            # 交叉变异

            offspring = []

            for i in range(0, self.pop_size, 2):

                p1, p2 = parents[i], parents[(i + 1) % len(parents)]

                c1 = self._mutate(self._crossover(p1, p2))

                c2 = self._mutate(self._crossover(p2, p1))

                offspring.extend([c1, c2])

            

            self.population = offspring[:self.pop_size]

            self.objectives = self._evaluate()

            

            # 更新档案

            self._update_archive()

            

            # 自适应ε调整

            if adaptive_epsilon and len(self.archive_objectives) > target_archive_size:

                self.epsilon = adaptive_epsilon(np.array(self.archive_objectives), 

                                                target_archive_size)

            

            if verbose and (gen + 1) % 20 == 0:

                print(f"Generation {gen + 1}: Archive size = {len(self.archive)}, "

                      f"ε = {self.epsilon}")

        

        return np.array(self.archive), np.array(self.archive_objectives)





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("ε-支配与ε-清理测试")

    print("=" * 50)

    

    random.seed(42)

    np.random.seed(42)

    

    # 测试ε-支配

    print("\n--- ε-支配测试 ---")

    

    obj1 = np.array([1.0, 2.0])

    obj2 = np.array([1.2, 2.1])

    epsilon = np.array([0.1, 0.1])

    

    is_epsilon_dom = epsilon_dominance(obj1, obj2, epsilon)

    print(f"obj1={obj1}, obj2={obj2}, ε={epsilon}")

    print(f"obj1 ε-支配 obj2: {is_epsilon_dom}")

    

    # 生成测试数据

    print("\n--- ε-非支配排序 ---")

    

    objectives = np.random.rand(50, 2)

    objectives[:, 1] = 1 - objectives[:, 0] + np.random.randn(50) * 0.1

    

    epsilon = np.array([0.05, 0.05])

    fronts = epsilon_dominance_sort(objectives, epsilon)

    

    print(f"ε-等级数: {len(fronts)}")

    for i, front in enumerate(fronts[:5]):

        print(f"  第{i+1}层: {len(front)} 个解")

    

    # ε-清理

    print("\n--- ε-清理 ---")

    

    test_obj = np.array([

        [1.0, 1.0],

        [1.02, 1.01],  # ε-等效于上面的

        [2.0, 2.0],

        [0.5, 0.5],

        [0.52, 0.48]   # ε-等效于上面的

    ])

    

    epsilon_test = np.array([0.1, 0.1])

    keep_idx = epsilon_clear(test_obj, epsilon_test)

    

    print(f"原始: {len(test_obj)} 个解, 清理后: {len(keep_idx)} 个解")

    print(f"保留的解: {test_obj[keep_idx]}")

    

    # 自适应ε

    print("\n--- 自适应ε计算 ---")

    

    large_set = np.random.rand(200, 2)

    large_set[:, 1] = 1 - large_set[:, 0] + np.random.randn(200) * 0.1

    

    target_size = 50

    epsilon_adaptive = adaptive_epsilon(large_set, target_size)

    

    print(f"目标大小: {target_size}, 自适应ε: {epsilon_adaptive}")

    

    # 完整算法测试

    print("\n--- ε-MOEA测试 ---")

    

    def zdt1(x):

        f1 = x[0]

        g = 1 + 9 * np.sum(x[1:]) / 9

        f2 = g * (1 - np.sqrt(x[0] / g))

        return [f1, f2]

    

    moea = EpsilonMOEA(n_vars=10, n_objectives=2, pop_size=100,

                       epsilon=np.array([0.01, 0.01]))

    archive, archive_obj = moea.optimize(zdt1, n_generations=200)

    

    print(f"档案大小: {len(archive)}")

    print(f"前5个解: {archive_obj[:5]}")

    

    print("\n" + "=" * 50)

    print("测试完成")

