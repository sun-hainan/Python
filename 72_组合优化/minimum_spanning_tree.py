# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / minimum_spanning_tree



本文件实现 minimum_spanning_tree 相关的算法功能。

"""



from typing import List, Tuple, Optional, Set

import heapq





class MinimumSpanningTreeSolver:

    """

    最小生成树求解器

    """

    

    def __init__(self, num_vertices: int):

        """

        初始化

        

        Args:

            num_vertices: 顶点数

        """

        self.n = num_vertices

        # 邻接表: {u: [(v, weight), ...]}

        self.graph: List[List[Tuple[int, float]]] = [[] for _ in range(num_vertices)]

    

    def add_edge(self, u: int, v: int, weight: float):

        """添加无向边"""

        self.graph[u].append((v, weight))

        self.graph[v].append((u, weight))

    

    def prim(self) -> Tuple[List[Tuple[int, int]], float]:

        """

        Prim算法:从一个顶点开始,逐步扩展

        

        Returns:

            (边列表 [(u,v), ...], 总权重)

        """

        in_mst = [False] * self.n

        min_edge = [(0, 0, -1)] * self.n  # (weight, to, from)

        

        # 从顶点0开始

        min_edge[0] = (0, 0, -1)

        

        total_weight = 0.0

        mst_edges = []

        

        for _ in range(self.n):

            # 找最小边

            min_w = float('inf')

            v = -1

            

            for i in range(self.n):

                if not in_mst[i] and min_edge[i][0] < min_w:

                    min_w = min_edge[i][0]

                    v = i

            

            if v == -1:

                break

            

            in_mst[v] = True

            total_weight += min_w

            

            if min_edge[v][2] != -1:

                mst_edges.append((min_edge[v][2], v))

            

            # 更新相邻顶点的最小边

            for neighbor, weight in self.graph[v]:

                if not in_mst[neighbor] and weight < min_edge[neighbor][0]:

                    min_edge[neighbor] = (weight, neighbor, v)

        

        return mst_edges, total_weight

    

    def prim_heap(self) -> Tuple[List[Tuple[int, int]], float]:

        """

        Prim算法(使用堆优化)

        

        Returns:

            (边列表, 总权重)

        """

        in_mst = [False] * self.n

        # (weight, to, from)

        heap = [(0, 0, -1)]

        

        total_weight = 0.0

        mst_edges = []

        

        while heap:

            w, v, parent = heapq.heappop(heap)

            

            if in_mst[v]:

                continue

            

            in_mst[v] = True

            total_weight += w

            

            if parent != -1:

                mst_edges.append((parent, v))

            

            for neighbor, weight in self.graph[v]:

                if not in_mst[neighbor]:

                    heapq.heappush(heap, (weight, neighbor, v))

        

        return mst_edges, total_weight

    

    def kruskal(self) -> Tuple[List[Tuple[int, int]], float]:

        """

        Kruskal算法:按权重从小到大选边

        

        Returns:

            (边列表, 总权重)

        """

        # 收集所有边

        edges = []

        for u in range(self.n):

            for v, w in self.graph[u]:

                if u < v:  # 避免重复

                    edges.append((w, u, v))

        

        # 按权重排序

        edges.sort()

        

        # 并查集

        parent = list(range(self.n))

        rank = [0] * self.n

        

        def find(x):

            if parent[x] != x:

                parent[x] = find(parent[x])

            return parent[x]

        

        def union(x, y):

            px, py = find(x), find(y)

            if px == py:

                return False

            if rank[px] < rank[py]:

                px, py = py, px

            parent[py] = px

            if rank[px] == rank[py]:

                rank[px] += 1

            return True

        

        mst_edges = []

        total_weight = 0.0

        

        for w, u, v in edges:

            if union(u, v):

                mst_edges.append((u, v))

                total_weight += w

                

                if len(mst_edges) == self.n - 1:

                    break

        

        return mst_edges, total_weight





def solve_mst(num_vertices: int, edges: List[Tuple[int, int, float]],

             method: str = 'kruskal') -> Tuple[List[Tuple[int, int]], float]:

    """

    MST求解便捷函数

    

    Args:

        num_vertices: 顶点数

        edges: 边列表 (u, v, weight)

        method: 'prim', 'kruskal'

    

    Returns:

        (MST边列表, 总权重)

    """

    solver = MinimumSpanningTreeSolver(num_vertices)

    for u, v, w in edges:

        solver.add_edge(u, v, w)

    

    if method == 'prim':

        return solver.prim()

    else:

        return solver.kruskal()





# 测试代码

if __name__ == "__main__":

    import random

    random.seed(42)

    

    # 测试1: 简单图

    print("测试1 - 简单图:")

    solver1 = MinimumSpanningTreeSolver(6)

    

    #    0 --1-- 1

    #    |  \   |

    #   4   2   5

    #    |    \ |

    #    2 --3-- 3

    #    |

    #    4 --3-- 5

    

    edges1 = [

        (0, 1, 1), (0, 2, 4), (0, 3, 2),

        (1, 3, 5), (1, 5, 4),

        (2, 3, 3), (2, 4, 3),

        (3, 5, 2), (4, 5, 1)

    ]

    

    for u, v, w in edges1:

        solver1.add_edge(u, v, w)

    

    mst_k, weight_k = solver1.kruskal()

    mst_p, weight_p = solver1.prim()

    

    print(f"  Kruskal: 边={mst_k}, 权重={weight_k}")

    print(f"  Prim: 边={mst_p}, 权重={weight_p}")

    

    # 验证

    print(f"  边数验证: Kruskal={len(mst_k)}, Prim={len(mst_p)} (应为{6-1})")

    

    # 测试2: 随机图

    print("\n测试2 - 随机图(20顶点):")

    n = 20

    solver2 = MinimumSpanningTreeSolver(n)

    

    edges2 = []

    for i in range(n):

        for j in range(i + 1, n):

            if random.random() > 0.7:

                w = random.uniform(1, 100)

                edges2.append((i, j, w))

                solver2.add_edge(i, j, w)

    

    mst2, weight2 = solver2.kruskal()

    print(f"  边数: {len(mst2)}")

    print(f"  总权重: {weight2:.2f}")

    

    # 验证MST性质

    print(f"  验证: 边数={len(mst2)}={n-1}")

    

    # 测试3: 算法比较

    print("\n测试3 - Kruskal vs Prim:")

    import time

    

    for n in [100, 200, 500]:

        solver = MinimumSpanningTreeSolver(n)

        edges = []

        for i in range(n):

            for j in range(i + 1, n):

                if random.random() > 0.9:

                    w = random.uniform(1, 100)

                    edges.append((i, j, w))

                    solver.add_edge(i, j, w)

        

        # Kruskal

        start = time.time()

        mst_k, w_k = solver.kruskal()

        time_k = time.time() - start

        

        # Prim (使用新的solver避免边重复)

        solver3 = MinimumSpanningTreeSolver(n)

        for u, v, w in edges:

            solver3.add_edge(u, v, w)

        

        start = time.time()

        mst_p, w_p = solver3.prim_heap()

        time_p = time.time() - start

        

        print(f"  n={n}, |E|={len(edges)}: Kruskal={time_k:.4f}s, Prim={time_p:.4f}s")

    

    # 测试4: 完全图

    print("\n测试4 - 完全图(n=50):")

    solver4 = MinimumSpanningTreeSolver(50)

    

    edges4 = []

    for i in range(50):

        for j in range(i + 1, 50):

            w = random.uniform(1, 100)

            edges4.append((i, j, w))

            solver4.add_edge(i, j, w)

    

    mst4, weight4 = solver4.kruskal()

    print(f"  MST权重: {weight4:.2f}")

    

    print("\n所有测试完成!")

