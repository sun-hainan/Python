# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / swarming_algorithm

本文件实现 swarming_algorithm 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict


class Ant:
    """蚂蚁个体"""
    
    def __init__(self, ant_id, start_node):
        # ant_id: 蚂蚁ID
        # start_node: 起始节点
        self.ant_id = ant_id
        self.current_node = start_node
        self.visited_nodes = [start_node]
        self.total_distance = 0.0
    
    def move_to(self, next_node, distance):
        """移动到下一节点"""
        self.visited_nodes.append(next_node)
        self.total_distance += distance
        self.current_node = next_node
    
    def has_visited(self, node):
        """检查是否访问过节点"""
        return node in self.visited_nodes
    
    def get_path(self):
        """获取完整路径"""
        return self.visited_nodes.copy()
    
    def reset(self, start_node):
        """重置蚂蚁状态"""
        self.current_node = start_node
        self.visited_nodes = [start_node]
        self.total_distance = 0.0


class AntColonyOptimization:
    """蚁群优化算法(ACO)用于TSP问题
    
    参数:
    - n_ants: 蚂蚁数量
    - n_iterations: 迭代次数
    - alpha: 信息素重要程度
    - beta: 启发式信息重要程度
    - evaporation: 信息素挥发率
    - pheromone_deposit: 信息素沉积量
    """
    
    def __init__(self, n_ants=20, n_iterations=100, alpha=1.0, beta=2.0, 
                 evaporation=0.5, pheromone_deposit=1.0):
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.alpha = alpha  # 信息素权重
        self.beta = beta    # 启发式权重
        self.evaporation = evaporation
        self.pheromone_deposit = pheromone_deposit
        
        # 图结构
        self.n_nodes = 0
        self.distance_matrix = None
        self.heuristic_matrix = None  # 启发式信息（距离的倒数）
        self.pheromone_matrix = None
        
        # 最优解记录
        self.best_path = None
        self.best_distance = float('inf')
        self.convergence_history = []
    
    def set_problem(self, distance_matrix):
        """
        设置问题（距离矩阵）
        distance_matrix: n x n 距离矩阵
        """
        self.n_nodes = len(distance_matrix)
        self.distance_matrix = np.array(distance_matrix)
        
        # 启发式矩阵：距离的倒数（越近概率越高）
        with np.errstate(divide='ignore'):
            self.heuristic_matrix = 1.0 / self.distance_matrix
            self.heuristic_matrix[np.isinf(self.heuristic_matrix)] = 0
        
        # 初始化信息素矩阵
        self.pheromone_matrix = np.ones((self.n_nodes, self.n_nodes))
        
        # 对角线设为0
        np.fill_diagonal(self.pheromone_matrix, 0)
    
    def _select_next_node(self, ant):
        """选择下一节点（轮盘赌选择）"""
        current = ant.current_node
        
        # 计算转移概率
        probabilities = []
        for j in range(self.n_nodes):
            if ant.has_visited(j):
                probabilities.append(0)
            else:
                # P_ij = tau_ij^alpha * eta_ij^beta / sum(tau_ik^alpha * eta_ik^beta)
                tau = self.pheromone_matrix[current, j] ** self.alpha
                eta = self.heuristic_matrix[current, j] ** self.beta
                probabilities.append(tau * eta)
        
        # 归一化
        total = sum(probabilities)
        if total == 0:
            # 如果所有概率都是0，随机选择
            unvisited = [j for j in range(self.n_nodes) if not ant.has_visited(j)]
            return np.random.choice(unvisited) if unvisited else -1
        
        probabilities = [p / total for p in probabilities]
        
        # 轮盘赌选择
        return np.random.choice(self.n_nodes, p=probabilities)
    
    def _construct_solution(self, ant):
        """构建完整路径"""
        while len(ant.visited_nodes) < self.n_nodes:
            next_node = self._select_next_node(ant)
            if next_node == -1:
                break
            
            distance = self.distance_matrix[ant.current_node, next_node]
            ant.move_to(next_node, distance)
        
        # 返回起点形成完整回路
        return_distance = self.distance_matrix[ant.current_node, ant.visited_nodes[0]]
        ant.total_distance += return_distance
    
    def _update_pheromone(self, ants):
        """更新信息素"""
        # 挥发
        self.pheromone_matrix *= (1 - self.evaporation)
        
        # 沉积
        for ant in ants:
            path = ant.get_path()
            pheromone_amount = self.pheromone_deposit / ant.total_distance
            
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                self.pheromone_matrix[u, v] += pheromone_amount
                self.pheromone_matrix[v, u] += pheromone_amount
    
    def solve(self, distance_matrix, start_node=0, verbose=True):
        """求解TSP"""
        self.set_problem(distance_matrix)
        
        if verbose:
            print("\n===== 蚁群优化算法求解TSP =====")
            print(f"  蚂蚁数量: {self.n_ants}")
            print(f"  迭代次数: {self.n_iterations}")
        
        # 初始化蚂蚁
        ants = [Ant(i, start_node) for i in range(self.n_ants)]
        
        for iteration in range(self.n_iterations):
            # 每个蚂蚁构建解
            for ant in ants:
                ant.reset(start_node)
                self._construct_solution(ant)
            
            # 更新信息素
            self._update_pheromone(ants)
            
            # 记录最优解
            for ant in ants:
                if ant.total_distance < self.best_distance:
                    self.best_distance = ant.total_distance
                    self.best_path = ant.get_path()
            
            self.convergence_history.append(self.best_distance)
            
            if verbose and iteration % 20 == 0:
                print(f"  迭代 {iteration}: 最优距离={self.best_distance:.4f}")
        
        return self.best_path, self.best_distance


