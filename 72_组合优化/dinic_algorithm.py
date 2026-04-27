# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / dinic_algorithm



本文件实现 dinic_algorithm 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple

from collections import deque





class DinicSolver:

    """

    Dinic最大流算法实现

    """

    

    def __init__(self, num_vertices: int):

        """

        初始化

        

        Args:

            num_vertices: 顶点数

        """

        self.n = num_vertices

        # 邻接表: {u: [(v, cap, rev_idx), ...]}

        self.graph: Dict[int, List[Tuple[int, float, int]]] = {i: [] for i in range(num_vertices)}

        # 原始边容量

        self.original_capacity: Dict[Tuple[int, int], float] = {}

    

    def add_edge(self, u: int, v: int, capacity: float):

        """

        添加有向边

        

        Args:

            u: 起点

            v: 终点

            capacity: 容量

        """

        # 正向边

        self.graph[u].append([v, capacity, len(self.graph[v])])

        # 反向边(残余容量为0)

        self.graph[v].append([u, 0, len(self.graph[u]) - 1])

        

        # 记录原始容量

        self.original_capacity[(u, v)] = self.original_capacity.get((u, v), 0) + capacity

    

    def bfs(self, source: int, sink: int) -> bool:

        """

        BFS构建分层图

        

        Args:

            source: 源点

            sink: 汇点

        

        Returns:

            是否存在增广路径

        """

        self.level = {i: -1 for i in range(self.n)}

        self.level[source] = 0

        

        queue = deque([source])

        while queue:

            u = queue.popleft()

            for v, cap, rev in self.graph[u]:

                if cap > 0 and self.level[v] < 0:

                    self.level[v] = self.level[u] + 1

                    queue.append(v)

        

        return self.level[sink] >= 0

    

    def dfs(self, u: int, sink: int, flow: float) -> float:

        """

        DFS在分层图上查找阻塞流

        

        Args:

            u: 当前节点

            sink: 汇点

            flow: 当前路径最小容量

        

        Returns:

            实际发送的流量

        """

        if u == sink:

            return flow

        

        for i in range(self.it[u], len(self.graph[u])):

            v, cap, rev = self.graph[u][i]

            

            if cap > 0 and self.level[u] < self.level[v]:

                d = self.dfs(v, sink, min(flow, cap))

                

                if d > 0:

                    # 更新残余容量

                    self.graph[u][i][1] -= d

                    self.graph[v][rev][1] += d

                    return d

            

            self.it[u] += 1

        

        return 0

    

    def dinic(self, source: int, sink: int) -> float:

        """

        Dinic主算法

        

        Args:

            source: 源点

            sink: 汇点

        

        Returns:

            最大流值

        """

        max_flow = 0

        

        while self.bfs(source, sink):

            self.it = {i: 0 for i in range(self.n)}

            

            while True:

                f = self.dfs(source, sink, float('inf'))

                if f == 0:

                    break

                max_flow += f

        

        return max_flow

    

    def get_flow_value(self, edge: Tuple[int, int]) -> float:

        """获取某边的流量"""

        u, v = edge

        if (u, v) in self.original_capacity:

            # 通过查找反向边的容量来推断流量

            for v_node, cap, rev in self.graph[v]:

                if v_node == u:

                    return self.original_capacity[(u, v)] - cap

        return 0





