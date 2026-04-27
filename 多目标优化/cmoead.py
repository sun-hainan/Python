# -*- coding: utf-8 -*-
"""
算法实现：多目标优化 / cmoead

本文件实现 cmoead 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Callable, Optional
import random


def constraint_dominance(obj1: np.ndarray, cv1: float,
                        obj2: np.ndarray, cv2: float,
                        minimize: bool = True) -> bool:
    """
    约束支配判断
    
    规则：
    1. 两个都可行时，用Pareto支配
    2. 一个可行一个不可行，可行的支配不可行的
    3. 两个都不可行，约束违反度小的支配约束违反度大的
    
    参数:
        obj1, obj2: 目标向量
        cv1, cv2: 约束违反度
        minimize: 是否最小化
    
    返回:
        True如果obj1支配obj2
    """
    # 两个都可行
    if cv1 <= 0 and cv2 <= 0:
        if minimize:
            return (np.all(obj1 <= obj2) and np.any(obj1 < obj2))
        else:
            return (np.all(obj1 >= obj2) and np.any(obj1 > obj2))
    
    # obj1可行，obj2不可行
    if cv1 <= 0 and cv2 > 0:
        return True
    
    # obj1不可行，obj2可行
    if cv1 > 0 and cv2 <= 0:
        return False
    
    # 两个都不可行，约束违反度小的支配大的
    return cv1 < cv2


class CMOEAD:
    """
    约束MOEA/D算法
    
    参数:
        n_vars: 决策变量维度
        n_objectives: 目标数量
        n_constraints: 约束数量
        pop_size: 种群大小
        neighborhood_size: 邻居大小
        bounds: 变量边界
    """
    
    def __init__(self, n_vars: int, n_objectives: int, n_constraints: int = 0,
                 pop_size: int = 100,
                 neighborhood_size: int = 20,
                 bounds: Tuple[float, float] = (0, 1)):
        self.n_vars = n_vars
        self.n_objectives = n_objectives
        self.n_constraints = n_constraints
        self.pop_size = pop_size
        self.neighborhood_size = neighborhood_size
        self.bounds = bounds
        
        # 权重向量
        self.weight_vectors = self._generate_weight_vectors()
        
        # 邻居
        self.neighbors = self._compute_neighbors()
        
        # 种群
        self.population = np.zeros((pop_size, n_vars))
        self.objectives = np.zeros((pop_size, n_objectives))
        self.constraints = np.zeros((pop_size, n_constraints))
        self.constraint_violations = np.zeros(pop_size)
        
        # 参考点
        self.z = np.zeros(n_objectives)
        
        # 参数
        self.crossover_prob = 0.9
        self.mutation_prob = 0.1
        self.eta = 20.0
        
        self.evaluate_func = None
        self.constraint_func = None
    
    def _generate_weight_vectors(self) -> np.ndarray:
        """生成权重向量"""
        n_obj = self.n_objectives
        n_div = self.pop_size - 1
        
        def generate_recursive(n, depth, current):
            if depth == n - 1:
                return [current + [1.0]]
            result = []
            for i in range(n_div + 1):
                frac = i / n_div
                result.extend(generate_recursive(n, depth + 1, current + [frac]))
            return result
        
        weights = generate_recursive(n_obj, 0, [])
        weight_vectors = []
        for w in weights:
            w = np.array(w)
            w_sum = np.sum(w)
            if w_sum > 0:
                w = w / w_sum
            weight_vectors.append(w)
        
        return np.array(weight_vectors[:self.pop_size])
    
    def _compute_neighbors(self) -> List[List[int]]:
        """计算邻居"""
        n = self.pop_size
        distances = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(self.weight_vectors[i] - self.weight_vectors[j])
                distances[i, j] = dist
                distances[j, i] = dist
        
        neighbors = []
        for i in range(n):
            neighbor_indices = np.argsort(distances[i])[:self.neighborhood_size]
            neighbors.append(neighbor_indices.tolist())
        
        return neighbors
    
    def _evaluate_constraints(self, x: np.ndarray) -> Tuple[np.ndarray, float]:
        """评估约束"""
        if self.constraint_func is None:
            return np.array([]), 0.0
        
        constraints = self.constraint_func(x)
        cv = np.sum(np.maximum(0, constraints))  # 约束违反度
        
        return constraints, cv
    
    def _decompose(self, obj: np.ndarray, weight: np.ndarray) -> float:
        """Tchebychev分解"""
        return np.max(weight * np.abs(obj - self.z))
    
    def _initialize(self):
        """初始化"""
        self.population = np.random.uniform(
            self.bounds[0], self.bounds[1],
            (self.pop_size, self.n_vars)
        )
        
        for i in range(self.pop_size):
            self.objectives[i] = self.evaluate_func(self.population[i])
            
            if self.n_constraints > 0:
                self.constraints[i], self.constraint_violations[i] = \
                    self._evaluate_constraints(self.population[i])
        
        # 更新理想点（只用可行解）
        feasible = self.constraint_violations <= 0
        if np.any(feasible):
            self.z = np.min(self.objectives[feasible], axis=0)
        else:
            self.z = np.min(self.objectives, axis=0)
    
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
    
    def _update_solution(self, idx: int, child_obj: np.ndarray,
                         child_vars: np.ndarray, child_cv: float):
        """更新解（使用约束支配）"""
        # 当前解的分解值
        current_decomposed = self._decompose(self.objectives[idx], self.weight_vectors[idx])
        new_decomposed = self._decompose(child_obj, self.weight_vectors[idx])
        
        # 约束支配判断
        should_update = constraint_dominance(
            child_obj, child_cv,
            self.objectives[idx], self.constraint_violations[idx]
        )
        
        if should_update and new_decomposed < current_decomposed:
            self.population[idx] = child_vars
            self.objectives[idx] = child_obj
            self.constraint_violations[idx] = child_cv
            
            # 更新理想点（可行解）
            if child_cv <= 0:
                self.z = np.minimum(self.z, child_obj)
            
            return True
        
        return False
    
    def _update_neighbors(self, idx: int, child_obj: np.ndarray,
                          child_vars: np.ndarray, child_cv: float):
        """更新邻居"""
        for j in self.neighbors[idx][:self.neighborhood_size // 2]:
            current_decomposed = self._decompose(self.objectives[j], self.weight_vectors[j])
            new_decomposed = self._decompose(child_obj, self.weight_vectors[j])
            
            should_update = constraint_dominance(
                child_obj, child_cv,
                self.objectives[j], self.constraint_violations[j]
            )
            
            if should_update and new_decomposed < current_decomposed:
                self.population[j] = child_vars
                self.objectives[j] = child_obj
                self.constraint_violations[j] = child_cv
                
                if child_cv <= 0:
                    self.z = np.minimum(self.z, child_obj)
    
    def optimize(self, evaluate_func: Callable,
                 constraint_func: Optional[Callable] = None,
                 n_generations: int = 200,
                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        运行c-MOEA/D优化
        """
        self.evaluate_func = evaluate_func
        self.constraint_func = constraint_func
        
        self._initialize()
        
        for gen in range(n_generations):
            for i in range(self.pop_size):
                # 选择交配伙伴
                neighbors = self.neighbors[i]
                if len(neighbors) < 2:
                    continue
                
                idx1, idx2 = random.sample(neighbors, 2)
                
                # 交叉
                parent1 = self.population[i]
                parent2 = self.population[idx1] if random.random() < 0.5 else self.population[idx2]
                
                child_vars = self._crossover(parent1, parent2)
                child_vars = self._mutate(child_vars)
                
                # 评估
                child_obj = evaluate_func(child_vars)
                child_cv = 0.0
                if self.n_constraints > 0:
                    _, child_cv = self._evaluate_constraints(child_vars)
                
                # 更新
                self._update_solution(i, child_obj, child_vars, child_cv)
                self._update_neighbors(i, child_obj, child_vars, child_cv)
            
            if verbose and (gen + 1) % 20 == 0:
                feasible_mask = self.constraint_violations <= 0
                if np.any(feasible_mask):
                    best_obj = self.objectives[feasible_mask][0]
                    print(f"Generation {gen + 1}: Best feasible = {best_obj}")
                else:
                    min_cv = np.min(self.constraint_violations)
                    print(f"Generation {gen + 1}: Min CV = {min_cv}")
        
        # 返回可行解
        feasible_mask = self.constraint_violations <= 0
        if np.any(feasible_mask):
            return self.population[feasible_mask], \
                   self.objectives[feasible_mask], \
                   self.constraint_violations[feasible_mask]
        else:
            return self.population, self.objectives, self.constraint_violations


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("约束多目标优化 c-MOEA/D 测试")
    print("=" * 50)
    
    random.seed(42)
    np.random.seed(42)
    
    # 测试函数（带约束）
    def zdt1(x):
        f1 = x[0]
        g = 1 + 9 * np.sum(x[1:]) / 9
        f2 = g * (1 - np.sqrt(x[0] / g))
        return np.array([f1, f2])
    
    # 约束函数：g(x) <= 0
    def constraint1(x):
        f1, f2 = zdt1(x)
        # 约束：f1 + f2 >= 0.5
        return [0.5 - f1 - f2]
    
    print("\n--- 无约束ZDT1问题 ---")
    cmoead = CMOEAD(n_vars=10, n_objectives=2, n_constraints=0,
                    pop_size=100, neighborhood_size=20)
    pop, obj, cv = cmoead.optimize(zdt1, n_generations=200)
    
    print(f"解的数量: {len(pop)}")
    print(f"可行解数量: {np.sum(cv <= 0)}")
    print(f"前5个目标值:\n{obj[:5]}")
    
    print("\n--- 带约束问题 ---")
    cmoead2 = CMOEAD(n_vars=10, n_objectives=2, n_constraints=1,
                    pop_size=100)
    pop2, obj2, cv2 = cmoead2.optimize(zdt1, constraint_func=constraint1,
                                       n_generations=200)
    
    print(f"解的数量: {len(pop2)}")
    print(f"可行解数量: {np.sum(cv2 <= 0)}")
    if np.any(cv2 <= 0):
        feasible_obj = obj2[cv2 <= 0]
        print(f"可行解前5个:\n{feasible_obj[:5]}")
    
    # 简单约束测试
    print("\n--- 简单约束优化 ---")
    
    def simple_obj(x):
        return np.array([x[0]**2, (x[0]-2)**2])
    
    def simple_constraint(x):
        # 约束：x <= 1 (即 1 - x >= 0)
        return [x[0] - 1]
    
    cmoead3 = CMOEAD(n_vars=1, n_objectives=2, n_constraints=1,
                    pop_size=50, bounds=(-5, 5))
    pop3, obj3, cv3 = cmoead3.optimize(simple_obj, constraint_func=simple_constraint,
                                       n_generations=100)
    
    print(f"可行解数量: {np.sum(cv3 <= 0)}")
    if np.any(cv3 <= 0):
        feasible = obj3[cv3 <= 0]
        print(f"可行解目标:\n{feasible}")
    
    print("\n" + "=" * 50)
    print("测试完成")
