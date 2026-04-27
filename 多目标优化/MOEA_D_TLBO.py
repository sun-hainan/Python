# -*- coding: utf-8 -*-
"""
算法实现：多目标优化 / MOEA_D_TLBO

本文件实现 MOEA_D_TLBO 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Callable
import random


class MOEADTLBO:
    """
    MOEA/D结合TLBO算法
    
    MOEA/D提供分解框架
    TLBO增强局部搜索能力
    """
    
    def __init__(self, n_vars: int, n_objectives: int,
                 pop_size: int = 100,
                 neighborhood_size: int = 20,
                 bounds: Tuple[float, float] = (0, 1)):
        self.n_vars = n_vars
        self.n_objectives = n_objectives
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
        
        # 参考点
        self.z = np.zeros(n_objectives)
        
        # 参数
        self.Tf = 2.0  # 教学因子
        self.crossover_prob = 0.9
        self.mutation_prob = 0.1
        self.eta = 20.0
        
        self.evaluate_func = None
    
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
        
        self.z = np.min(self.objectives, axis=0)
    
    def _teaching_phase(self, idx: int) -> np.ndarray:
        """
        教学阶段：教师影响学生
        
        参数:
            idx: 学生索引
        
        返回:
            新解
        """
        # 找当前子问题的教师（权重向量最近的可行解）
        teacher_idx = idx
        min_dist = np.inf
        
        for i in range(self.pop_size):
            if self.objectives[i] is None:
                continue
            dist = np.linalg.norm(self.objectives[i] - self.z)
            if dist < min_dist:
                min_dist = dist
                teacher_idx = i
        
        teacher = self.population[teacher_idx]
        student = self.population[idx].copy()
        
        # 计算均值
        mean_solution = np.mean(self.population, axis=0)
        
        # 教学：学生向教师学习
        for j in range(self.n_vars):
            diff = teacher[j] - mean_solution[j]
            r = random.random()
            
            # 新解
            new_val = student[j] + r * diff
            
            # 评估是否改进
            if self._decompose(self.evaluate_func(student), self.weight_vectors[idx]) > \
               self._decompose(self.evaluate_func(student), self.weight_vectors[idx]):
                student[j] = new_val
        
        return np.clip(student, self.bounds[0], self.bounds[1])
    
    def _learning_phase(self, idx: int) -> np.ndarray:
        """
        学习阶段：学生相互学习
        
        参数:
            idx: 学生索引
        
        返回:
            新解
        """
        student = self.population[idx].copy()
        
        # 随机选择学习伙伴
        neighbors = self.neighbors[idx]
        if len(neighbors) < 2:
            return student
        
        # 选择邻居中的一个进行学习
        partner_idx = random.choice(neighbors)
        partner = self.population[partner_idx]
        
        student_obj = self.evaluate_func(student)
        partner_obj = self.evaluate_func(partner)
        
        # 向更好的解学习
        if self._decompose(partner_obj, self.weight_vectors[idx]) < \
           self._decompose(student_obj, self.weight_vectors[idx]):
            r = random.random()
            new_solution = student + r * (partner - student)
        else:
            r = random.random()
            new_solution = student + r * (student - partner)
        
        return np.clip(new_solution, self.bounds[0], self.bounds[1])
    
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
                         child_vars: np.ndarray):
        """更新解"""
        current_decomposed = self._decompose(self.objectives[idx], self.weight_vectors[idx])
        new_decomposed = self._decompose(child_obj, self.weight_vectors[idx])
        
        if new_decomposed < current_decomposed:
            self.population[idx] = child_vars
            self.objectives[idx] = child_obj
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
        运行MOEA/D-TLBO优化
        """
        self.evaluate_func = evaluate_func
        self._initialize()
        
        for gen in range(n_generations):
            # 每个解都进行TLBO学习
            for i in range(self.pop_size):
                # 教学阶段
                if random.random() < 0.5:
                    child_vars = self._teaching_phase(i)
                else:
                    # 学习阶段
                    child_vars = self._learning_phase(i)
                
                # 交叉变异
                neighbors = self.neighbors[i]
                if len(neighbors) >= 2:
                    idx1, idx2 = random.sample(neighbors, 2)
                    parent2 = self.population[idx1] if random.random() < 0.5 else self.population[idx2]
                    child_vars = self._crossover(self.population[i], parent2)
                
                child_vars = self._mutate(child_vars)
                
                # 评估
                child_obj = evaluate_func(child_vars)
                
                # 更新
                self._update_solution(i, child_obj, child_vars)
                self._update_neighbors(i, child_obj, child_vars)
            
            if verbose and (gen + 1) % 20 == 0:
                decomposed_values = [
                    self._decompose(self.objectives[i], self.weight_vectors[i])
                    for i in range(self.pop_size)
                ]
                best_idx = np.argmin(decomposed_values)
                print(f"Generation {gen + 1}: Best obj = {self.objectives[best_idx]}")
        
        return self.population, self.objectives


