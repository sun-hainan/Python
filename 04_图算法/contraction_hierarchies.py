# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / contraction_hierarchies



本文件实现 contraction_hierarchies 相关的算法功能。

"""



import heapq

from typing import List, Tuple, Dict, Set, Optional

from collections import defaultdict





class Edge:

    """图的边"""

    def __init__(self, to: int, weight: float, shortcut: bool = False, 

                 via_node: Optional[int] = None):

        self.to = to              # 目标节点

        self.weight = weight     # 边权重

        self.shortcut = shortcut  # 是否为 shortcut 边

        self.via_node = via_node  # shortcut 经过的中间节点（用于路径重建）

    

    def __repr__(self):

        if self.shortcut:

            return f"Edge(to={self.to}, w={self.weight}, via={self.via_node})"

        return f"Edge(to={self.to}, w={self.weight})"





class ContractionHierarchies:

    """

    Contraction Hierarchies 最短路径算法

    

    预处理步骤：

    1. 计算所有节点的重要性

    2. 按重要性从低到高收缩节点

    3. 添加必要的 shortcut 边

    """

    

    def __init__(self, n: int):

        """

        Args:

            n: 节点数量

        """

        self.n = n

        self.graph: List[List[Edge]] = [[] for _ in range(n)]

        self.reverse_graph: List[List[Edge]] = [[] for _ in range(n)]

        self.order: List[int] = []       # 节点收缩顺序

        self.rank: List[int] = [-1] * n   # rank[node] = 收缩顺序

    

    def add_edge(self, u: int, v: int, w: float):

        """添加无向边"""

        self.graph[u].append(Edge(v, w))

        self.graph[v].append(Edge(u, w))

    

    def calc_importance(self, node: int, 

                        witnessed: Set[Tuple[int, int]]) -> float:

        """

        计算节点重要性（越大越重要，越后收缩）

        

        启发式规则：

        - Shortcut 覆盖率：添加这个节点能省多少条边

        - 邻居数量：邻居越少越重要

        - 边数：节点上的边数

        

        Args:

            node: 节点ID

            witnessed: 已有的 shortcut 覆盖（边对）

        

        Returns:

            重要性分数

        """

        # 邻居边数

        edge_count = len(self.graph[node])

        

        # 计算如果收缩这个节点，会添加多少 shortcut

        # 通过检查所有不相邻的邻居对

        shortcuts = 0

        neighbors = [e.to for e in self.graph[node]]

        

        for i, u in enumerate(neighbors):

            for v in neighbors[i+1:]:

                # 如果 u 和 v 不直接相连，收缩 node 会产生 shortcut

                directly_connected = any(e.to == v for e in self.graph[u])

                if not directly_connected:

                    shortcuts += 1

        

        # 重要性 = 1000 * shortcuts - edge_count

        # shortcut 越多越重要（最后收缩），边越多越不重要（先收缩）

        importance = 1000 * shortcuts - edge_count

        

        return importance

    

    def contract_node(self, node: int) -> int:

        """

        收缩单个节点

        

        1. 找出所有需要 shortcut 的邻居对

        2. 添加 shortcut 边

        3. 从图中移除该节点

        

        Args:

            node: 要收缩的节点

        

        Returns:

            添加的 shortcut 数量

        """

        neighbors = [e.to for e in self.graph[node]]

        shortcuts_added = 0

        

        # 检查每对邻居是否需要 shortcut

        for i, u in enumerate(neighbors):

            for v in neighbors[i+1:]:

                # 检查 u 和 v 是否已直接相连

                direct = False

                for e in self.graph[u]:

                    if e.to == v:

                        direct = True

                        break

                

                if direct:

                    continue

                

                # 计算 u 到 v 经过 node 的最短距离

                # dist(u, node) + dist(node, v)

                dist_u_node = next((e.weight for e in self.graph[node] if e.to == u), float('inf'))

                dist_node_v = next((e.weight for e in self.graph[node] if e.to == v), float('inf'))

                shortcut_dist = dist_u_node + dist_node_v

                

                # 添加 shortcut（更新逆图）

                # 这里简化为只记录 u->v

                self.graph[u].append(Edge(v, shortcut_dist, 

                                         shortcut=True, via_node=node))

                

                # 在逆图中添加 v->u

                self.graph[v].append(Edge(u, shortcut_dist,

                                         shortcut=True, via_node=node))

                

                shortcuts_added += 1

        

        # 从所有邻居的邻居列表中移除 node（保持一致性）

        for neighbor in neighbors:

            self.graph[neighbor] = [e for e in self.graph[neighbor] if e.to != node]

        

        return shortcuts_added

    

    def build(self) -> None:

        """

        构建收缩层级（预处理）

        

        核心流程：

        1. 计算所有节点的重要性

        2. 选择最重要的节点（最后收缩）进行扩张

        3. 重复直到所有节点都被处理

        """

        # 计算初始重要性

        importance = [self.calc_importance(i, set()) for i in range(self.n)]

        

        # 使用最大堆（Python 的 heapq 是最小堆，所以取负数）

        heap = [(-imp, i) for i, imp in enumerate(importance)]

        heapq.heapify(heap)

        

        contracted: Set[int] = set()

        

        while heap:

            neg_imp, node = heapq.heappop(heap)

            

            if node in contracted:

                continue

            

            # 标记为已收缩

            contracted.add(node)

            self.order.append(node)

            self.rank[node] = len(self.order) - 1

            

            # 添加 shortcut

            shortcuts = self.contract_node(node)

            

            # 更新邻居的重要性并重新入堆

            for e in self.graph[node]:

                if e.to not in contracted:

                    new_imp = self.calc_importance(e.to, set())

                    heapq.heappush(heap, (-new_imp, e.to))

    

    def query(self, start: int, goal: int) -> Optional[Tuple[float, List[int]]]:

        """

        查询从起点到终点的最短路径

        

        使用双向 Dijkstra，只沿"向上"方向搜索

        

        Args:

            start: 起点ID

            goal: 终点ID

        

        Returns:

            (最短距离, 路径节点列表) 或 None

        """

        if start == goal:

            return (0.0, [start])

        

        # 双向 Dijkstra

        # forward: 从起点向上（只走 rank 增加的方向）

        # backward: 从终点向上

        

        INF = float('inf')

        

        dist_f: Dict[int, float] = {start: 0}

        dist_b: Dict[int, float] = {goal: 0}

        

        # 已访问节点

        visited_f: Set[int] = set()

        visited_b: Set[int] = set()

        

        # 优先队列：(距离, 节点)

        heap_f = [(0, start)]

        heap_b = [(0, goal)]

        

        best_dist = INF

        best_node = None

        

        while heap_f and heap_b:

            # 从起点侧扩展

            if heap_f:

                d_f, u_f = heapq.heappop(heap_f)

                

                if u_f not in visited_f:

                    visited_f.add(u_f)

                    

                    # 检查是否与反向搜索相交

                    if u_f in dist_b:

                        total = dist_f[u_f] + dist_b[u_f]

                        if total < best_dist:

                            best_dist = total

                            best_node = u_f

                    

                    # 只沿 rank 增加的方向扩展（向上）

                    for edge in self.graph[u_f]:

                        v = edge.to

                        # 向上移动：rank 只能增加

                        if self.rank[v] > self.rank[u_f]:

                            new_dist = dist_f[u_f] + edge.weight

                            if v not in dist_f or new_dist < dist_f[v]:

                                dist_f[v] = new_dist

                                heapq.heappush(heap_f, (new_dist, v))

            

            # 从终点侧扩展

            if heap_b:

                d_b, u_b = heapq.heappop(heap_b)

                

                if u_b not in visited_b:

                    visited_b.add(u_b)

                    

                    if u_b in dist_f:

                        total = dist_f[u_b] + dist_b[u_b]

                        if total < best_dist:

                            best_dist = total

                            best_node = u_b

                    

                    for edge in self.graph[u_b]:

                        v = edge.to

                        if self.rank[v] > self.rank[u_b]:

                            new_dist = dist_b[u_b] + edge.weight

                            if v not in dist_b or new_dist < dist_b[v]:

                                dist_b[v] = new_dist

                                heapq.heappush(heap_b, (new_dist, v))

        

        if best_dist == INF:

            return None

        

        # 路径重建（简化版本）

        path = self._reconstruct_path(start, goal, dist_f, dist_b, best_node)

        return (best_dist, path)

    

    def _reconstruct_path(self, start: int, goal: int,

                          dist_f: Dict[int, float],

                          dist_b: Dict[int, float],

                          meet_node: int) -> List[int]:

        """

        重建从起点到终点的路径

        

        通过 shortcut 的 via_node 信息重建完整路径

        """

        # 前半部分：从 start 到 meet_node

        path_f = [meet_node]

        curr = meet_node

        while curr != start:

            # 找到从哪个节点来的

            found = False

            for edge in self.graph[curr]:

                if self.rank[edge.to] < self.rank[curr]:

                    prev = edge.to

                    # 检查这是否是实际路径上的边

                    if prev in dist_f and abs(dist_f[prev] + edge.weight - dist_f[curr]) < 1e-9:

                        path_f.append(prev)

                        curr = prev

                        found = True

                        break

            if not found:

                break

        

        path_f.reverse()

        

        # 后半部分：从 meet_node 到 goal

        path_b = []

        curr = meet_node

        while curr != goal:

            found = False

            for edge in self.graph[curr]:

                if self.rank[edge.to] < self.rank[curr]:

                    next_node = edge.to

                    if next_node in dist_b and abs(dist_b[next_node] + edge.weight - dist_b[curr]) < 1e-9:

                        path_b.append(next_node)

                        curr = next_node

                        found = True

                        break

            if not found:

                break

        

        return path_f + path_b





def build_ch_from_edges(n: int, edges: List[Tuple[int, int, float]]) -> ContractionHierarchies:

    """

    从边列表构建收缩层级

    

    Args:

        n: 节点数量

        edges: 边列表 [(u, v, weight), ...]

    

    Returns:

        ContractionHierarchies 实例

    """

    ch = ContractionHierarchies(n)

    for u, v, w in edges:

        ch.add_edge(u, v, w)

    ch.build()

    return ch





if __name__ == "__main__":

    # 测试1：简单图

    print("测试1 - 简单图:")

    ch = ContractionHierarchies(6)

    edges = [

        (0, 1, 1), (0, 2, 2), (1, 2, 1),

        (1, 3, 3), (2, 3, 1), (2, 4, 4),

        (3, 4, 2), (3, 5, 1), (4, 5, 3),

    ]

    for u, v, w in edges:

        ch.add_edge(u, v, w)

    

    print(f"  节点数: {ch.n}, 边数: {sum(len(e) for e in ch.graph) // 2}")

    print(f"  收缩顺序: {ch.order}")

    

    # 查询测试

    result = ch.query(0, 5)

    print(f"  路径 0->5: {result}")

    

    # 测试2：较大图

    print("\n测试2 - 网格图:")

    # 创建 5x5 网格

    n = 25

    ch2 = ContractionHierarchies(n)

    

    for i in range(5):

        for j in range(5):

            idx = i * 5 + j

            if j < 4:  # 右邻居

                ch2.add_edge(idx, idx + 1, 1.0)

            if i < 4:  # 下邻居

                ch2.add_edge(idx, idx + 5, 1.0)

    

    print(f"  节点数: {ch2.n}, 边数: {sum(len(e) for e in ch2.graph) // 2}")

    

    # 多次查询

    test_queries = [(0, 24), (0, 12), (4, 20), (11, 13)]

    for s, g in test_queries:

        result = ch2.query(s, g)

        print(f"  路径 {s}->{g}: 距离={result[0] if result else '无'}")

    

    # 性能测试

    import time

    import random

    

    print("\n性能测试:")

    sizes = [100, 500, 1000]

    for size in sizes:

        n = size

        ch3 = ContractionHierarchies(n)

        

        # 创建随机图

        for i in range(n):

            for j in range(i + 1, min(i + 10, n)):

                if random.random() < 0.3:

                    w = random.uniform(1, 10)

                    ch3.add_edge(i, j, w)

        

        build_start = time.time()

        ch3.build()

        build_time = time.time() - build_start

        

        # 查询时间

        query_start = time.time()

        for _ in range(100):

            s = random.randint(0, n - 1)

            g = random.randint(0, n - 1)

            ch3.query(s, g)

        query_time = time.time() - query_start

        

        print(f"  n={size}: 预处理={build_time:.2f}s, 100次查询={query_time:.4f}s")