class Particle:
    """粒子（PSO中的个体）"""
    
    def __init__(self, dim, bounds):
        # dim: 维度
        # bounds: 变量边界 [(min, max), ...]
        self.dim = dim
        self.bounds = bounds
        
        # 位置和速度
        self.position = np.random.uniform(
            [b[0] for b in bounds],
            [b[1] for b in bounds]
        )
        self.velocity = np.random.uniform(-0.1, 0.1, dim)
        
        # 个体最优
        self.pbest_position = self.position.copy()
        self.pbest_fitness = float('inf')
    
    def evaluate(self, objective_func):
        """评估适应度"""
        fitness = objective_func(self.position)
        
        if fitness < self.pbest_fitness:
            self.pbest_fitness = fitness
            self.pbest_position = self.position.copy()
        
        return fitness
    
    def update_velocity(self, gbest_position, w=0.7, c1=1.5, c2=1.5):
        """更新速度"""
        r1, r2 = np.random.random(self.dim), np.random.random(self.dim)
        
        cognitive = c1 * r1 * (self.pbest_position - self.position)
        social = c2 * r2 * (gbest_position - self.position)
        
        self.velocity = w * self.velocity + cognitive + social
    
    def update_position(self):
        """更新位置"""
        self.position += self.velocity
        
        # 边界约束
        for i in range(self.dim):
            low, high = self.bounds[i]
            self.position[i] = np.clip(self.position[i], low, high)


class ParticleSwarmOptimization:
    """粒子群优化算法(PSO)"""
    
    def __init__(self, n_particles=30, n_iterations=100):
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        
        self.particles = []
        self.gbest_position = None
        self.gbest_fitness = float('inf')
        self.convergence_history = []
    
    def set_objective(self, objective_func, dim, bounds):
        """设置目标函数和搜索空间"""
        self.objective_func = objective_func
        self.dim = dim
        self.bounds = bounds
        
        # 初始化粒子群
        self.particles = [
            Particle(dim, bounds) 
            for _ in range(self.n_particles)
        ]
        
        self.gbest_position = self.particles[0].position.copy()
        self.gbest_fitness = float('inf')
    
    def step(self):
        """单步迭代"""
        # 评估所有粒子
        for particle in self.particles:
            fitness = particle.evaluate(self.objective_func)
            
            if fitness < self.gbest_fitness:
                self.gbest_fitness = fitness
                self.gbest_position = particle.position.copy()
        
        # 更新所有粒子
        for particle in self.particles:
            particle.update_velocity(self.gbest_position)
            particle.update_position()
        
        self.convergence_history.append(self.gbest_fitness)
    
    def solve(self, objective_func, dim, bounds, verbose=True):
        """求解"""
        self.set_objective(objective_func, dim, bounds)
        
        if verbose:
            print("\n===== 粒子群优化算法(PSO) =====")
            print(f"  粒子数量: {self.n_particles}")
            print(f"  迭代次数: {self.n_iterations}")
            print(f"  搜索维度: {dim}")
        
        for iteration in range(self.n_iterations):
            self.step()
            
            if verbose and iteration % 20 == 0:
                print(f"  迭代 {iteration}: 最优适应度={self.gbest_fitness:.6f}")
        
        return self.gbest_position, self.gbest_fitness


