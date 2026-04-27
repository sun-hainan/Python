# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / dijkstra_routing



本文件实现 dijkstra_routing 相关的算法功能。

"""



import heapq

from dataclasses import dataclass, field

from typing import List, Dict, Tuple, Optional, Set

import matplotlib.pyplot as plt

import random





@dataclass

class Edge:

    """图的边"""

    src: str

    dst: str

    weight: float

    

    def __repr__(self):

        return f"{self.src}->{self.dst}({self.weight})"





@dataclass

class Graph:

    """加权有向图"""

    vertices: Set[str] = field(default_factory=set)

    edges: Dict[str, List[Edge]] = field(default_factory=dict)  # src -> [edges]

    

    def add_vertex(self, v: str):

        """添加顶点"""

        self.vertices.add(v)

        if v not in self.edges:

            self.edges[v] = []

    

    def add_edge(self, src: str, dst: str, weight: float, directed=False):

        """

        添加边

        

        Args:

            src: 源顶点

            dst: 目标顶点

            weight: 权重

            directed: 是否为有向图

        """

        self.add_vertex(src)

        self.add_vertex(dst)

        

        self.edges[src].append(Edge(src, dst, weight))

        

        if not directed:

            self.edges[dst].append(Edge(dst, src, weight))





class DijkstraRouter:

    """

    Dijkstra最短路径路由器

    """

    

    def __init__(self, graph: Graph):

        self.graph = graph

        self.distances: Dict[str, float] = {}

        self.previous: Dict[str, Optional[str]] = {}

        self.paths: Dict[str, List[str]] = {}

    

    def shortest_path(self, source: str, destination: str = None) -> Tuple[Dict[str, float], Dict[str, List[str]]]:

        """

        计算从source到所有节点的最短路径

        

        Args:

            source: 源顶点

            destination: 目标顶点（可选）

        

        Returns:

            (distances, paths)

        """

        # 初始化

        dist = {v: float('inf') for v in self.graph.vertices}

        prev = {v: None for v in self.graph.vertices}

        dist[source] = 0

        

        # 优先队列: (distance, vertex)

        pq = [(0, source)]

        visited = set()

        

        while pq:

            d, u = heapq.heappop(pq)

            

            if u in visited:

                continue

            visited.add(u)

            

            # 遍历邻居

            for edge in self.graph.edges.get(u, []):

                v = edge.dst

                new_dist = d + edge.weight

                

                if new_dist < dist[v]:

                    dist[v] = new_dist

                    prev[v] = u

                    heapq.heappush(pq, (new_dist, v))

        

        # 重建路径

        paths = {}

        for v in self.graph.vertices:

            paths[v] = self._reconstruct_path(prev, source, v)

        

        self.distances = dist

        self.previous = prev

        self.paths = paths

        

        return dist, paths

    

    def _reconstruct_path(self, prev: Dict[str, Optional[str]], 

                         source: str, target: str) -> List[str]:

        """重建从source到target的路径"""

        path = []

        current = target

        

        while current is not None:

            path.append(current)

            current = prev[current]

        

        path.reverse()

        

        # 验证路径

        if path and path[0] != source:

            return []

        

        return path

    

    def get_routing_table(self, source: str) -> Dict[str, Tuple[str, float]]:

        """

        获取路由表

        

        Args:

            source: 路由器ID

        

        Returns:

            {destination: (next_hop, distance)}

        """

        self.shortest_path(source)

        

        routing_table = {}

        for dest in self.graph.vertices:

            if dest == source:

                continue

            

            path = self.paths[dest]

            if path and len(path) > 1:

                routing_table[dest] = (path[1], self.distances[dest])

        

        return routing_table





class BidirectionalDijkstra:

    """

    双向Dijkstra算法

    

    从源和目标同时搜索，减少搜索空间

    """

    

    def __init__(self, graph: Graph):

        self.graph = graph

    

    def shortest_path(self, source: str, target: str) -> Tuple[float, List[str]]:

        """

        计算最短路径

        

        Args:

            source: 源顶点

            target: 目标顶点

        

        Returns:

            (distance, path)

        """

        if source == target:

            return 0, [source]

        

        # 双向搜索

        dist_s = {source: 0}  # 从source出发的距离

        dist_t = {target: 0}  # 从target出发的距离

        prev_s = {source: None}

        prev_t = {target: None}

        

        visited_s = set()

        visited_t = set()

        

        pq_s = [(0, source)]

        pq_t = [(0, target)]

        

        best_dist = float('inf')

        best_node = None

        

        while pq_s and pq_t:

            # 从source侧扩展

            if pq_s:

                d_s, u_s = heapq.heappop(pq_s)

                

                if u_s not in visited_s:

                    visited_s.add(u_s)

                    

                    # 检查是否与target侧相交

                    if u_s in visited_t:

                        current_dist = dist_s[u_s] + dist_t[u_s]

                        if current_dist < best_dist:

                            best_dist = current_dist

                            best_node = u_s

                        break

                    

                    for edge in self.graph.edges.get(u_s, []):

                        v = edge.dst

                        new_dist = dist_s[u_s] + edge.weight

                        if v not in dist_s or new_dist < dist_s[v]:

                            dist_s[v] = new_dist

                            prev_s[v] = u_s

                            heapq.heappush(pq_s, (new_dist, v))

            

            # 从target侧扩展

            if pq_t:

                d_t, u_t = heapq.heappop(pq_t)

                

                if u_t not in visited_t:

                    visited_t.add(u_t)

                    

                    if u_t in visited_s:

                        current_dist = dist_s[u_t] + dist_t[u_t]

                        if current_dist < best_dist:

                            best_dist = current_dist

                            best_node = u_t

                        break

                    

                    for edge in self.graph.edges.get(u_t, []):

                        v = edge.dst

                        new_dist = dist_t[u_t] + edge.weight

                        if v not in dist_t or new_dist < dist_t[v]:

                            dist_t[v] = new_dist

                            prev_t[v] = u_t

                            heapq.heappush(pq_t, (new_dist, v))

        

        # 重建路径

        if best_node is None:

            return float('inf'), []

        

        # 从source侧重建

        path_s = []

        node = best_node

        while node is not None:

            path_s.append(node)

            node = prev_s.get(node)

        path_s.reverse()

        

        # 从target侧重建

        path_t = []

        node = best_node

        while node is not None:

            path_t.append(node)

            node = prev_t.get(node)

        

        return best_dist, path_s + path_t[1:]





def visualize_graph(graph: Graph, routing_paths: Dict[Tuple[str, str], List[str]] = None):

    """

    可视化图和路由路径

    """

    # 为简化，使用矩阵表示

    n = len(graph.vertices)

    vertices_list = sorted(graph.vertices)

    

    print("\n邻接表:")

    for v in vertices_list:

        edges = graph.edges.get(v, [])

        if edges:

            print(f"  {v}: {', '.join(str(e) for e in edges)}")





def demo_basic_dijkstra():

    """

    演示基本Dijkstra算法

    """

    print("=== Dijkstra算法演示 ===\n")

    

    # 创建网络拓扑

    graph = Graph()

    

    # 添加边（模拟网络拓扑）

    edges = [

        ("A", "B", 4),

        ("A", "C", 2),

        ("B", "C", 1),

        ("B", "D", 5),

        ("C", "D", 8),

        ("C", "E", 10),

        ("D", "E", 2),

        ("D", "F", 6),

        ("E", "F", 3),

    ]

    

    for src, dst, weight in edges:

        graph.add_edge(src, dst, weight)

    

    print("网络拓扑:")

    for src, dst, weight in edges:

        print(f"  {src} <--{weight}--> {dst}")

    

    # 计算最短路径

    router = DijkstraRouter(graph)

    dists, paths = router.shortest_path("A")

    

    print("\n从 A 出发的最短路径:")

    for dest in sorted(graph.vertices):

        if dest == "A":

            continue

        print(f"  A -> {dest}: 距离={dists[dest]:.1f}, 路径={' -> '.join(paths[dest])}")

    

    # 路由表

    print("\n路由表:")

    rt = router.get_routing_table("A")

    for dest, (next_hop, dist) in sorted(rt.items()):

        print(f"  -> {dest}: 下一跳={next_hop}, 距离={dist:.1f}")





def demo_network_routing():

    """

    演示网络路由场景

    """

    print("\n=== 网络路由场景 ===\n")

    

    # 创建更复杂的网络拓扑

    graph = Graph()

    

    # 模拟ISP网络

    edges = [

        # 核心层

        ("Core1", "Core2", 1),

        ("Core2", "Core3", 1),

        ("Core3", "Core1", 1),

        # 汇聚层

        ("Agg1", "Core1", 2),

        ("Agg1", "Core2", 2),

        ("Agg2", "Core2", 2),

        ("Agg2", "Core3", 2),

        # 接入层

        ("Acc1", "Agg1", 3),

        ("Acc1", "Agg2", 3),

        ("Acc2", "Agg2", 3),

        # 主机

        ("Host1", "Acc1", 1),

        ("Host2", "Acc1", 1),

        ("Host3", "Acc2", 1),

    ]

    

    for src, dst, weight in edges:

        graph.add_edge(src, dst, weight)

    

    router = DijkstraRouter(graph)

    

    # Host1到Host3的路由

    print("Host1 到 Host3 的路由分析:")

    dists, paths = router.shortest_path("Host1")

    

    print(f"  最短距离: {dists['Host3']}")

    print(f"  路径: {' -> '.join(paths['Host3'])}")

    

    # 模拟链路故障

    print("\n模拟链路故障 (Agg1-Core1 断开):")

    

    # 重新构建图（移除一条边）

    graph2 = Graph()

    for src, dst, weight in edges:

        if not ((src == "Agg1" and dst == "Core1") or (src == "Core1" and dst == "Agg1")):

            graph2.add_edge(src, dst, weight)

    

    router2 = DijkstraRouter(graph2)

    dists2, paths2 = router2.shortest_path("Host1")

    

    print(f"  新最短距离: {dists2['Host3']}")

    print(f"  新路径: {' -> '.join(paths2['Host3'])}")





def demo_bidirectional():

    """

    演示双向Dijkstra

    """

    print("\n=== 双向Dijkstra演示 ===\n")

    

    # 创建大型图

    graph = Graph()

    

    # 网格拓扑

    size = 10

    for i in range(size):

        for j in range(size):

            if i > 0:

                graph.add_edge(f"({i},{j})", f"({i-1},{j})", 1)

            if j > 0:

                graph.add_edge(f"({i},{j})", f"({i},{j-1})", 1)

    

    source = "(0,0)"

    target = "(9,9)"

    

    # 单向Dijkstra

    import time

    router = DijkstraRouter(graph)

    

    start = time.time()

    dists, paths = router.shortest_path(source)

    single_time = time.time() - start

    

    # 双向Dijkstra

    bi_dijkstra = BidirectionalDijkstra(graph)

    

    start = time.time()

    bi_dist, bi_path = bi_dijkstra.shortest_path(source, target)

    bi_time = time.time() - start

    

    print(f"拓扑大小: {len(graph.vertices)} 节点")

    print(f"源: {source}, 目标: {target}")

    print(f"\n单向Dijkstra: {single_time*1000:.2f}ms")

    print(f"双向Dijkstra: {bi_time*1000:.2f}ms")

    print(f"加速比: {single_time/bi_time:.2f}x")

    print(f"\n距离验证: 单向={dists[target]:.1f}, 双向={bi_dist:.1f}")





def demo_routing_table_convergence():

    """

    演示路由表收敛

    """

    print("\n=== 路由表收敛演示 ===\n")

    

    graph = Graph()

    edges = [

        ("R1", "R2", 1),

        ("R2", "R3", 1),

        ("R3", "R4", 1),

        ("R1", "R3", 10),  # 备份链路

    ]

    

    for src, dst, weight in edges:

        graph.add_edge(src, dst, weight)

    

    router = DijkstraRouter(graph)

    

    print("初始状态:")

    rt = router.get_routing_table("R1")

    for dest, (next_hop, dist) in sorted(rt.items()):

        print(f"  R1 -> {dest}: 下一跳={next_hop}, 距离={dist}")

    

    print("\nR2-R3链路故障:")

    print("  R1 需要重新计算到 R3,R4 的路径")

    

    # 模拟故障

    graph2 = Graph()

    edges2 = [

        ("R1", "R2", 1),

        ("R1", "R3", 10),  # 只能走这条

        ("R3", "R4", 1),

    ]

    for src, dst, weight in edges2:

        graph2.add_edge(src, dst, weight)

    

    router2 = DijkstraRouter(graph2)

    rt2 = router2.get_routing_table("R1")

    

    print("\n收敛后:")

    for dest, (next_hop, dist) in sorted(rt2.items()):

        print(f"  R1 -> {dest}: 下一跳={next_hop}, 距离={dist}")

    

    print("\n注意: R1->R3的路径从 R1->R2->R3(距离2) 变为 R1->R3(距离10)")





if __name__ == "__main__":

    print("=" * 60)

    print("Dijkstra最短路径路由算法")

    print("=" * 60)

    

    # 基本演示

    demo_basic_dijkstra()

    

    # 网络路由场景

    demo_network_routing()

    

    # 双向Dijkstra

    demo_bidirectional()

    

    # 路由表收敛

    demo_routing_table_convergence()

    

    print("\n" + "=" * 60)

    print("算法复杂度分析:")

    print("=" * 60)

    print("""

朴素实现: O(V^2)

优先队列: O((V+E)logV)



Dijkstra vs Bellman-Ford:

| 特性       | Dijkstra    | Bellman-Ford |

|------------|-------------|---------------|

| 时间复杂度 | O((V+E)logV)| O(VE)         |

| 边权重     | 非负         | 可以为负       |

| 负权重检测 | 不支持       | 支持           |



优化变体:

- 双向Dijkstra: 适合固定起点终点

- A*搜索: Dijkstra + 启发式

- Contraction Hierarchies: 预处理加速

""")

