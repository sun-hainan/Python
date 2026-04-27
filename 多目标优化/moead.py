# -*- coding: utf-8 -*-
"""
算法实现：多目标优化 / moead

本文件实现 moead 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Callable, Optional
import random


class MOEAD:
    """
    MOEA/D算法
    
    参数:
        n_vars: 决策变量维度
        n_objectives: 目标数量
        pop_size: 种群大小（通常等于权重向量数）
        neighborhood_size: 邻居大小
        decomposition: 分解方法 ('ws', 'te', 'pbi')
        bounds: 变量边界
    """
    
    def __init__(self, n_vars: int, n_objectives: int,
                 pop_size: int = 100,
                 neighborhood_size: int = 20,
                 decomposition: str = 'te',
                 bounds: Tuple[float, float] = (0, 1)):
        self.n_vars = n_vars
        self.n_objectives = n_objectives
        self.pop_size = pop_size
        self.neighborhood_size = neighborhood_size
        self.decomposition = decomposition
        self.bounds = bounds
        
        # 生成权重向量
        self.weight_vectors = self._generate_weight_vectors()
        
        # 邻居关系
        self.neighbors = self._compute_neighbors()
        
        # 当前种群
        self.population = np.zeros((pop_size, n_vars))
        self.objectives = np.zeros((pop_size, n_objectives))
        
        # 参考点
        self.z = np.zeros(n_objectives)  # 理想点
        
        # 算法参数
        self.crossover_prob = 0.9
        self.mutation_prob = 0.1
        self.eta = 20.0
        
        self.evaluate_func = None
    
    def _generate_weight_vectors(self) -> np.ndarray:
        """生成均匀分布的权重向量（Das-Dennis风格）"""
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
        
        # 归一化
        weight_vectors = []
        for w in weights:
            w = np.array(w)
            w_sum = np.sum(w)
            if w_sum > 0:
                w = w / w_sum
            weight_vectors.append(w)
        
        # 添加极端权重
        for i in range(n_obj):
            w = np.zeros(n_obj)
            w[i] = 1.0
            weight_vectors.append(w)
        
        return np.array(weight_vectors[:self.pop_size])
    
    def _compute_neighbors(self) -> List[List[int]]:
        """计算每个权重的邻居（基于欧氏距离）"""
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
    
    def _decompose(self, obj: np.ndarray, weight: np.ndarray) -> float:
        """
        分解函数
        
        参数:
            obj: 目标值
            weight: 权重向量
        
        返回:
            标量值
        """
        if self.decomposition == 'ws':
            # 加权求和
            return np.sum(obj * weight)
        
        elif self.decomposition == 'te':
            # Tchebychev
            return np.max(weight * np.abs(obj - self.z))
        
        elif self.decomposition == 'pbi':
            # 边界交叉法（PBI）
            d1 = np.sum((obj - self.z) * weight) / np.linalg.norm(weight)
            
            d2_norm = obj - self.z - d1 * weight / np.linalg.norm(weight)
            d2 = np.linalg.norm(d2_norm)
            
            return d1 + 5 * d2  # penalty参数theta=5
        
        else:
            return np.sum(obj * weight)
    
    def _initialize_population(self):
        """初始化种群"""
        self.population = np.random.uniform(
            self.bounds[0], self.bounds[1],
            (self.pop_size, self.n_vars)
        )
        
        # 评估
        for i in range(self.pop_size):
            self.objectives[i] = self.evaluate_func(self.population[i])
        
        # 更新理想点
        self.z = np.min(self.objectives, axis=0)
    
    def _mating_restriction(self, idx: int, mating_pool_size: int = 2) -> List[int]:
        """限制交配：只在邻居中选择"""
        neighbors = self.neighbors[idx]
        
        if len(neighbors) < mating_pool_size:
            return neighbors
        
        return random.sample(neighbors, mating_pool_size)
    
    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> np.ndarray:
        """模拟二进制交叉"""
        child = parent1.copy()
        
        if random.random() > self.crossover_prob:
            return child
        
        for i in range(self.n_vars):
            if random.random() < 0.5:
                u = random.random()
                
                if u <= 0.5:
                    beta = (2 * u) ** (1 / (self.eta + 1))
                else:
                    beta = (1 / (2 * (1 - u))) ** (1 / (self.eta + 1))
                
                child[i] = 0.5 * ((1 + beta) * parent1[i] + (1 - beta) * parent2[i])
        
        return np.clip(child, self.bounds[0], self.bounds[1])
    
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
    
    def _update_solution(self, idx: int, child_obj: np.ndarray, 
                         child_vars: np.ndarray):
        """更新解"""
        # 当前解的分解值
        current_decomposed = self._decompose(self.objectives[idx], self.weight_vectors[idx])
        new_decomposed = self._decompose(child_obj, self.weight_vectors[idx])
        
        if new_decomposed < current_decomposed:
            # 替换
            self.population[idx] = child_vars
            self.objectives[idx] = child_obj
            
            # 更新理想点
            self.z = np.minimum(self.z, child_obj)
            
            return True
        
        return False
    
    def _update_neighbors(self, idx: int, child_obj: np.ndarray, 
                          child_vars: np.ndarray):
        """更新邻居"""
        for j in self.neighbors[idx][:self.neighborhood_size // 2]:
            current_decomposed = self._decompose(self.objectives[j], self.weight_vectors[j])
            new_decomposed = self._decompose(child_obj, self.weight_vectors[j])
            
            if new_decomposed < current_decomposed:
                self.population[j] = child_vars
                self.objectives[j] = child_obj
                self.z = np.minimum(self.z, child_obj)
    
    def optimize(self, evaluate_func: Callable,
                 n_generations: int = 200,
                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        运行MOEA/D优化
        
        参数:
            evaluate_func: 评估函数 f(x) -> [f1, f2, ...]
            n_generations: 迭代代数
            verbose: 是否打印进度
        
        返回:
            (最优解, Pareto前沿)
        """
        self.evaluate_func = evaluate_func
        
        # 初始化
        self._initialize_population()
        
        for gen in range(n_generations):
            for i in range(self.pop_size):
                # 选择交配伙伴
                mating_pool = self._mating_restriction(i, 2)
                
                if len(mating_pool) < 2:
                    continue
                
                # 交叉
                parent1 = self.population[i]
                parent2 = self.population[random.choice(mating_pool)]
                
                child_vars = self._crossover(parent1, parent2)
                child_vars = self._mutate(child_vars)
                
                # 评估
                child_obj = evaluate_func(child_vars)
                
                # 更新
                self._update_solution(i, child_obj, child_vars)
                
                # 更新邻居
                self._update_neighbors(i, child_obj, child_vars)
            
            if verbose and (gen + 1) % 20 == 0:
                # 打印当前最佳
                decomposed_values = [
                    self._decompose(self.objectives[i], self.weight_vectors[i])
                    for i in range(self.pop_size)
                ]
                best_idx = np.argmin(decomposed_values)
                print(f"Generation {gen + 1}: Best obj = {self.objectives[best_idx]}")
        
        return self.population, self.objectives


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("MOEA/D 基于分解的多目标优化测试")
    print("=" * 50)
    
    random.seed(42)
    np.random.seed(42)
    
    # ZDT1
    def zdt1(x):
        f1 = x[0]
        g = 1 + 9 * np.sum(x[1:]) / 9
        f2 = g * (1 - np.sqrt(x[0] / g))
        return np.array([f1, f2])
    
    # DTLZ1 (简化)
    def dtlz1(x, n_obj=3):
        g = 100 * (len(x) - n_obj + 1 + np.sum((x[n_obj-1:] - 0.5)**2 - np.cos(20 * np.pi * (x[n_obj-1:] - 0.5))))
        f = [(g + 1) * 0.5 * (1 + x[i]) for i in range(n_obj)]
        f[-1] *= np.prod([x[i] for i in range(n_obj - 1)])
        for i in range(1, n_obj - 1):
            f[i] *= np.prod([x[j] for j in range(n_obj - 1 - i)]) * (1 - x[n_obj - 1 - i])
        return np.array(f)
    
    print("\n--- ZDT1 问题 (Tchebychev分解) ---")
    moead = MOEAD(n_vars=10, n_objectives=2, pop_size=100, 
                  neighborhood_size=20, decomposition='te')
    pareto_vars, pareto_front = moead.optimize(zdt1, n_generations=200)
    
    print(f"Pareto前沿点数: {len(pareto_front)}")
    print(f"前5个解: {pareto_front[:5]}")
    
    print("\n--- ZDT1 问题 (PBI分解) ---")
    moead2 = MOEAD(n_vars=10, n_objectives=2, pop_size=100, decomposition='pbi')
    pareto_vars2, pareto_front2 = moead2.optimize(zdt1, n_generations=200)
    
    print(f"Pareto前沿点数: {len(pareto_front2)}")
    print(f"前5个解: {pareto_front2[:5]}")
    
    print("\n--- 三目标问题 (DTLZ1简化) ---")
    moead3 = MOEAD(n_vars=12, n_objectives=3, pop_size=105, decomposition='te')
    pareto_vars3, pareto_front3 = moead3.optimize(
        lambda x: dtlz1(x, n_obj=3), n_generations=150
    )
    
    print(f"Pareto前沿点数: {len(pareto_front3)}")
    print(f"前3个解: {pareto_front3[:3]}")
    
    print("\n" + "=" * 50)
    print("测试完成")
