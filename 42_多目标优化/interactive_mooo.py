# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / interactive_mooo



本文件实现 interactive_mooo 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Callable, Optional, Dict

from dataclasses import dataclass





@dataclass

class ReferencePoint:

    """参照点"""

    objectives: np.ndarray

    name: str = ""

    

    def distance_to(self, obj: np.ndarray) -> float:

        """计算到目标的欧氏距离"""

        return np.linalg.norm(self.objectives - obj)





@dataclass

class Preference:

    """偏好信息"""

    type: str  # 'point', 'region', 'weight'

    data: any





class InteractiveOptimizer:

    """

    交互式多目标优化器

    

    支持：

    - 参照点输入

    - 权重调整

    - 区域偏好

    """

    

    def __init__(self, evaluate_func: Callable, n_objectives: int,

                 bounds: List[Tuple[float, float]],

                 initial_population: Optional[np.ndarray] = None):

        self.evaluate_func = evaluate_func

        self.n_objectives = n_objectives

        self.bounds = bounds

        

        # 当前种群

        if initial_population is not None:

            self.population = initial_population

        else:

            n_vars = len(bounds)

            self.population = np.random.uniform(

                [b[0] for b in bounds],

                [b[1] for b in bounds],

                (100, n_vars)

            )

        

        # 评估

        self.objectives = np.array([evaluate_func(x) for x in self.population])

        

        # 参照点

        self.reference_points: List[ReferencePoint] = []

        

        # 理想点和最差点

        self._update_extremes()

    

    def _update_extremes(self):

        """更新理想点和最差点"""

        self.ideal_point = np.min(self.objectives, axis=0)

        self.nadir_point = np.max(self.objectives, axis=0)

    

    def add_reference_point(self, objectives: np.ndarray, name: str = ""):

        """添加参照点"""

        ref = ReferencePoint(objectives=np.array(objectives), name=name)

        self.reference_points.append(ref)

    

    def clear_reference_points(self):

        """清空参照点"""

        self.reference_points = []

    

    def _Decompose_with_reference(self, ref_point: np.ndarray) -> float:

        """

        使用参照点分解

        

        使用Tchebychev距离

        """

        # 归一化

        range_obj = self.nadir_point - self.ideal_point

        range_obj = np.maximum(range_obj, 1e-10)

        

        normalized_obj = (self.objectives - self.ideal_point) / range_obj

        normalized_ref = (ref_point - self.ideal_point) / range_obj

        

        # Tchebychev距离

        distances = np.max(np.abs(normalized_obj - normalized_ref), axis=1)

        

        return np.min(distances)

    

    def optimize_towards_reference(self, ref_point: np.ndarray,

                                  n_iterations: int = 20,

                                  step_size: float = 0.1) -> np.ndarray:

        """

        朝着参照点优化

        

        参数:

            ref_point: 参照点目标值

            n_iterations: 迭代次数

            step_size: 更新步长

        

        返回:

            优化后的解

        """

        ref_point = np.array(ref_point)

        

        for iteration in range(n_iterations):

            # 计算每个解到参照点的距离

            distances = np.array([

                np.linalg.norm(obj - ref_point) for obj in self.objectives

            ])

            

            # 选择最近的解

            best_idx = np.argmin(distances)

            best_solution = self.population[best_idx]

            best_obj = self.objectives[best_idx]

            

            # 计算梯度方向（简化：朝向参照点的方向）

            if np.linalg.norm(best_obj - ref_point) < 1e-6:

                break

            

            direction = ref_point - best_obj

            direction = direction / (np.linalg.norm(direction) + 1e-10)

            

            # 更新解

            # 这里需要根据具体问题定义梯度，这里用随机搜索代替

            for i in range(len(self.population)):

                if np.random.random() < 0.1:

                    # 随机扰动

                    perturbation = np.random.randn(len(self.population[i])) * 0.1

                    new_solution = np.clip(

                        self.population[i] + step_size * perturbation,

                        [b[0] for b in self.bounds],

                        [b[1] for b in self.bounds]

                    )

                    

                    new_obj = self.evaluate_func(new_solution)

                    

                    # 如果改善，更新

                    if np.linalg.norm(new_obj - ref_point) < np.linalg.norm(self.objectives[i] - ref_point):

                        self.population[i] = new_solution

                        self.objectives[i] = new_obj

            

            self._update_extremes()

        

        return self.population[np.argmin([

            np.linalg.norm(obj - ref_point) for obj in self.objectives

        ])]

    

    def weight_based_optimization(self, weights: np.ndarray,

                                  n_iterations: int = 20) -> np.ndarray:

        """

        基于权重的优化

        

        使用加权求和优化特定方向

        """

        weights = np.array(weights) / np.sum(weights)

        

        for iteration in range(n_iterations):

            # 计算加权目标值

            weighted_scores = self.objectives @ weights

            

            # 选择最优的几个

            top_indices = np.argsort(weighted_scores)[:10]

            

            # 在最优解附近搜索

            for idx in top_indices:

                best = self.population[idx]

                

                for _ in range(5):

                    perturbation = np.random.randn(len(best)) * 0.05

                    new_solution = np.clip(

                        best + perturbation,

                        [b[0] for b in self.bounds],

                        [b[1] for b in self.bounds]

                    )

                    

                    new_obj = self.evaluate_func(new_solution)

                    

                    # 比较加权分数

                    old_score = self.objectives[idx] @ weights

                    new_score = new_obj @ weights

                    

                    if new_score < old_score:

                        # 找到更好的解

                        idx_in_pop = np.where(np.all(self.population == self.population[idx], axis=1))[0]

                        if len(idx_in_pop) > 0:

                            self.population[idx_in_pop[0]] = new_solution

                            self.objectives[idx_in_pop[0]] = new_obj

        

        # 返回加权最优的解

        best_idx = np.argmin(self.objectives @ weights)

        return self.population[best_idx], self.objectives[best_idx]

    

    def preference_based_recombination(self, preference: Preference,

                                       n_offspring: int = 20) -> np.ndarray:

        """

        基于偏好的重组

        

        参数:

            preference: 偏好信息

            n_offspring: 生成的子代数量

        

        返回:

            新生成的解

        """

        offspring = []

        

        if preference.type == 'weight':

            weights = preference.data

            weights = np.array(weights) / np.sum(weights)

            

            # 选择加权目标值最低的解

            scores = self.objectives @ weights

            elite_indices = np.argsort(scores)[:10]

            

            # 在精英附近生成新解

            for _ in range(n_offspring):

                idx1, idx2 = np.random.choice(elite_indices, 2, replace=False)

                

                # 交叉

                child = (self.population[idx1] + self.population[idx2]) / 2

                

                # 变异

                if np.random.random() < 0.3:

                    child = child + np.random.randn(len(child)) * 0.1

                

                child = np.clip(child, [b[0] for b in self.bounds], [b[1] for b in self.bounds])

                offspring.append(child)

        

        elif preference.type == 'region':

            # 区域偏好：在指定目标范围内搜索

            obj_min, obj_max = preference.data

            

            valid_indices = []

            for i, obj in enumerate(self.objectives):

                if np.all(obj >= obj_min) and np.all(obj <= obj_max):

                    valid_indices.append(i)

            

            if len(valid_indices) > 0:

                # 在区域内解附近搜索

                for _ in range(n_offspring):

                    idx = np.random.choice(valid_indices)

                    child = self.population[idx] + np.random.randn(len(self.population[idx])) * 0.1

                    child = np.clip(child, [b[0] for b in self.bounds], [b[1] for b in self.bounds])

                    offspring.append(child)

            else:

                # 如果没有解在区域内，在整个种群搜索

                for _ in range(n_offspring):

                    idx = np.random.randint(len(self.population))

                    child = self.population[idx] + np.random.randn(len(self.population[idx])) * 0.1

                    child = np.clip(child, [b[0] for b in self.bounds], [b[1] for b in self.bounds])

                    offspring.append(child)

        

        return np.array(offspring)

    

    def get_pareto_front(self) -> np.ndarray:

        """获取当前Pareto前沿"""

        n = len(self.objectives)

        is_pareto = np.ones(n, dtype=bool)

        

        for i in range(n):

            for j in range(n):

                if i != j and is_pareto[i]:

                    if np.all(self.objectives[j] <= self.objectives[i]) and \

                       np.any(self.objectives[j] < self.objectives[i]):

                        is_pareto[i] = False

                        break

        

        return self.objectives[is_pareto]





