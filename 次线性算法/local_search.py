# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / local_search

本文件实现 local_search 相关的算法功能。
"""

import numpy as np
import random
import math


def hill_climbing(objective_func, neighbor_func, initial_solution, max_iter=1000):
    """
    爬山算法 (Hill Climbing)
    
    每次移动到邻域中最好的邻居
    
    Parameters
    ----------
    objective_func : callable
        目标函数 (要最大化)
    neighbor_func : callable
        邻居生成函数 solution -> [neighbors]
    initial_solution : any
        初始解
    max_iter : int
        最大迭代次数
    
    Returns
    -------
    tuple
        (最优解, 最优值, 迭代历史)
    """
    current = initial_solution
    current_value = objective_func(current)
    
    history = [current_value]
    
    for iteration in range(max_iter):
        # 生成邻居
        neighbors = neighbor_func(current)
        
        if not neighbors:
            break
        
        # 找到最好的邻居
        best_neighbor = None
        best_value = current_value
        
        for neighbor in neighbors:
            value = objective_func(neighbor)
            if value > best_value:
                best_value = value
                best_neighbor = neighbor
        
        # 如果没有更好的邻居,停止
        if best_neighbor is None:
            break
        
        # 移动到更好的邻居
        current = best_neighbor
        current_value = best_value
        history.append(current_value)
    
    return current, current_value, history


def simulated_annealing(objective_func, neighbor_func, initial_solution, 
                        initial_temp=100, cooling_rate=0.995, min_temp=0.01, 
                        max_iter=1000):
    """
    模拟退火算法
    
    核心思想:
    - 以概率 exp(ΔE/T) 接受更差的解
    - 温度逐渐降低,接受更差解的概率减小
    - 理论上能找到全局最优
    
    Parameters
    ----------
    objective_func : callable
        目标函数 (要最大化)
    neighbor_func : callable
        邻居生成函数
    initial_solution : any
        初始解
    initial_temp : float
        初始温度
    cooling_rate : float
        冷却率,每次 T *= cooling_rate
    min_temp : float
        最低温度
    max_iter : int
        最大迭代次数
    
    Returns
    -------
    tuple
        (最优解, 最优值, 接受率)
    """
    current = initial_solution
    current_value = objective_func(current)
    
    best = current
    best_value = current_value
    
    temperature = initial_temp
    total_accepted = 0
    total_rejected = 0
    
    for iteration in range(max_iter):
        if temperature < min_temp:
            break
        
        # 生成邻居
        neighbors = neighbor_func(current)
        
        if not neighbors:
            break
        
        # 随机选择一个邻居
        neighbor = random.choice(neighbors)
        neighbor_value = objective_func(neighbor)
        
        # 计算差值 (我们要最大化)
        delta = neighbor_value - current_value
        
        # 接受准则
        if delta > 0:
            # 更好的解,总是接受
            current = neighbor
            current_value = neighbor_value
            total_accepted += 1
        else:
            # 更差的解,以概率接受
            prob = math.exp(delta / temperature)
            if random.random() < prob:
                current = neighbor
                current_value = neighbor_value
                total_accepted += 1
            else:
                total_rejected += 1
        
        # 更新最优
        if current_value > best_value:
            best = current
            best_value = current_value
        
        # 冷却
        temperature *= cooling_rate
    
    accept_rate = total_accepted / (total_accepted + total_rejected) if (total_accepted + total_rejected) > 0 else 0
    
    return best, best_value, {'accept_rate': accept_rate}


def randomized_local_search(objective_func, neighbor_func, initial_solution, max_iter=1000):
    """
    随机化局部搜索 (Randomized Local Search)
    
    随机选择一个邻居,如果是更好的则接受
    重复直到收敛
    
    Parameters
    ----------
    objective_func : callable
        目标函数
    neighbor_func : callable
        邻居生成函数
    initial_solution : any
        初始解
    max_iter : int
        最大迭代次数
    
    Returns
    -------
    tuple
        (最优解, 最优值, 改进次数)
    """
    current = initial_solution
    current_value = objective_func(current)
    
    best = current
    best_value = current_value
    
    improvements = 0
    
    for iteration in range(max_iter):
        neighbors = neighbor_func(current)
        
        if not neighbors:
            break
        
        # 随机选择一个邻居
        neighbor = random.choice(neighbors)
        neighbor_value = objective_func(neighbor)
        
        # 如果更好,移动
        if neighbor_value > current_value:
            current = neighbor
            current_value = neighbor_value
            improvements += 1
            
            # 更新最优
            if current_value > best_value:
                best = current
                best_value = current_value
    
    return best, best_value, {'improvements': improvements}


def metropolis_algorithm(objective_func, neighbor_func, initial_solution, 
                        temperature=1.0, max_iter=1000):
    """
    Metropolis 算法
    
    固定温度下的蒙特卡洛模拟
    用于估计系统状态分布
    
    Parameters
    ----------
    objective_func : callable
        目标函数 (能量函数,最小化)
    neighbor_func : callable
        邻居生成函数
    initial_solution : any
        初始解
    temperature : float
        温度参数
    max_iter : int
        最大迭代次数
    
    Returns
    -------
    tuple
        (解历史, 能量历史)
    """
    current = initial_solution
    current_energy = objective_func(current)
    
    solution_history = [current]
    energy_history = [current_energy]
    
    for iteration in range(max_iter):
        neighbors = neighbor_func(current)
        
        if not neighbors:
            break
        
        neighbor = random.choice(neighbors)
        neighbor_energy = objective_func(neighbor)
        
        delta = neighbor_energy - current_energy
        
        # 接受准则 (最小化能量)
        if delta < 0:
            current = neighbor
            current_energy = neighbor_energy
        else:
            prob = math.exp(-delta / temperature)
            if random.random() < prob:
                current = neighbor
                current_energy = neighbor_energy
        
        solution_history.append(current)
        energy_history.append(current_energy)
    
    return solution_history, energy_history


def iterative_improvement_max_3sat(clauses, num_vars, max_flips=1000):
    """
    MAX-3SAT 的迭代改进算法
    
    目标: 最大化满足的字句数
    
    Parameters
    ----------
    clauses : list
        字句列表,每个字句是文字列表
    num_vars : int
        变量数量
    max_flips : int
        最大翻转次数
    
    Returns
    -------
    tuple
        (赋值, 满足的字句数)
    """
    def evaluate(assignment):
        """计算满足的字句数"""
        satisfied = 0
        for clause in clauses:
            clause_satisfied = any(
                (literal > 0 and assignment[literal - 1]) or 
                (literal < 0 and not assignment[-literal - 1])
                for literal in clause
            )
            if clause_satisfied:
                satisfied += 1
        return satisfied
    
    # 随机初始化赋值
    assignment = [random.choice([True, False]) for _ in range(num_vars)]
    current_satisfied = evaluate(assignment)
    
    for _ in range(max_flips):
        # 找到翻转后改善最大的变量
        best_var = -1
        best_improvement = 0
        
        for i in range(num_vars):
            # 翻转变量 i
            assignment[i] = not assignment[i]
            new_satisfied = evaluate(assignment)
            improvement = new_satisfied - current_satisfied
            
            if improvement > best_improvement:
                best_improvement = improvement
                best_var = i
            
            # 恢复
            assignment[i] = not assignment[i]
        
        # 如果有改善,翻转
        if best_var >= 0 and best_improvement > 0:
            assignment[best_var] = not assignment[best_var]
            current_satisfied += best_improvement
        else:
            # 局部最优
            break
    
    return assignment, current_satisfied


def vertex_cover_local_search(graph, initial_cover=None, max_iter=1000):
    """
    顶点覆盖的局部搜索
    
    目标: 最小化覆盖大小
    
    Parameters
    ----------
    graph : dict
        图的邻接表
    initial_cover : set
        初始覆盖,如果没有则用贪心生成
    max_iter : int
        最大迭代次数
    
    Returns
    -------
    tuple
        (最小覆盖, 覆盖大小)
    """
    vertices = list(graph.keys())
    
    if initial_cover is None:
        # 贪心初始化
        cover = set()
        edges_remaining = set()
        for u in graph:
            for v in graph[u]:
                if u < v:
                    edges_remaining.add((u, v))
        
        while edges_remaining:
            # 找到度数最高的边
            best_edge = max(edges_remaining, 
                          key=lambda e: sum(1 for other in edges_remaining if e[0] in other or e[1] in other))
            cover.add(best_edge[0])
            cover.add(best_edge[1])
            
            # 删除被覆盖的边
            edges_remaining = {e for e in edges_remaining if e[0] not in cover or e[1] not in cover}
    else:
        cover = set(initial_cover)
    
    def is_valid_cover(c):
        """检查是否是有效覆盖"""
        for u in graph:
            for v in graph[u]:
                if u < v and u not in c and v not in c:
                    return False
        return True
    
    def get_neighbors(c):
        """生成邻居: 删除一个顶点或添加一个顶点"""
        neighbors = []
        
        # 删除操作
        for v in c:
            neighbor = c - {v}
            if is_valid_cover(neighbor):
                neighbors.append(neighbor)
        
        # 添加操作 (如果当前不是有效覆盖)
        if not is_valid_cover(c):
            for v in vertices:
                if v not in c:
                    neighbors.append(c | {v})
        
        return neighbors
    
    # 局部搜索
    current_cover = cover
    current_size = len(current_cover)
    
    for iteration in range(max_iter):
        neighbors = get_neighbors(current_cover)
        
        if not neighbors:
            break
        
        # 找到最小的邻居
        best_neighbor = None
        best_size = current_size
        
        for neighbor in neighbors:
            if len(neighbor) < best_size:
                best_size = len(neighbor)
                best_neighbor = neighbor
        
        if best_neighbor is None:
            break
        
        current_cover = best_neighbor
        current_size = best_size
    
    return current_cover, current_size


def two_opt_tsp(cost_matrix, initial_tour=None, max_iter=1000):
    """
    2-opt 局部搜索求解 TSP
    
    每次反转路径中的一段,减少总成本
    
    Parameters
    ----------
    cost_matrix : np.ndarray
        成本矩阵
    initial_tour : list
        初始回路
    max_iter : int
        最大迭代次数
    
    Returns
    -------
    tuple
        (最优回路, 总成本)
    """
    n = len(cost_matrix)
    
    if initial_tour is None:
        # 贪心初始化
        tour = list(range(n))
        random.shuffle(tour)
    else:
        tour = list(initial_tour)
    
    def tour_cost(t):
        """计算回路成本"""
        cost = 0
        for i in range(len(t) - 1):
            cost += cost_matrix[t[i]][t[i + 1]]
        cost += cost_matrix[t[-1]][t[0]]  # 回到起点
        return cost
    
    current_cost = tour_cost(tour)
    
    for iteration in range(max_iter):
        improved = False
        
        for i in range(n - 1):
            for j in range(i + 2, n):
                # 反转 i+1 到 j 之间的边
                new_tour = tour[:i + 1] + tour[i + 1:j + 1][::-1] + tour[j + 1:]
                new_cost = tour_cost(new_tour)
                
                if new_cost < current_cost:
                    tour = new_tour
                    current_cost = new_cost
                    improved = True
                    break
            
            if improved:
                break
        
        if not improved:
            break
    
    return tour, current_cost


def compute_tour_cost(tour, points):
    """
    计算 TSP 回路的成本 (欧几里得距离)
    
    Parameters
    ----------
    tour : list
        访问顺序
    points : list
        点坐标列表
    
    Returns
    -------
    float
        总成本
    """
    n = len(points)
    cost = 0
    
    for i in range(len(tour) - 1):
        p1 = points[tour[i]]
        p2 = points[tour[i + 1]]
        cost += np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
    
    # 回到起点
    p1 = points[tour[-1]]
    p2 = points[tour[0]]
    cost += np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
    
    return cost


if __name__ == "__main__":
    # 测试: 局部搜索算法
    
    print("=" * 60)
    print("局部搜索算法测试")
    print("=" * 60)
    
    random.seed(42)
    np.random.seed(42)
    
    # 测试爬山算法
    print("\n--- 爬山算法 ---")
    
    # 简单函数优化: f(x) = -x^2 + 噪声
    def simple_objective(x):
        return -x ** 2 + random.uniform(-0.1, 0.1)
    
    def simple_neighbor(x):
        return [x + random.uniform(-1, 1) for _ in range(5)]
    
    best_x, best_val, history = hill_climbing(
        simple_objective, simple_neighbor, initial_solution=5.0, max_iter=100
    )
    
    print(f"初始解: 5.0")
    print(f"最优解: {best_x:.4f}")
    print(f"最优值: {best_val:.4f}")
    print(f"迭代次数: {len(history)}")
    
    # 测试模拟退火
    print("\n--- 模拟退火 ---")
    
    best_x_sa, best_val_sa, stats = simulated_annealing(
        simple_objective, simple_neighbor, initial_solution=5.0,
        initial_temp=10, cooling_rate=0.98, max_iter=200
    )
    
    print(f"最优解: {best_x_sa:.4f}")
    print(f"最优值: {best_val_sa:.4f}")
    print(f"接受率: {stats['accept_rate']:.4f}")
    
    # 测试 TSP 2-opt
    print("\n--- TSP 2-opt 局部搜索 ---")
    
    n_points = 10
    points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n_points)]
    
    # 计算成本矩阵
    cost_matrix = np.zeros((n_points, n_points))
    for i in range(n_points):
        for j in range(n_points):
            cost_matrix[i][j] = np.sqrt(
                (points[i][0] - points[j][0]) ** 2 + 
                (points[i][1] - points[j][1]) ** 2
            )
    
    best_tour, best_cost = two_opt_tsp(cost_matrix, max_iter=100)
    
    print(f"城市数: {n_points}")
    print(f"最优回路: {best_tour}")
    print(f"总成本: {best_cost:.2f}")
    
    # 验证
    verify_cost = compute_tour_cost(best_tour, points)
    print(f"验证成本: {verify_cost:.2f}")
    
    # 测试顶点覆盖局部搜索
    print("\n--- 顶点覆盖局部搜索 ---")
    
    test_graph = {
        0: [1, 2],
        1: [0, 2, 3],
        2: [0, 1, 3],
        3: [1, 2, 4],
        4: [3, 5],
        5: [4]
    }
    
    cover, size = vertex_cover_local_search(test_graph, max_iter=100)
    
    print(f"最小覆盖: {cover}")
    print(f"覆盖大小: {size}")
    
    # 验证覆盖
    covered = set()
    for v in cover:
        for nb in test_graph[v]:
            covered.add((min(v, nb), max(v, nb)))
    
    all_edges = set()
    for v in test_graph:
        for nb in test_graph[v]:
            if v < nb:
                all_edges.add((v, nb))
    
    print(f"完全覆盖: {covered == all_edges}")
    
    # 测试 MAX-3SAT
    print("\n--- MAX-3SAT 局部搜索 ---")
    
    # 生成随机 3-SAT 实例
    num_vars = 20
    num_clauses = 50
    
    clauses = []
    for _ in range(num_clauses):
        clause = []
        for _ in range(3):
            var = random.randint(1, num_vars)
            sign = 1 if random.random() < 0.5 else -1
            clause.append(sign * var)
        clauses.append(clause)
    
    assignment, satisfied = iterative_improvement_max_3sat(clauses, num_vars, max_flips=500)
    
    print(f"变量数: {num_vars}")
    print(f"字句数: {num_clauses}")
    print(f"满足的字句: {satisfied}/{num_clauses}")
    print(f"满足比例: {satisfied / num_clauses:.2f}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