class BacterialForaging:
    """细菌觅食优化算法(BFO)"""
    
    def __init__(self, n_bacteria=30, n_iterations=100):
        self.n_bacteria = n_bacteria
        self.n_iterations = n_iterations
        
        self.bacteria = []
        self.best_position = None
        self.best_fitness = float('inf')
    
    def set_objective(self, objective_func, dim, bounds):
        """设置目标函数"""
        self.objective_func = objective_func
        self.dim = dim
        self.bounds = bounds
        
        self.bacteria = [
            np.random.uniform(bounds[i][0], bounds[i][1], dim)
            for _ in range(self.n_bacteria)
        ]
    
    def elimination_dispersal(self, probability=0.25):
        """ elimination-dispersal 步骤"""
        for i in range(self.n_bacteria):
            if np.random.random() < probability:
                # 随机重新放置
                self.bacteria[i] = np.random.uniform(
                    [b[0] for b in self.bounds],
                    [b[1] for b in self.bounds]
                )
    
    def solve(self, objective_func, dim, bounds, verbose=True):
        """求解"""
        self.set_objective(objective_func, dim, bounds)
        
        if verbose:
            print("\n===== 细菌觅食优化算法(BFO) =====")
            print(f"  细菌数量: {self.n_bacteria}")
            print(f"  迭代次数: {self.n_iterations}")
        
        for iteration in range(self.n_iterations):
            # 评估
            fitnesses = [self.objective_func(b) for b in self.bacteria]
            
            # 记录最优
            min_idx = np.argmin(fitnesses)
            if fitnesses[min_idx] < self.best_fitness:
                self.best_fitness = fitnesses[min_idx]
                self.best_position = self.bacteria[min_idx].copy()
            
            # 趋向（向最优移动）
            for i in range(self.n_bacteria):
                direction = self.best_position - self.bacteria[i]
                step_size = 0.5 / (1 + iteration * 0.1)
                self.bacteria[i] += step_size * direction + np.random.randn(dim) * 0.1
                
                # 边界约束
                self.bacteria[i] = np.clip(self.bacteria[i], 
                                          [b[0] for b in bounds],
                                          [b[1] for b in bounds])
            
            if iteration % 20 == 0 and verbose:
                print(f"  迭代 {iteration}: 最优适应度={self.best_fitness:.6f}")
        
        return self.best_position, self.best_fitness


