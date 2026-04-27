# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / bipartite_matching

本文件实现 bipartite_matching 相关的算法功能。
"""

from typing import List, Dict, Optional, Set, Tuple
from collections import deque


class BipartiteMatchingSolver:
    """
    二分图匹配求解器
    """
    
    def __init__(self, left_size: int, right_size: int):
        """
        初始化
        
        Args:
            left_size: 左侧顶点数
            right_size: 右侧顶点数
        """
        self.n_left = left_size
        self.n_right = right_size
        # 邻接表: 左侧顶点i -> 右侧邻居列表
        self.graph: List[List[int]] = [[] for _ in range(left_size)]
    
    def add_edge(self, left: int, right: int):
        """添加边(从左侧到右侧)"""
        if 0 <= left < self.n_left and 0 <= right < self.n_right:
            self.graph[left].append(right)
    
    def bipartite_matching(self) -> Tuple[int, Dict[int, int]]:
        """
        朴素的最大匹配(DFS增广路径)
        
        Returns:
            (匹配数, 匹配字典 {左侧:右侧})
        """
        match_to_right = [-1] * self.n_right  # 右侧匹配到的左侧顶点
        result = {}
        
        def dfs(u: int, visited: Set[int]) -> bool:
            for v in self.graph[u]:
                if v not in visited:
                    visited.add(v)
                    if match_to_right[v] == -1 or dfs(match_to_right[v], visited):
                        match_to_right[v] = u
                        return True
            return False
        
        matches = 0
        for u in range(self.n_left):
            if dfs(u, set()):
                matches += 1
        
        # 构建结果字典
        for v, u in enumerate(match_to_right):
            if u != -1:
                result[u] = v
        
        return matches, result
    
    def hopcroft_karp(self) -> Tuple[int, Dict[int, int]]:
        """
        Hopcroft-Karp算法: O(E√V)
        
        Returns:
            (匹配数, 匹配字典)
        """
        # 左侧匹配到的右侧顶点
        match_to_right = [-1] * self.n_right
        # 右侧匹配到的左侧顶点
        match_to_left = [-1] * self.n_left
        # 距离
        dist = [0] * self.n_left
        
        INF = float('inf')
        
        def bfs() -> bool:
            queue = deque()
            
            # 初始化:所有左侧未匹配顶点距离为0
            for u in range(self.n_left):
                if match_to_left[u] == -1:
                    dist[u] = 0
                    queue.append(u)
                else:
                    dist[u] = INF
            
            # 虚拟源点距离
            dist_null = INF
            
            while queue:
                u = queue.popleft()
                
                if dist[u] < dist_null:
                    for v in self.graph[u]:
                        # 右侧顶点v匹配到的左侧顶点
                        if match_to_right[v] != -1:
                            # 下一层
                            if dist[match_to_right[v]] == INF:
                                dist[match_to_right[v]] = dist[u] + 1
                                queue.append(match_to_right[v])
                        else:
                            # 找到增广路径
                            dist_null = dist[u] + 1
            
            return dist_null != INF
        
        def dfs(u: int) -> bool:
            for v in self.graph[u]:
                # 如果右侧未匹配或沿着增广路径
                if match_to_right[v] == -1 or (dist[match_to_right[v]] == dist[u] + 1 and dfs(match_to_right[v])):
                    match_to_right[v] = u
                    match_to_left[u] = v
                    return True
            dist[u] = INF
            return False
        
        matching = 0
        
        while bfs():
            for u in range(self.n_left):
                if match_to_left[u] == -1:
                    if dfs(u):
                        matching += 1
        
        # 构建结果
        result = {}
        for v, u in enumerate(match_to_right):
            if u != -1:
                result[u] = v
        
        return matching, result
    
    def maximum_weighted_matching(self, weights: List[List[float]]) -> Dict[int, int]:
        """
        最大权匹配(使用匈牙利算法)
        注意:这里简化处理,假设是完美匹配
        
        Args:
            weights: 权重矩阵 [left][right]
        
        Returns:
            匹配字典
        """
        n = max(self.n_left, self.n_right)
        
        # 扩展为方阵
        cost = [[0.0] * n for _ in range(n)]
        for i in range(self.n_left):
            for j in range(self.n_right):
                cost[i][j] = -weights[i][j]  # 转为最小化
        
        # 匈牙利算法(简化版)
        u = [0] * (n + 1)
        v = [0] * (n + 1)
        p = [0] * (n + 1)
        way = [0] * (n + 1)
        
        for i in range(1, n + 1):
            p[0] = i
            j0 = 0
            minv = [float('inf')] * (n + 1)
            used = [False] * (n + 1)
            
            while p[j0] != 0:
                used[j0] = True
                i0 = p[j0]
                delta = float('inf')
                j1 = 0
                
                for j in range(1, n + 1):
                    if not used[j]:
                        cur = cost[i0-1][j-1] - u[i0] - v[j]
                        if cur < minv[j]:
                            minv[j] = cur
                            way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j
                
                for j in range(n + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta
                
                j0 = j1
            
            while j0 != 0:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
        
        result = {}
        for j in range(1, n + 1):
            if p[j] != 0 and p[j] <= self.n_left and j <= self.n_right:
                result[p[j] - 1] = j - 1
        
        return result


def solve_bipartite_matching(left_size: int, right_size: int,
                             edges: List[Tuple[int, int]],
                             method: str = 'hk') -> Tuple[int, Dict[int, int]]:
    """
    二分图匹配便捷函数
    
    Args:
        left_size: 左侧顶点数
        right_size: 右侧顶点数
        edges: 边列表
        method: 'naive', 'hk'
    
    Returns:
        (匹配数, 匹配字典)
    """
    solver = BipartiteMatchingSolver(left_size, right_size)
    for u, v in edges:
        solver.add_edge(u, v)
    
    if method == 'naive':
        return solver.bipartite_matching()
    else:
        return solver.hopcroft_karp()


# 测试代码
if __name__ == "__main__":
    import random
    random.seed(42)
    
    # 测试1: 简单二分图
    print("测试1 - 简单二分图:")
    # 左侧: A,B,C,D (0,1,2,3)
    # 右侧: 1,2,3,4 (0,1,2,3)
    # 边: A-1, A-2, B-2, C-3, D-1, D-4
    
    edges1 = [(0, 0), (0, 1), (1, 1), (2, 2), (3, 0), (3, 3)]
    
    solver1 = BipartiteMatchingSolver(4, 4)
    for u, v in edges1:
        solver1.add_edge(u, v)
    
    match1, result1 = solver1.hopcroft_karp()
    print(f"  边: {edges1}")
    print(f"  最大匹配: {match1}")
    print(f"  匹配: {result1}")
    
    # 测试2: 另一例
    print("\n测试2 - 另一例:")
    edges2 = [(0, 0), (0, 2), (1, 1), (1, 2), (2, 2), (3, 3)]
    
    solver2 = BipartiteMatchingSolver(4, 4)
    for u, v in edges2:
        solver2.add_edge(u, v)
    
    match2, result2 = solver2.hopcroft_karp()
    print(f"  边: {edges2}")
    print(f"  最大匹配: {match2}")
    print(f"  匹配: {result2}")
    
    # 测试3: 不平衡的二分图
    print("\n测试3 - 不平衡二分图:")
    edges3 = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (3, 0), (3, 1)]
    
    solver3 = BipartiteMatchingSolver(4, 3)
    for u, v in edges3:
        solver3.add_edge(u, v)
    
    match3, result3 = solver3.hopcroft_karp()
    print(f"  左侧4个,右侧3个")
    print(f"  最大匹配: {match3}")
    
    # 测试4: 大规模随机图
    print("\n测试4 - 大规模随机图(100vs100):")
    n = 100
    solver4 = BipartiteMatchingSolver(n, n)
    
    edges4 = []
    for u in range(n):
        for _ in range(random.randint(1, 10)):
            v = random.randint(0, n - 1)
            edges4.append((u, v))
            solver4.add_edge(u, v)
    
    import time
    
    # Hopcroft-Karp
    start = time.time()
    match4_hk, _ = solver4.hopcroft_karp()
    time_hk = time.time() - start
    
    # 朴素
    solver4_naive = BipartiteMatchingSolver(n, n)
    for u, v in edges4:
        solver4_naive.add_edge(u, v)
    
    start = time.time()
    match4_naive, _ = solver4_naive.bipartite_matching()
    time_naive = time.time() - start
    
    print(f"  HK匹配数: {match4_hk}, 时间: {time_hk:.4f}s")
    print(f"  朴素匹配数: {match4_naive}, 时间: {time_naive:.4f}s")
    
    # 测试5: 最大权匹配
    print("\n测试5 - 最大权匹配:")
    weights = [
        [3, 5, 2, 4],  # A
        [2, 8, 1, 3],  # B
        [6, 4, 2, 5],  # C
        [1, 5, 3, 2],  # D
    ]
    
    solver5 = BipartiteMatchingSolver(4, 4)
    for i in range(4):
        for j in range(4):
            if weights[i][j] > 0:
                solver5.add_edge(i, j)
    
    result5 = solver5.maximum_weighted_matching(weights)
    print(f"  权重矩阵:")
    for row in weights:
        print(f"    {row}")
    print(f"  最大权匹配: {result5}")
    
    # 计算总权重
    total_weight = sum(weights[u][v] for u, v in result5.items())
    print(f"  总权重: {total_weight}")
    
    print("\n所有测试完成!")