def solve_max_flow_dinic(num_vertices: int, edges: List[Tuple[int, int, float]],

                        source: int, sink: int) -> float:

    """

    Dinic算法求解最大流

    

    Args:

        num_vertices: 顶点数

        edges: 边列表

        source: 源点

        sink: 汇点

    

    Returns:

        最大流值

    """

    solver = DinicSolver(num_vertices)

    for u, v, cap in edges:

        solver.add_edge(u, v, cap)

    return solver.dinic(source, sink)





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单网络

    print("测试1 - 简单网络:")

    solver = DinicSolver(6)

    # s(0) -> a(1):10, s(0)->b(2):10

    # a(1) -> t(5):5

    # b(2) -> a(1):2, b(2)->c(3):8

    # c(3) -> t(5):10

    # a(1) -> c(3):7

    

    solver.add_edge(0, 1, 10)

    solver.add_edge(0, 2, 10)

    solver.add_edge(1, 2, 2)

    solver.add_edge(1, 3, 7)

    solver.add_edge(1, 5, 5)

    solver.add_edge(2, 3, 8)

    solver.add_edge(3, 5, 10)

    

    max_flow = solver.dinic(0, 5)

    print(f"  最大流: {max_flow}")

    

    # 测试2: 便捷函数

    print("\n测试2 - 便捷函数:")

    edges = [(0, 1, 16), (0, 2, 13), (1, 2, 10), (1, 3, 12), 

             (2, 1, 4), (2, 4, 14), (3, 2, 9), (3, 5, 20), (4, 3, 7), (4, 5, 4)]

    max_flow2 = solve_max_flow_dinic(6, edges, 0, 5)

    print(f"  最大流: {max_flow2}")

    

    # 测试3: 大型网络

    print("\n测试3 - 较大网络:")

    import random

    random.seed(42)

    

    solver3 = DinicSolver(100)

    for _ in range(200):

        u = random.randint(0, 49)

        v = random.randint(50, 99)

        cap = random.randint(1, 100)

        solver3.add_edge(u, v, cap)

    

    # 源点连接左侧,汇点连接右侧

    for i in range(50):

        solver3.add_edge(0, i, 1000)

        solver3.add_edge(50 + i, 99, 1000)

    

    max_flow3 = solver3.dinic(0, 99)

    print(f"  最大流(100顶点,200边): {max_flow3}")

    

    # 测试4: 验证流量守恒

    print("\n测试4 - 验证流量守恒:")

    solver4 = DinicSolver(4)

    solver4.add_edge(0, 1, 10)

    solver4.add_edge(0, 2, 5)

    solver4.add_edge(1, 2, 5)

    solver4.add_edge(1, 3, 10)

    solver4.add_edge(2, 3, 10)

    

    max_flow4 = solver4.dinic(0, 3)

    print(f"  源点流出: {max_flow4}")

    

    # 验证中间节点

    for node in [1, 2]:

        inflow = sum(cap for v, cap, rev in solver4.graph if v == node)

        outflow = sum(edge[1] for edge in solver4.graph[node])

        print(f"  节点{node}: 入流={inflow}, 出流={outflow}")

    

    # 测试5: 与Edmonds-Karp比较

    print("\n测试5 - Dinic vs Edmonds-Karp:")

    

    # 重新实现Edmonds-Karp用于比较

    class EKSimple:

        def __init__(self, n):

            self.n = n

            self.graph = {i: {} for i in range(n)}

        

        def add_edge(self, u, v, cap):

            if v not in self.graph[u]:

                self.graph[u][v] = 0

            self.graph[u][v] += cap

            if u not in self.graph[v]:

                self.graph[v][u] = 0

        

        def bfs(self, s, t):

            parent = {}

            queue = deque([s])

            visited = {s}

            while queue:

                u = queue.popleft()

                for v in self.graph[u]:

                    if v not in visited and self.graph[u][v] > 0:

                        visited.add(v)

                        parent[v] = u

                        if v == t:

                            return parent

                        queue.append(v)

            return parent

        

        def max_flow(self, s, t):

            flow = 0

            while True:

                parent = self.bfs(s, t)

                if not parent or t not in parent:

                    break

                path = []

                v = t

                while v != s:

                    path.append(v)

                    v = parent[v]

                path.append(s)

                path.reverse()

                

                min_cap = min(self.graph[path[i]][path[i+1]] for i in range(len(path)-1))

                

                for i in range(len(path)-1):

                    u, v = path[i], path[i+1]

                    self.graph[u][v] -= min_cap

                    self.graph[v][u] += min_cap

                

                flow += min_cap

            return flow

    

    import time

    

    # 小型网络

    solver5_ek = EKSimple(50)

    solver5_dinic = DinicSolver(50)

    

    edges5 = []

    for _ in range(100):

        u = random.randint(0, 49)

        v = random.randint(0, 49)

        cap = random.randint(1, 50)

        edges5.append((u, v, cap))

        solver5_ek.add_edge(u, v, cap)

        solver5_dinic.add_edge(u, v, cap)

    

    # Edmonds-Karp

    start = time.time()

    flow_ek = solver5_ek.max_flow(0, 49)

    time_ek = time.time() - start

    

    # Dinic

    start = time.time()

    flow_dinic = solver5_dinic.dinic(0, 49)

    time_dinic = time.time() - start

    

    print(f"  Edmonds-Karp: 流={flow_ek}, 时间={time_ek:.4f}s")

    print(f"  Dinic: 流={flow_dinic}, 时间={time_dinic:.4f}s")

    

    print("\n所有测试完成!")

