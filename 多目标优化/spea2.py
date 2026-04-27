# -*- coding: utf-8 -*-
"""
算法实现：多目标优化 / spea2

本文件实现 spea2 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Callable, Optional
import random


class SPEA2:
    """
    SPEA2算法
    
    参数:
        n_vars: 决策变量维度
        n_objectives: 目标数量
        pop_size: 种群大小
        archive_size: 档案大小
        crossover_prob: 交叉概率
        mutation_prob: 变异概率
        bounds: 变量边界
    """
    
    def __init__(self, n_vars: int, n_objectives: int,
                 pop_size: int = 100,
                 archive_size: Optional[int] = None,
                 crossover_prob: float = 0.9,
                 mutation_prob: float = 0.1,
                 eta: float = 20.0,
                 bounds: Tuple[float, float] = (0, 1)):
        self.n_vars = n_vars
        self.n_objectives = n_objectives
        self.pop_size = pop_size
        self.archive_size = archive_size or pop_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.eta = eta
        self.bounds = bounds
        
        # 档案（帕累托最优解集合）
        self.archive = []
        self.archive_objectives = []
        
        # 算法参数
        self.evaluate_func = None
    
    def _initialize_population(self) -> List[np.ndarray]:
        """初始化种群"""
        return [np.random.uniform(self.bounds[0], self.bounds[1], self.n_vars) 
                for _ in range(self.pop_size)]
    
    def _evaluate(self, population: List[np.ndarray]) -> List[np.ndarray]:
        """评估种群"""
        return [np.array(self.evaluate_func(ind)) for ind in population]
    
    def _dominance(self, obj1: np.ndarray, obj2: np.ndarray) -> bool:
        """判断obj1是否支配obj2（最小化）"""
        return np.all(obj1 <= obj2) and np.any(obj1 < obj2)
    
    def _calculate_strength(self, combined_objectives: List[np.ndarray]) -> np.ndarray:
        """
        计算强度值
        
        强度：解i支配的解数量 / (群体大小 + 1)
        """
        n = len(combined_objectives)
        strength = np.zeros(n)
        
        for i in range(n):
            for j in range(n):
                if i != j and self._dominance(combined_objectives[i], combined_objectives[j]):
                    strength[i] += 1
        
        strength = strength / (n + 1)
        
        return strength
    
    def _calculate_fitness(self, objectives: List[np.ndarray], 
                          strength: np.ndarray, 
                          indices: List[int]) -> np.ndarray:
        """
        计算适应度
        
        fitness(i) = S(i) + sum_{j支配i} S(j)
        """
        n = len(indices)
        fitness = np.zeros(n)
        
        for i, idx_i in enumerate(indices):
            for j, idx_j in enumerate(indices):
                if i != j and self._dominance(objectives[idx_j], objectives[idx_i]):
                    fitness[i] += strength[idx_j]
        
        fitness += strength[indices]
        
        return fitness
    
    def _density_estimation(self, objectives: np.ndarray) -> np.ndarray:
        """
        密度估计（网格方法）
        
        返回每个解的密度估计值（越小越不拥挤）
        """
        n = len(objectives)
        
        if n <= 1:
            return np.zeros(n)
        
        # 找到边界
        f_min = np.min(objectives, axis=0)
        f_max = np.max(objectives, axis=0)
        
        # 划分网格
        n_bins = int(np.sqrt(n / 2))  # 经验值
        
        densities = np.zeros(n)
        
        for i in range(n):
            # 计算该点周围网格中的点数
            grid_count = 0
            for j in range(n):
                in_grid = True
                for m in range(self.n_objectives):
                    # 归一化坐标
                    if f_max[m] - f_min[m] > 1e-10:
                        coord_i = (objectives[i, m] - f_min[m]) / (f_max[m] - f_min[m])
                        coord_j = (objectives[j, m] - f_min[m]) / (f_max[m] - f_min[m])
                        
                        bin_width = 1.0 / n_bins
                        if abs(coord_i - coord_j) > bin_width:
                            in_grid = False
                            break
                
                if in_grid:
                    grid_count += 1
            
            # 密度 = 1 / (2 + grid_count)
            densities[i] = 1.0 / (2 + grid_count)
        
        return densities
    
    def _environmental_selection(self, combined_pop: List[np.ndarray],
                                 combined_obj: List[np.ndarray]) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """环境选择：从组合中选择下一代档案"""
        n_combined = len(combined_pop)
        
        # 计算强度
        strength = self._calculate_strength(combined_obj)
        
        # 计算适应度
        all_indices = list(range(n_combined))
        fitness = self._calculate_fitness(combined_obj, strength, all_indices)
        
        # 非支配解
        non_dominated = []
        for i, obj in enumerate(combined_obj):
            is_dominated = False
            for j, obj2 in enumerate(combined_obj):
                if i != j and self._dominance(obj2, obj):
                    is_dominated = True
                    break
            if not is_dominated:
                non_dominated.append(i)
        
        # 分类
        if len(non_dominated) > self.archive_size:
            # 需要从非支配解中选出
            new_archive_obj = [combined_obj[i] for i in non_dominated]
            new_archive_pop = [combined_pop[i] for i in non_dominated]
            
            # 使用聚类
            new_archive, new_obj = self._truncation(new_archive_pop, new_archive_obj, self.archive_size)
        elif len(non_dominated) < self.archive_size:
            # 需要添加被支配的解
            new_archive = [combined_pop[i] for i in non_dominated]
            new_obj = [combined_obj[i] for i in non_dominated]
            
            # 按适应度排序，添加更多解
            fitness_sorted = [(fitness[i], i) for i in range(n_combined) if i not in non_dominated]
            fitness_sorted.sort()
            
            remaining = self.archive_size - len(new_archive)
            for _, idx in fitness_sorted[:remaining]:
                new_archive.append(combined_pop[idx])
                new_obj.append(combined_obj[idx])
        else:
            new_archive = [combined_pop[i] for i in non_dominated]
            new_obj = [combined_obj[i] for i in non_dominated]
        
        return new_archive, new_obj
    
    def _truncation(self, archive: List[np.ndarray], 
                   archive_obj: List[np.ndarray],
                   target_size: int) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        聚类截断：当非支配解超过档案大小时使用
        
        基于欧氏距离的聚类
        """
        if len(archive) <= target_size:
            return archive, archive_obj
        
        n = len(archive)
        to_remove = n - target_size
        
        while to_remove > 0:
            # 找到最近的两个解
            min_dist = np.inf
            remove_idx = -1
            
            for i in range(n):
                for j in range(i + 1, n):
                    dist = np.linalg.norm(np.array(archive_obj[i]) - np.array(archive_obj[j]))
                    if dist < min_dist:
                        min_dist = dist
                        remove_idx = i
            
            # 移除
            archive.pop(remove_idx)
            archive_obj.pop(remove_idx)
            to_remove -= 1
        
        return archive, archive_obj
    
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
    
    def optimize(self, evaluate_func: Callable,
                 n_generations: int = 200,
                 verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        运行SPEA2优化
        """
        self.evaluate_func = evaluate_func
        
        # 初始化种群
        population = self._initialize_population()
        objectives = self._evaluate(population)
        
        # 初始化档案
        self.archive = population.copy()
        self.archive_objectives = objectives.copy()
        
        for gen in range(n_generations):
            # 合并种群和档案
            combined_pop = population + self.archive
            combined_obj = objectives + self.archive_objectives
            
            # 环境选择
            self.archive, self.archive_objectives = self._environmental_selection(
                combined_pop, combined_obj
            )
            
            # 创建子代
            mating_pool = random.sample(range(len(self.archive)), self.pop_size)
            offspring = []
            
            for i in range(0, self.pop_size, 2):
                parent1 = self.archive[mating_pool[i % len(mating_pool)]]
                parent2 = self.archive[mating_pool[(i + 1) % len(mating_pool)]]
                
                child1 = self._mutate(self._crossover(parent1, parent2))
                child2 = self._mutate(self._crossover(parent2, parent1))
                
                offspring.append(child1)
                offspring.append(child2)
            
            population = offspring[:self.pop_size]
            objectives = self._evaluate(population)
            
            if verbose and (gen + 1) % 20 == 0:
                best_idx = np.argmin([np.sum(obj) for obj in self.archive_objectives])
                print(f"Generation {gen + 1}: Best obj = {self.archive_objectives[best_idx]}")
        
        return np.array(self.archive), np.array(self.archive_objectives)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("SPEA2 强度帕累托进化算法测试")
    print("=" * 50)
    
    random.seed(42)
    np.random.seed(42)
    
    # ZDT1
    def zdt1(x):
        f1 = x[0]
        g = 1 + 9 * np.sum(x[1:]) / 9
        f2 = g * (1 - np.sqrt(x[0] / g))
        return [f1, f2]
    
    # ZDT2
    def zdt2(x):
        f1 = x[0]
        g = 1 + 9 * np.sum(x[1:]) / 9
        f2 = g * (1 - (x[0] / g) ** 2)
        return [f1, f2]
    
    print("\n--- ZDT1 问题 ---")
    spea2 = SPEA2(n_vars=10, n_objectives=2, pop_size=100, archive_size=100)
    pareto_vars, pareto_front = spea2.optimize(zdt1, n_generations=200)
    
    print(f"档案大小: {len(pareto_front)}")
    print(f"前5个解: {pareto_front[:5]}")
    
    print("\n--- ZDT2 问题 ---")
    spea2_2 = SPEA2(n_vars=10, n_objectives=2, pop_size=100)
    pareto_vars2, pareto_front2 = spea2_2.optimize(zdt2, n_generations=200)
    
    print(f"档案大小: {len(pareto_front2)}")
    print(f"前5个解: {pareto_front2[:5]}")
    
    # 验证帕累托性质
    print("\n--- 帕累托验证 ---")
    from pareto_front import is_non_dominated
    
    is_pareto = is_non_dominated(pareto_front)
    print(f"所有解都是非支配的: {np.all(is_pareto)}")
    
    print("\n" + "=" * 50)
    print("测试完成")