class NIMBUS:

    """

    NIMBUS (Navigation Interactive Multiobjective Optimization)

    

    基于分类的交互式多目标优化方法

    """

    

    def __init__(self, evaluate_func: Callable, n_objectives: int,

                 bounds: List[Tuple[float, float]]):

        self.evaluate_func = evaluate_func

        self.n_objectives = n_objectives

        self.bounds = bounds

        

        self.current_solution = None

        self.current_objectives = None

        

        # 分类结果

        self.classification = {

            'too_much': [],    # 需要减少的目标

            'too_little': [],  # 需要增加的目标

            'acceptable': [],  # 可接受的目标

            'indifferent': []  # 无所谓的目标

        }

    

    def set_solution(self, x: np.ndarray):

        """设置当前解"""

        self.current_solution = x

        self.current_objectives = evaluate_func(x)

    

    def classify_objectives(self, reference_levels: np.ndarray):

        """

        分类目标

        

        参数:

            reference_levels: 参考水平（决策者提供）

        """

        obj = self.current_objectives

        

        self.classification = {

            'too_much': [],

            'too_little': [],

            'acceptable': [],

            'indifferent': []

        }

        

        for i in range(self.n_objectives):

            if obj[i] > reference_levels[i]:

                self.classification['too_much'].append(i)

            elif obj[i] < reference_levels[i]:

                self.classification['too_little'].append(i)

            else:

                self.classification['acceptable'].append(i)

    

    def generate_aspiration_points(self) -> List[np.ndarray]:

        """

        生成期望点

        """

        aspiration_points = []

        

        if len(self.classification['too_much']) == 0:

            return aspiration_points

        

        # 每个需要减少的目标生成一个期望点

        for i in self.classification['too_much']:

            asp = self.current_objectives.copy()

            asp[i] = reference_levels[i]  # 降到参考水平

            aspiration_points.append(asp)

        

        return aspiration_points

    

    def optimize_classified(self, aspiration_point: np.ndarray) -> np.ndarray:

        """

        优化到期望点

        

        解决一个约束子问题：

        min max(f_i - asp_i) for i in too_much

        s.t. f_j >= ref_j for j in too_little

        """

        # 简化：使用加权法

        weights = np.ones(self.n_objectives)

        for i in self.classification['too_much']:

            weights[i] = 10.0  # 重点优化

        

        # 使用当前解作为起点

        best = self.current_solution.copy()

        

        for _ in range(50):

            # 随机搜索

            candidate = best + np.random.randn(len(best)) * 0.1

            candidate = np.clip(candidate, [b[0] for b in self.bounds], [b[1] for b in self.bounds])

            

            cand_obj = self.evaluate_func(candidate)

            

            # 评估

            old_violation = max(0, np.max(self.current_objectives - aspiration_point))

            new_violation = max(0, np.max(cand_obj - aspiration_point))

            

            if new_violation < old_violation:

                best = candidate

                self.current_objectives = cand_obj

        

        self.current_solution = best

        return best





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("交互式多目标优化测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 测试函数

    def test_func(x):

        f1 = x[0] ** 2

        f2 = (x[0] - 2) ** 2

        return np.array([f1, f2])

    

    bounds = [(-5, 5)]

    

    print("\n--- 交互式优化器 ---")

    optimizer = InteractiveOptimizer(test_func, n_objectives=2, bounds=bounds)

    

    print(f"初始种群: {len(optimizer.population)} 个解")

    pareto = optimizer.get_pareto_front()

    print(f"初始Pareto前沿: {len(pareto)} 个点")

    

    # 添加参照点

    print("\n--- 参照点优化 ---")

    ref_point = np.array([0.5, 0.5])

    optimizer.add_reference_point(ref_point, "target1")

    

    # 优化

    best_solution = optimizer.optimize_towards_reference(ref_point, n_iterations=30)

    print(f"优化后的解: x={best_solution[0]:.4f}")

    print(f"目标值: {test_func(best_solution)}")

    

    # 权重优化

    print("\n--- 权重优化 ---")

    weights = np.array([0.3, 0.7])

    sol, obj = optimizer.weight_based_optimization(weights, n_iterations=30)

    print(f"权重{weights}下的最优解: x={sol[0]:.4f}")

    print(f"目标值: {obj}")

    

    # 基于偏好的重组

    print("\n--- 偏好重组 ---")

    pref = Preference(type='weight', data=np.array([0.8, 0.2]))

    offspring = optimizer.preference_based_recombination(pref, n_offspring=10)

    print(f"生成 {len(offspring)} 个新解")

    

    print("\n--- NIMBUS ---")

    nimbus = NIMBUS(test_func, n_objectives=2, bounds=bounds)

    

    # 设置初始解

    initial_x = np.array([1.5])

    nimbus.set_solution(initial_x)

    print(f"当前解: x={initial_x[0]:.4f}")

    print(f"当前目标: {nimbus.current_objectives}")

    

    # 分类

    ref_levels = np.array([0.3, 0.8])

    nimbus.classify_objectives(ref_levels)

    print(f"参考水平: {ref_levels}")

    print(f"分类结果: {nimbus.classification}")

    

    # 生成期望点

    aspirations = nimbus.generate_aspiration_points()

    print(f"期望点: {aspirations}")

    

    print("\n" + "=" * 50)

    print("测试完成")

