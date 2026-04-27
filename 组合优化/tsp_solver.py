# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / tsp_solver

本文件实现 tsp_solver 相关的算法功能。
"""

import random
import math
import itertools
from typing import List, Tuple, Optional


class TSPSolver:
    """
    旅行商问题求解器
    """
    
    def __init__(self, coordinates: List[Tuple[float, float]]):
        """
        初始化求解器
        
        Args:
            coordinates: 城市坐标列表 [(x1,y1), (x2,y2), ...]
        """
        self.coords = coordinates
        self.n = len(coordinates)
        
        # 预计算距离矩阵
        self.dist = [[0.0] * self.n for _ in range(self.n)]
        for i in range(self.n):
            for j in range(i + 1, self.n):
                d = math.sqrt((coordinates[i][0] - coordinates[j][0])**2 + 
                            (coordinates[i][1] - coordinates[j][1])**2)
                self.dist[i][j] = d
                self.dist[j][i] = d
    
    def tour_length(self, tour: List[int]) -> float:
        """
        计算路径长度
        
        Args:
            tour: 路径(城市索引序列)
        
        Returns:
            总长度
        """
        length = 0.0
        for i in range(len(tour)):
            length += self.dist[tour[i]][tour[(i + 1) % len(tour)]]
        return length
    
    def nearest_neighbor(self, start: int = 0) -> Tuple[List[int], float]:
        """
        最近邻启发式算法
        
        Args:
            start: 起始城市索引
        
        Returns:
            (路径, 长度)
        """
        unvisited = set(range(self.n))
        tour = [start]
        unvisited.remove(start)
        
        while unvisited:
            current = tour[-1]
            nearest = min(unvisited, key=lambda x: self.dist[current][x])
            tour.append(nearest)
            unvisited.remove(nearest)
        
        return tour, self.tour_length(tour)
    
    def two_opt(self, tour: List[int], max_iterations: int = 1000) -> Tuple[List[int], float]:
        """
        2-opt局部搜索
        
        Args:
            tour: 初始路径
            max_iterations: 最大迭代次数
        
        Returns:
            (改进后的路径, 长度)
        """
        best_tour = tour[:]
        best_length = self.tour_length(best_tour)
        
        improved = True
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            for i in range(1, self.n - 1):
                for j in range(i + 1, self.n):
                    # 反转tour[i:j+1]
                    new_tour = best_tour[:i] + best_tour[i:j+1][::-1] + best_tour[j+1:]
                    new_length = self.tour_length(new_tour)
                    
                    if new_length < best_length:
                        best_tour = new_tour
                        best_length = new_length
                        improved = True
            
            # 如果一次遍历没有改进,停止
            if not improved:
                break
        
        return best_tour, best_length
    
    def or_opt(self, tour: List[int]) -> Tuple[List[int], float]:
        """
        Or-opt: 将连续的几个节点移动到其他位置
        
        Args:
            tour: 当前路径
        
        Returns:
            (改进后的路径, 长度)
        """
        best_tour = tour[:]
        best_length = self.tour_length(best_tour)
        
        improved = True
        while improved:
            improved = False
            
            for seg_len in [1, 2, 3]:  # 段长度
                for i in range(1, self.n - seg_len):
                    segment = best_tour[i:i+seg_len]
                    remaining = best_tour[:i] + best_tour[i+seg_len:]
                    
                    for j in range(len(remaining)):
                        new_tour = remaining[:j] + segment + remaining[j:]
                        new_length = self.tour_length(new_tour)
                        
                        if new_length < best_length:
                            best_tour = new_tour
                            best_length = new_length
                            improved = True
                            break
                    
                    if improved:
                        break
                if improved:
                    break
        
        return best_tour, best_length
    
    def simulated_annealing(self, initial_temp: float = 1000,
                           cooling_rate: float = 0.995,
                           min_temp: float = 1,
                           max_iter_per_temp: int = 100) -> Tuple[List[int], float]:
        """
        模拟退火算法
        
        Args:
            initial_temp: 初始温度
            cooling_rate: 冷却率
            min_temp: 最低温度
            max_iter_per_temp: 每个温度下的最大迭代次数
        
        Returns:
            (路径, 长度)
        """
        # 初始解:最近邻
        current_tour, current_length = self.nearest_neighbor()
        
        # 先做一次2-opt预热
        current_tour, current_length = self.two_opt(current_tour, max_iterations=100)
        
        best_tour = current_tour[:]
        best_length = current_length
        
        temp = initial_temp
        
        while temp > min_temp:
            for _ in range(max_iter_per_temp):
                # 随机选择两种邻域操作之一
                if random.random() < 0.5:
                    # 2-opt:反转一段
                    i, j = sorted(random.sample(range(self.n), 2))
                    new_tour = current_tour[:i] + current_tour[i:j+1][::-1] + current_tour[j+1:]
                else:
                    # 2-change:交换两个节点
                    i, j = random.sample(range(self.n), 2)
                    new_tour = current_tour[:]
                    new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
                
                new_length = self.tour_length(new_tour)
                delta = new_length - current_length
                
                # 以概率接受差解
                if delta < 0 or random.random() < math.exp(-delta / temp):
                    current_tour = new_tour
                    current_length = new_length
                    
                    if current_length < best_length:
                        best_tour = current_tour[:]
                        best_length = current_length
            
            temp *= cooling_rate
        
        return best_tour, best_length
    
    def solve(self, method: str = 'hybrid', 
             start: int = 0) -> Tuple[List[int], float]:
        """
        主求解函数
        
        Args:
            method: 'nearest', '2opt', 'sa', 'hybrid'
            start: 起始城市
        
        Returns:
            (路径, 长度)
        """
        if method == 'nearest':
            return self.nearest_neighbor(start)
        
        elif method == '2opt':
            tour, length = self.nearest_neighbor(start)
            return self.two_opt(tour)
        
        elif method == 'sa':
            return self.simulated_annealing()
        
        else:  # hybrid
            # 先最近邻,再2-opt,最后or-opt
            tour, length = self.nearest_neighbor(start)
            tour, length = self.two_opt(tour)
            tour, length = self.or_opt(tour)
            return tour, length


def solve_tsp(coordinates: List[Tuple[float, float]], 
              method: str = 'hybrid') -> Tuple[List[int], float]:
    """
    TSP求解便捷函数
    
    Args:
        coordinates: 城市坐标
        method: 求解方法
    
    Returns:
        (路径, 长度)
    """
    solver = TSPSolver(coordinates)
    return solver.solve(method)


def solve_tsp_exact(num_cities: int = 10) -> Optional[Tuple[List[int], float]]:
    """
    精确求解TSP(枚举法,仅适用于小规模)
    
    Args:
        num_cities: 城市数量
    
    Returns:
        最优解
    """
    if num_cities > 10:
        print("城市数量太多,不适合枚举")
        return None
    
    # 随机生成城市
    coords = [(random.random(), random.random()) for _ in range(num_cities)]
    
    # 预计算距离
    dist = [[0.0] * num_cities for _ in range(num_cities)]
    for i in range(num_cities):
        for j in range(i + 1, num_cities):
            d = math.sqrt((coords[i][0] - coords[j][0])**2 + (coords[i][1] - coords[j][1])**2)
            dist[i][j] = d
            dist[j][i] = d
    
    best_tour = None
    best_length = float('inf')
    
    # 枚举所有排列(固定0为起点)
    for perm in itertools.permutations(range(1, num_cities)):
        tour = [0] + list(perm)
        length = sum(dist[tour[i]][tour[(i+1) % num_cities]] for i in range(num_cities))
        
        if length < best_length:
            best_length = length
            best_tour = tour
    
    return best_tour, best_length


# 测试代码
if __name__ == "__main__":
    random.seed(42)
    
    # 测试1: 简单TSP
    print("测试1 - 简单TSP(10城市):")
    coords = [(random.random(), random.random()) for _ in range(10)]
    
    solver = TSPSolver(coords)
    
    # 最近邻
    tour_nn, len_nn = solver.nearest_neighbor()
    print(f"  最近邻: 长度={len_nn:.4f}")
    
    # 2-opt
    tour_2opt, len_2opt = solver.two_opt(tour_nn)
    print(f"  2-opt: 长度={len_2opt:.4f}")
    
    # 模拟退火
    tour_sa, len_sa = solver.simulated_annealing()
    print(f"  模拟退火: 长度={len_sa:.4f}")
    
    # 混合方法
    tour_hybrid, len_hybrid = solver.solve('hybrid')
    print(f"  混合方法: 长度={len_hybrid:.4f}")
    
    # 测试2: 精确解对比(小规模)
    print("\n测试2 - 精确解对比(6城市):")
    exact_tour, exact_len = solve_tsp_exact(6)
    print(f"  精确解: 长度={exact_len:.4f}, 路径={exact_tour}")
    
    solver2 = TSPSolver(coords[:6])
    hybrid_tour, hybrid_len = solver2.solve('hybrid')
    print(f"  混合方法: 长度={hybrid_len:.4f}")
    
    # 测试3: 不同算法的改进效果
    print("\n测试3 - 算法比较(20城市):")
    coords20 = [(random.random(), random.random()) for _ in range(20)]
    solver20 = TSPSolver(coords20)
    
    tour, length = solver20.nearest_neighbor()
    print(f"  最近邻: {length:.4f}")
    
    tour, length = solver20.two_opt(tour)
    print(f"  2-opt后: {length:.4f}")
    
    tour, length = solver20.or_opt(tour)
    print(f"  or-opt后: {length:.4f}")
    
    # 测试4: 模拟退火参数影响
    print("\n测试4 - SA参数对比(15城市):")
    coords15 = [(random.random(), random.random()) for _ in range(15)]
    solver15 = TSPSolver(coords15)
    
    # 快冷却
    tour_fast, len_fast = solver15.simulated_annealing(initial_temp=500, cooling_rate=0.99, max_iter_per_temp=50)
    print(f"  快冷却: {len_fast:.4f}")
    
    # 慢冷却
    tour_slow, len_slow = solver15.simulated_annealing(initial_temp=1000, cooling_rate=0.999, max_iter_per_temp=200)
    print(f"  慢冷却: {len_slow:.4f}")
    
    print("\n所有测试完成!")
