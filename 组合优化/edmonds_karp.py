# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / edmonds_karp



本文件实现 edmonds_karp 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional

from collections import deque





class MaxFlowSolver:

    """

    最大流求解器

    使用Edmonds-Karp算法求解网络最大流问题

    """

    

    def __init__(self, num_vertices: int):

        """

        初始化求解器

        

        Args:

            num_vertices: 顶点数

        """

        self.n = num_vertices

        # 邻接表存储残余网络: {u: {v: capacity}}

        self.graph: Dict[int, Dict[int, float]] = {i: {} for i in range(num_vertices)}

        # 原始边容量(用于追溯边)

        self.original_capacity: Dict[Tuple[int, int], float] = {}

    

    def add_edge(self, u: int, v: int, capacity: float):

        """

        添加有向边

        

        Args:

            u: 起点

            v: 终点

            capacity: 容量

        """

        if v not in self.graph[u]:

            self.graph[u][v] = 0

        self.graph[u][v] += capacity

        self.original_capacity[(u, v)] = self.original_capacity.get((u, v), 0) + capacity

        

        # 添加反向边(残余网络需要)

        if u not in self.graph[v]:

            self.graph[v][u] = 0

    

    def bfs(self, source: int, sink: int) -> Tuple[bool, Dict[int, int], float]:

        """

        BFS查找增广路径

        

        Args:

            source: 源点

            sink: 汇点

        

        Returns:

            (是否找到路径, 父节点字典, 路径最小容量)

        """

        parent = {source: None}

        visited = {source}

        queue = deque([source])

        

        # 记录到每个节点的最小残余容量

        min_cap = {source: float('inf')}

        

        while queue:

            u = queue.popleft()

            

            for v in self.graph[u]:

                if v not in visited and self.graph[u][v] > 0:

                    visited.add(v)

                    parent[v] = u

                    min_cap[v] = min(min_cap[u], self.graph[u][v])

                    

                    if v == sink:

                        return True, parent, min_cap[v]

                    

                    queue.append(v)

        

        return False, parent, 0

    

    def edmonds_karp(self, source: int, sink: int) -> float:

        """

        Edmonds-Karp算法求解最大流

        

        Args:

            source: 源点

            sink: 汇点

        

        Returns:

            最大流值

        """

        max_flow = 0

        iteration = 0

        

        while True:

            iteration += 1

            found, parent, path_cap = self.bfs(source, sink)

            

            if not found:

                break

            

            # 更新残余网络

            v = sink

            while parent[v] is not None:

                u = parent[v]

                # 正向边减少容量

                self.graph[u][v] -= path_cap

                # 反向边增加容量

                self.graph[v][u] += path_cap

                v = u

            

            max_flow += path_cap

            print(f"  迭代{iteration}: 增加流={path_cap}, 总流={max_flow}")

        

        return max_flow

    

    def get_flow_value(self, edge: Tuple[int, int]) -> float:

        """获取某条边的当前流量"""

        u, v = edge

        if edge in self.original_capacity:

            return self.original_capacity[edge] - self.graph[u].get(v, 0)

        return 0

    

    def get_min_cut(self, source: int) -> Set[int]:

        """

        获取最小 cut 的 S 侧

        

        Args:

            source: 源点

        

        Returns:

            能从源点到达的顶点集合

        """

        visited = {source}

        queue = deque([source])

        

        while queue:

            u = queue.popleft()

            for v in self.graph[u]:

                if v not in visited and self.graph[u][v] > 0:

                    visited.add(v)

                    queue.append(v)

        

        return visited





