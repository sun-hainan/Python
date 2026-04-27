# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / parallel_dijkstra

本文件实现 parallel_dijkstra 相关的算法功能。
"""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import math


class Graph:
    """图的邻接表表示"""
    
    def __init__(self):
        # 邻接表：adj[u] = [(v, weight), ...]
        self.adj = defaultdict(list)
        self.num_nodes = 0
    
    def add_edge(self, u, v, weight):
        """添加有向边 u -> v"""
        self.adj[u].append((v, weight))
        self.num_nodes = max(self.num_nodes, u + 1, v + 1)
    
    def add_undirected_edge(self, u, v, weight):
        """添加无向边 u <-> v"""
        self.add_edge(u, v, weight)
        self.add_edge(v, u, weight)


def parallel_multi_source_dijkstra(graph, source_nodes, num_workers=None):
    """
    多源并行 Dijkstra 算法（适合稀疏图，多源点）
    
    参数:
        graph: Graph 对象
        source_nodes: 源点列表
        num_workers: 并行工作线程数
    
    返回:
        distances: dict，key 为节点 id，value 为 (dist, source) 元组
                  表示从最近源点到达该节点的距离和源点
    """
    num_nodes = graph.num_nodes
    
    # 初始化距离：源点为 0，其他为无穷大
    INF = float('inf')
    distances = [INF] * num_nodes
    source_of_node = [-1] * num_nodes  # 记录每个节点属于哪个源点
    
    for src in source_nodes:
        distances[src] = 0
        source_of_node[src] = src
    
    # 使用优先队列实现多源 Dijkstra
    import heapq
    
    # 多源堆：元素为 (distance, source, node)
    heap = [(0, src, src) for src in source_nodes]
    heapq.heapify(heap)
    
    visited = [False] * num_nodes
    
    while heap:
        curr_dist, src, u = heapq.heappop(heap)
        
        # 如果已经访问过，跳过
        if visited[u]:
            continue
        
        visited[u] = True
        distances[u] = curr_dist
        source_of_node[u] = src
        
        # 松弛从 u 出发的所有边
        for v, weight in graph.adj[u]:
            if not visited[v]:
                new_dist = curr_dist + weight
                if new_dist < distances[v]:
                    heapq.heappush(heap, (new_dist, src, v))
    
    return distances, source_of_node


def parallel_bellman_ford(graph, source_nodes, num_workers=None):
    """
    并行多源 Bellman-Ford 算法（适合稠密图）
    
    参数:
        graph: Graph 对象
        source_nodes: 源点列表
        num_workers: 并行工作线程数
    
    返回:
        distances: 各节点到最近源点的最短距离
    """
    num_nodes = graph.num_nodes
    INF = float('inf')
    
    # 初始化
    distances = [INF] * num_nodes
    source_of_node = [-1] * num_nodes
    
    for src in source_nodes:
        distances[src] = 0
        source_of_node[src] = src
    
    # 获取所有边
    edges = []
    for u in graph.adj:
        for v, weight in graph.adj[u]:
            edges.append((u, v, weight))
    
    num_edges = len(edges)
    max_iterations = num_nodes - 1
    
    # Bellman-Ford 迭代
    for iteration in range(max_iterations):
        updated = False
        
        # 并行松弛所有边
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            def relax_edge(edge):
                u, v, weight = edge
                if distances[u] != INF and distances[u] + weight < distances[v]:
                    return (v, distances[u] + weight)
                return None
            
            futures = [executor.submit(relax_edge, e) for e in edges]
            
            for future in futures:
                result = future.result()
                if result:
                    v, new_dist = result
                    distances[v] = new_dist
                    # 更新源点信息
                    source_of_node[v] = source_of_node[edges[next(i for i, e in enumerate(edges) if e[1] == v)][0]]]
                    updated = True
        
        # 如果没有更新，提前结束
        if not updated:
            break
    
    return distances


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("多源最短路并行化 测试")
    print("=" * 60)
    
    # 测试用例1：简单图
    print("\n[测试1] 简单有向图")
    g1 = Graph()
    g1.add_edge(0, 1, 4)
    g1.add_edge(0, 2, 2)
    g1.add_edge(1, 2, 1)
    g1.add_edge(1, 3, 5)
    g1.add_edge(2, 3, 8)
    g1.add_edge(2, 4, 10)
    g1.add_edge(3, 4, 2)
    g1.add_edge(3, 5, 6)
    g1.add_edge(4, 5, 3)
    
    sources = [0]
    dists, sources_info = parallel_multi_source_dijkstra(g1, sources)
    print(f"源点: {sources}")
    print(f"最短距离: {dists[:6]}")
    
    # 验证：手动计算最短路
    expected = [0, 4, 2, 9, 11, 14]  # 从节点0到各点的最短路
    assert dists[:6] == expected, f"结果错误: {dists[:6]} vs {expected}"
    print("✅ 通过\n")
    
    # 测试用例2：多源
    print("[测试2] 多源最短路")
    g2 = Graph()
    g2.add_undirected_edge(0, 1, 4)
    g2.add_undirected_edge(0, 2, 2)
    g2.add_undirected_edge(1, 2, 1)
    g2.add_undirected_edge(1, 3, 5)
    g2.add_undirected_edge(2, 3, 8)
    g2.add_undirected_edge(3, 4, 2)
    g2.add_undirected_edge(4, 5, 3)
    
    sources = [0, 5]
    dists, sources_info = parallel_multi_source_dijkstra(g2, sources)
    print(f"源点: {sources}")
    print(f"到各节点的距离: {dists[:6]}")
    print(f"来源源点: {sources_info[:6]}")
    
    # 验证：节点0到自身0，节点5到自身0
    assert dists[0] == 0, "节点0距离应为0"
    assert dists[5] == 0, "节点5距离应为0"
    print("✅ 通过\n")
    
    # 测试用例3：无向图连通性
    print("[测试3] 连通无向图")
    g3 = Graph()
    g3.add_undirected_edge(0, 1, 1)
    g3.add_undirected_edge(1, 2, 2)
    g3.add_undirected_edge(2, 3, 3)
    g3.add_undirected_edge(3, 4, 4)
    
    sources = [0]
    dists, _ = parallel_multi_source_dijkstra(g3, sources)
    expected = [0, 1, 3, 6, 10]
    print(f"从节点0出发: {dists[:5]}")
    assert dists[:5] == expected, f"结果错误: {dists[:5]} vs {expected}"
    print("✅ 通过\n")
    
    # 测试用例4：未连通图
    print("[测试4] 未连通图")
    g4 = Graph()
    g4.add_edge(0, 1, 1)
    g4.add_edge(2, 3, 2)  # 另一个连通分量
    
    sources = [0]
    dists, _ = parallel_multi_source_dijkstra(g4, sources)
    print(f"距离: {dists}")
    assert dists[0] == 0
    assert dists[1] == 1
    assert dists[2] == float('inf')  # 不可达
    assert dists[3] == float('inf')  # 不可达
    print("✅ 通过\n")
    
    # 测试用例5：Bellman-Ford 验证
    print("[测试5] Bellman-Ford 并行算法验证")
    g5 = Graph()
    g5.add_edge(0, 1, -1)
    g5.add_edge(0, 2, 4)
    g5.add_edge(1, 2, 3)
    g5.add_edge(1, 3, 2)
    g5.add_edge(1, 4, 2)
    g5.add_edge(3, 2, 5)
    g5.add_edge(3, 1, 1)
    g5.add_edge(4, 3, -3)
    
    sources = [0]
    dists_dijkstra, _ = parallel_multi_source_dijkstra(g5, sources)
    dists_bellman, _ = parallel_bellman_ford(g5, sources)
    
    print(f"Dijkstra 结果: {dists_dijkstra[:5]}")
    print(f"Bellman-Ford 结果: {dists_bellman[:5]}")
    assert dists_dijkstra == dists_bellman, "两种算法结果不一致"
    print("✅ 通过")
    
    print("\n" + "=" * 60)
    print("所有测试通过！多源最短路并行化验证完成。")
    print("=" * 60)