class TLBOEnhancer:
    """
    TLBO增强器：用于增强现有MOEA/D种群
    """
    
    def __init__(self, n_vars: int, n_objectives: int, Tf: float = 2.0):
        self.n_vars = n_vars
        self.n_objectives = n_objectives
        self.Tf = Tf
    
    def enhance(self, population: np.ndarray, objectives: np.ndarray,
                evaluate_func: Callable) -> Tuple[np.ndarray, np.ndarray]:
        """
        增强种群
        
        参数:
            population: 当前种群
            objectives: 当前目标值
            evaluate_func: 评估函数
        
        返回:
            增强后的种群和目标值
        """
        n = len(population)
        enhanced_pop = population.copy()
        enhanced_obj = objectives.copy()
        
        for i in range(n):
            # 教学
            teacher_idx = np.argmin(objectives)
            teacher = population[teacher_idx]
            
            mean_solution = np.mean(population, axis=0)
            
            # 生成教学后的解
            new_solution = population[i].copy()
            for j in range(self.n_vars):
                r = random.random()
                diff = teacher[j] - self.Tf * mean_solution[j]
                new_solution[j] = population[i][j] + r * diff
            
            # 评估
            new_obj = evaluate_func(new_solution)
            
            if np.sum(new_obj) < np.sum(objectives[i]):
                enhanced_pop[i] = new_solution
                enhanced_obj[i] = new_obj
            
            # 学习（从邻居）
            if len(population) > 1:
                other_idx = random.choice([k for k in range(n) if k != i])
                other = population[other_idx]
                other_obj = objectives[other_idx]
                
                learn_solution = enhanced_pop[i].copy()
                r = random.random()
                
                if np.sum(other_obj) < np.sum(enhanced_obj[i]):
                    learn_solution = enhanced_pop[i] + r * (other - enhanced_pop[i])
                else:
                    learn_solution = enhanced_pop[i] + r * (enhanced_pop[i] - other)
                
                learn_obj = evaluate_func(learn_solution)
                
                if np.sum(learn_obj) < np.sum(enhanced_obj[i]):
                    enhanced_pop[i] = learn_solution
                    enhanced_obj[i] = learn_obj
        
        return enhanced_pop, enhanced_obj


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("MOEA/D-TLBO 测试")
    print("=" * 50)
    
    random.seed(42)
    np.random.seed(42)
    
    # ZDT1
    def zdt1(x):
        f1 = x[0]
        g = 1 + 9 * np.sum(x[1:]) / 9
        f2 = g * (1 - np.sqrt(x[0] / g))
        return np.array([f1, f2])
    
    print("\n--- MOEA/D-TLBO ZDT1 问题 ---")
    moead_tlbo = MOEADTLBO(n_vars=10, n_objectives=2, pop_size=100,
                          neighborhood_size=20)
    pareto_vars, pareto_front = moead_tlbo.optimize(zdt1, n_generations=200)
    
    print(f"Pareto前沿点数: {len(pareto_front)}")
    print(f"前5个解:\n{pareto_front[:5]}")
    
    print("\n--- TLBO增强器测试 ---")
    enhancer = TLBOEnhancer(n_vars=10, n_objectives=2)
    
    initial_pop = np.random.uniform(0, 1, (50, 10))
    initial_obj = np.array([zdt1(x) for x in initial_pop])
    
    enhanced_pop, enhanced_obj = enhancer.enhance(initial_pop, initial_obj, zdt1)
    
    print(f"增强前目标范围: [{np.min(initial_obj):.4f}, {np.max(initial_obj):.4f}]")
    print(f"增强后目标范围: [{np.min(enhanced_obj):.4f}, {np.max(enhanced_obj):.4f}]")
    
    print("\n" + "=" * 50)
    print("测试完成")