class FireflyAlgorithm:
    """萤火虫算法(FA)"""
    
    def __init__(self, n_fireflies=30, n_iterations=100, alpha=0.5, beta0=1.0, gamma=1.0):
        self.n_fireflies = n_fireflies
        self.n_iterations = n_iterations
        self.alpha = alpha  # 随机化参数
        self.beta0 = beta0  # 最大吸引度
        self.gamma = gamma  # 光吸收系数
        
        self.fireflies = []
        self.best_position = None
        self.best_fitness = float('inf')
    
    def set_objective(self, objective_func, dim, bounds):
        """设置目标函数"""
        self.objective_func = objective_func
        self.dim = dim
        self.bounds = bounds
        
        self.fireflies = [
            np.random.uniform(bounds[i][0], bounds[i][1], dim)
            for _ in range(self.n_fireflies)
        ]
    
    def attractiveness(self, distance):
        """吸引度函数"""
        return self.beta0 * np.exp(-self.gamma * distance ** 2)
    
    def step(self):
        """单步迭代"""
        # 评估
        fitnesses = [self.objective_func(f) for f in self.fireflies]
        
        # 更新最优
        min_idx = np.argmin(fitnesses)
        if fitnesses[min_idx] < self.best_fitness:
            self.best_fitness = fitnesses[min_idx]
            self.best_position = self.fireflies[min_idx].copy()
        
        # 移动萤火虫
        for i in range(self.n_fireflies):
            for j in range(self.n_fireflies):
                if fitnesses[j] < fitnesses[i]:  # j比i更亮
                    distance = np.linalg.norm(self.fireflies[j] - self.fireflies[i])
                    beta = self.attractiveness(distance)
                    
                    # 向更亮的萤火虫移动
                    self.fireflies[i] += beta * (self.fireflies[j] - self.fireflies[i])
                    self.fireflies[i] += self.alpha * (np.random.randn(self.dim) - 0.5)
                    
                    # 边界约束
                    self.fireflies[i] = np.clip(self.fireflies[i],
                                                [b[0] for b in self.bounds],
                                                [b[1] for b in self.bounds])
    
    def solve(self, objective_func, dim, bounds, verbose=True):
        """求解"""
        self.set_objective(objective_func, dim, bounds)
        
        if verbose:
            print("\n===== 萤火虫算法(FA) =====")
            print(f"  萤火虫数量: {self.n_fireflies}")
            print(f"  迭代次数: {self.n_iterations}")
        
        for iteration in range(self.n_iterations):
            self.step()
            
            if verbose and iteration % 20 == 0:
                print(f"  迭代 {iteration}: 最优适应度={self.best_fitness:.6f}")
        
        return self.best_position, self.best_fitness


if __name__ == "__main__":
    # 测试群体智能算法
    print("=" * 50)
    print("群体智能算法测试")
    print("=" * 50)
    
    # 测试1: 蚁群优化求解TSP
    print("\n--- 蚁群优化(ACO) TSP测试 ---")
    
    # 创建简单的TSP实例
    n_cities = 10
    np.random.seed(42)
    distance_matrix = np.random.randint(1, 100, (n_cities, n_cities))
    np.fill_diagonal(distance_matrix, 0)
    distance_matrix = (distance_matrix + distance_matrix.T) / 2  # 对称
    
    print(f"  城市数量: {n_cities}")
    
    aco = AntColonyOptimization(n_ants=15, n_iterations=100, alpha=1.0, beta=2.0)
    path, distance = aco.solve(distance_matrix, start_node=0)
    
    print(f"  最优路径: {path}")
    print(f"  最优距离: {distance:.2f}")
    
    # 测试2: 粒子群优化
    print("\n--- 粒子群优化(PSO)测试 ---")
    
    def rastrigin(x):
        """Rastrigin函数（测试函数）"""
        n = len(x)
        return 10 * n + sum(x_i**2 - 10 * np.cos(2 * np.pi * x_i) for x_i in x)
    
    dim = 5
    bounds = [(-5.12, 5.12) for _ in range(dim)]
    
    pso = ParticleSwarmOptimization(n_particles=30, n_iterations=100)
    best_pos, best_fitness = pso.solve(rastrigin, dim, bounds)
    
    print(f"  搜索维度: {dim}")
    print(f"  最优解: {[f'{x:.4f}' for x in best_pos]}")
    print(f"  最优适应度: {best_fitness:.6f}")
    
    # 测试3: 细菌觅食优化
    print("\n--- 细菌觅食优化(BFO)测试 ---")
    
    bfo = BacterialForaging(n_bacteria=20, n_iterations=80)
    best_pos_bfo, best_fitness_bfo = bfo.solve(rastrigin, dim, bounds)
    
    print(f"  最优适应度: {best_fitness_bfo:.6f}")
    
    # 测试4: 萤火虫算法
    print("\n--- 萤火虫算法(FA)测试 ---")
    
    fa = FireflyAlgorithm(n_fireflies=20, n_iterations=80)
    best_pos_fa, best_fitness_fa = fa.solve(rastrigin, dim, bounds)
    
    print(f"  最优适应度: {best_fitness_fa:.6f}")
    
    print("\n✓ 群体智能算法测试完成")