def solve_max_flow(num_vertices: int, edges: List[Tuple[int, int, float]], 

                   source: int, sink: int) -> float:

    """

    最大流求解便捷函数

    

    Args:

        num_vertices: 顶点数

        edges: 边列表 (u, v, capacity)

        source: 源点

        sink: 汇点

    

    Returns:

        最大流值

    """

    solver = MaxFlowSolver(num_vertices)

    for u, v, cap in edges:

        solver.add_edge(u, v, cap)

    return solver.edmonds_karp(source, sink)





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单网络

    print("测试1 - 简单网络:")

    #       s ---1--- a ---2--- t

    #       |           |

    #       3           3

    #       |           |

    #       b ---1--- c

    

    solver1 = MaxFlowSolver(5)  # 0=s, 1=a, 2=b, 3=c, 4=t

    solver1.add_edge(0, 1, 3)  # s->a

    solver1.add_edge(0, 2, 3)  # s->b

    solver1.add_edge(1, 2, 2)  # a->b

    solver1.add_edge(1, 4, 2)  # a->t

    solver1.add_edge(2, 3, 2)  # b->c

    solver1.add_edge(3, 4, 3)  # c->t

    solver1.add_edge(1, 3, 3)  # a->c

    

    max_flow = solver1.edmonds_karp(0, 4)

    print(f"  最大流: {max_flow}")

    

    # 测试2: 使用便捷函数

    print("\n测试2 - 使用便捷函数:")

    edges = [(0, 1, 10), (0, 2, 10), (1, 2, 2), (1, 3, 4), (2, 3, 8), (3, 4, 10)]

    max_flow2 = solve_max_flow(5, edges, 0, 4)

    print(f"  最大流: {max_flow2}")

    

    # 测试3: 二分匹配

    print("\n测试3 - 二分匹配(最大流建模):")

    # 将二分匹配问题转换为最大流问题

    # 左侧3个节点,右侧3个节点,边: 0->0, 0->2, 1->0, 1->1, 2->2

    

    # 创建流网络: s -> left -> right -> t

    solver3 = MaxFlowSolver(9)  # 0=s, 1-3=left, 4-6=right, 7=t

    

    # s到左侧

    for i in range(3):

        solver3.add_edge(0, 1 + i, 1)

    

    # 左侧到右侧的边

    left_to_right = [(0, 0), (0, 2), (1, 0), (1, 1), (2, 2)]

    for l, r in left_to_right:

        solver3.add_edge(1 + l, 4 + r, 1)

    

    # 右侧到t

    for i in range(3):

        solver3.add_edge(4 + i, 8, 1)

    

    max_flow3 = solver3.edmonds_karp(0, 8)

    print(f"  最大匹配数: {max_flow3}")

    

    # 测试4: 验证最大流最小割定理

    print("\n测试4 - 验证最小割:")

    min_cut = solver1.get_min_cut(0)

    print(f"  从源点{0}可达集合: {min_cut}")

    print(f"  最小割另一侧: {set(range(5)) - min_cut}")

    

    # 计算割的容量

    cut_capacity = 0

    for u in min_cut:

        for v in range(5):

            if v not in min_cut and (u, v) in solver1.original_capacity:

                cut_capacity += solver1.original_capacity[(u, v)]

    print(f"  最小割容量: {cut_capacity}")

    

    # 测试5: 多源多汇问题

    print("\n测试5 - 多源多汇(超级源汇):")

    # 添加超级源点和超级汇点

    solver5 = MaxFlowSolver(6)  # 0,1=源, 2,3=中间, 4,5=汇, 5=special_sink

    

    # 实际网络

    solver5.add_edge(0, 2, 10)

    solver5.add_edge(1, 2, 5)

    solver5.add_edge(2, 3, 15)

    solver5.add_edge(3, 4, 10)

    solver5.add_edge(3, 5, 5)

    

    # 添加超级源点

    super_source = 6

    solver5.add_edge(super_source, 0, float('inf'))

    solver5.add_edge(super_source, 1, float('inf'))

    

    # 添加超级汇点

    super_sink = 7

    solver5.add_edge(4, super_sink, float('inf'))

    solver5.add_edge(5, super_sink, float('inf'))

    

    # 临时扩展

    solver5.graph[super_source] = {0: float('inf'), 1: float('inf')}

    solver5.graph[super_sink] = {}

    solver5.n = 8

    

    # 重新创建求解器(简化版)

    solver5_simple = MaxFlowSolver(8)

    for u in [0, 1, 2, 3, 4, 5]:

        for v, cap in solver5.graph[u].items():

            if cap > 0:

                solver5_simple.add_edge(u, v, cap)

    

    # 超级源到原源

    solver5_simple.add_edge(6, 0, float('inf'))

    solver5_simple.add_edge(6, 1, float('inf'))

    # 原汇到超级汇

    solver5_simple.add_edge(4, 7, float('inf'))

    solver5_simple.add_edge(5, 7, float('inf'))

    

    max_flow5 = solver5_simple.edmonds_karp(6, 7)

    print(f"  多源多汇最大流: {max_flow5}")

    

    print("\n所有测试完成!")

