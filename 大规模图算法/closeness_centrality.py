"""
接近中心性算法 (Closeness Centrality)
======================================
计算图中每个节点的接近中心性：节点到所有其他节点的最短路径长度之和的倒数。

接近中心性衡量一个节点到图中所有其他节点的"接近"程度。

使用Brandes算法的变体实现。

参考：
    - Bavelas, A. (1950). Communication patterns in task-oriented groups.
    - Freeman, L.C. (1979). Centrality in social networks: Conceptual clarification.
"""

from typing import List, Dict, Set, Tuple
from collections import deque
import math


class Graph:
    """无向图数据结构"""
    
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [[] for _ in range(n)]  # adj[u] = [v1, v2, ...]
    
    def add_edge(self, u: int, v: int):
        """添加无向边"""
        self.adj[u].append(v)
        self.adj[v].append(u)
    
    def neighbors(self, u: int) -> List[int]:
        """返回邻居列表"""
        return self.adj[u]


def bfs_distances(graph: Graph, source: int) -> Tuple[Dict[int, int], Dict[int, int], Dict[int, List[int]]]:
    """
    BFS计算单源最短路径
    
    参数:
        graph: 输入图
        source: 源节点
    
    返回:
        (distances: 距离, num_shortest_paths: 最短路径数, predecessors: 前驱)
    """
    n = graph.n
    distances = {v: -1 for v in range(n)}
    num_paths = {v: 0 for v in range(n)}
    predecessors = {v: [] for v in range(n)}
    
    distances[source] = 0
    num_paths[source] = 1
    
    queue = deque([source])
    
    while queue:
        v = queue.popleft()
        
        for w in graph.neighbors(v):
            # 第一次发现
            if distances[w] == -1:
                distances[w] = distances[v] + 1
                queue.append(w)
            
            # 找到更短路径
            if distances[w] == distances[v] + 1:
                num_paths[w] += num_paths[v]
                predecessors[w].append(v)
    
    return distances, num_paths, predecessors


def closeness_centrality_naive(graph: Graph, normalized: bool = True) -> Dict[int, float]:
    """
    朴素接近中心性计算
    
    参数:
        graph: 输入图
        normalized: 是否归一化
    
    返回:
        节点 -> 接近中心性
    """
    n = graph.n
    closeness = {}
    
    for source in range(n):
        distances, _, _ = bfs_distances(graph, source)
        
        # 计算可达节点的距离和
        total_dist = 0
        reachable = 0
        
        for target in range(n):
            if distances[target] > 0:  # 排除自己
                total_dist += distances[target]
                reachable += 1
        
        if reachable > 0 and total_dist > 0:
            # 接近中心性 = n-1 / 距离和
            closeness[source] = reachable / total_dist
        else:
            closeness[source] = 0.0
        
        # 归一化：乘以可达节点数/(n-1)
        if normalized and reachable > 0:
            closeness[source] *= reachable / (n - 1)
    
    return closeness


def brandes_closeness(graph: Graph) -> Dict[int, float]:
    """
    Brandes接近中心性算法
    
    利用前驱信息减少重复计算
    
    参数:
        graph: 输入图
    
    返回:
        节点 -> 接近中心性
    """
    n = graph.n
    closeness = {v: 0.0 for v in range(n)}
    
    for s in range(n):
        # BFS from s
        distances, num_paths, predecessors = bfs_distances(graph, s)
        
        # 可达节点数
        reachable = sum(1 for d in distances.values() if d > 0)
        
        if reachable == 0:
            continue
        
        # 按距离降序处理节点
        nodes_by_dist = sorted([v for v in range(n) if distances[v] > 0], 
                               key=lambda x: distances[x], reverse=True)
        
        # 累加距离贡献
        for v in nodes_by_dist:
            for p in predecessors[v]:
                # p对closeness[s]的贡献
                sigma_p = num_paths[p]
                sigma_v = num_paths[v]
                if sigma_v > 0:
                    closeness[s] += (sigma_p / sigma_v) * distances[v]
    
    # 处理
    for v in range(n):
        # 加上到每个可达节点的距离本身
        distances, _, _ = bfs_distances(graph, v)
        total = sum(d for d in distances.values() if d > 0)
        if total > 0:
            reachable = sum(1 for d in distances.values() if d > 0)
            closeness[v] = (reachable - 1) / total if total > 0 else 0
            closeness[v] *= reachable / (n - 1)
    
    return closeness


def closeness_centrality_weighted(graph: Graph, 
                                   weights: Dict[Tuple[int, int], float]) -> Dict[int, float]:
    """
    加权图的接近中心性（使用Dijkstra）
    
    参数:
        graph: 输入图
        weights: 边权重 {(u,v): weight}
    
    返回:
        节点 -> 接近中心性
    """
    import heapq
    
    n = graph.n
    closeness = {}
    
    for source in range(n):
        # Dijkstra
        dist = {v: math.inf for v in range(n)}
        dist[source] = 0
        pq = [(0, source)]
        
        while pq:
            d, v = heapq.heappop(pq)
            if d > dist[v]:
                continue
            
            for w in graph.neighbors(v):
                edge_key = (min(v, w), max(v, w))
                weight = weights.get(edge_key, 1.0)
                new_dist = dist[v] + weight
                
                if new_dist < dist[w]:
                    dist[w] = new_dist
                    heapq.heappush(pq, (new_dist, w))
        
        # 计算接近中心性
        total_dist = sum(d for d in dist.values() if d < math.inf and d > 0)
        reachable = sum(1 for d in dist.values() if d < math.inf and d > 0)
        
        if total_dist > 0 and reachable > 0:
            closeness[source] = (reachable - 1) / total_dist
            closeness[source] *= reachable / (n - 1)
        else:
            closeness[source] = 0.0
    
    return closeness


def harmonic_centrality(graph: Graph) -> Dict[int, float]:
    """
    调和中心性：接近中心性的变体
    
    h(v) = sum_{u != v} 1 / d(u, v)
    
    参数:
        graph: 输入图
    
    返回:
        节点 -> 调和中心性
    """
    n = graph.n
    harmonic = {v: 0.0 for v in range(n)}
    
    for source in range(n):
        distances, _, _ = bfs_distances(graph, source)
        
        for target in range(n):
            if source != target and distances[target] > 0:
                harmonic[source] += 1.0 / distances[target]
    
    return harmonic


def closeness_centrality_sample(graph: Graph, k: int, seed: int = 42) -> Dict[int, float]:
    """
    近似接近中心性：只从k个随机节点计算
    
    参数:
        graph: 输入图
        k: 采样节点数
        seed: 随机种子
    
    返回:
        近似的接近中心性
    """
    import random
    random.seed(seed)
    
    n = graph.n
    sources = random.sample(range(n), min(k, n))
    
    # 存储部分结果
    partial_sum = {v: 0.0 for v in range(n)}
    partial_count = {v: 0 for v in range(n)}
    
    for source in sources:
        distances, _, _ = bfs_distances(graph, source)
        reachable = sum(1 for d in distances.values() if d > 0)
        
        for v in range(n):
            if distances[v] > 0:
                partial_sum[v] += (reachable - 1) / distances[v]
                partial_count[v] += 1
    
    # 推断到所有n个节点的接近中心性
    closeness = {}
    for v in range(n):
        if partial_count[v] > 0:
            # 从采样节点推断
            avg_reachable_ratio = partial_count[v] / k
            closeness[v] = (partial_sum[v] / partial_count[v]) * avg_reachable_ratio
        else:
            closeness[v] = 0.0
    
    return closeness


def graph_components_closeness(graph: Graph) -> Dict[int, float]:
    """
    处理非连通图的接近中心性
    
    对每个连通分量分别计算
    
    参数:
        graph: 输入图
    
    返回:
        节点 -> 接近中心性
    """
    n = graph.n
    
    # 找连通分量
    visited = [False] * n
    components = []
    
    for start in range(n):
        if not visited[start]:
            # BFS找连通分量
            component = []
            queue = deque([start])
            visited[start] = True
            
            while queue:
                v = queue.popleft()
                component.append(v)
                
                for w in graph.neighbors(v):
                    if not visited[w]:
                        visited[w] = True
                        queue.append(w)
            
            components.append(component)
    
    closeness = {}
    
    for component in components:
        if len(component) == 1:
            closeness[component[0]] = 0.0
            continue
        
        # 创建子图
        subgraph = Graph(len(component))
        node_map = {component[i]: i for i in range(len(component))}
        
        for node in component:
            for neighbor in graph.neighbors(node):
                if neighbor in node_map:
                    subgraph.add_edge(node_map[node], node_map[neighbor])
        
        # 计算子图中的接近中心性
        subgraph_closeness = closeness_centrality_naive(subgraph, normalized=False)
        
        # 映射回原图
        for i, node in enumerate(component):
            closeness[node] = subgraph_closeness[i]
    
    return closeness


if __name__ == "__main__":
    print("=== 接近中心性算法测试 ===")
    
    # 创建测试图
    g = Graph(6)
    edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (3, 4), (4, 5)]
    for u, v in edges:
        g.add_edge(u, v)
    
    print("\n测试图:")
    print("   0 --- 1 --- 3 --- 4")
    print("    \\   /   \\   /")
    print("      2       5")
    
    # 计算接近中心性
    cc = closeness_centrality_naive(g, normalized=True)
    
    print("\n各节点接近中心性 (朴素算法):")
    for v, score in sorted(cc.items(), key=lambda x: x[1], reverse=True):
        print(f"  节点 {v}: {score:.4f}")
    
    # 调和中心性
    print("\n各节点调和中心性:")
    hc = harmonic_centrality(g)
    for v, score in sorted(hc.items(), key=lambda x: x[1], reverse=True):
        print(f"  节点 {v}: {score:.4f}")
    
    # 非连通图测试
    print("\n\n非连通图测试:")
    g_disconnected = Graph(7)
    # 第一个连通分量: 0-1-2
    g_disconnected.add_edge(0, 1)
    g_disconnected.add_edge(1, 2)
    # 第二个连通分量: 3-4-5-6
    g_disconnected.add_edge(3, 4)
    g_disconnected.add_edge(4, 5)
    g_disconnected.add_edge(5, 6)
    
    cc_disc = graph_components_closeness(g_disconnected)
    print("非连通图各节点接近中心性:")
    for v, score in sorted(cc_disc.items()):
        print(f"  节点 {v}: {score:.4f}")
    
    # 加权图测试
    print("\n\n加权图测试:")
    g_weighted = Graph(4)
    g_weighted.add_edge(0, 1)
    g_weighted.add_edge(1, 2)
    g_weighted.add_edge(2, 3)
    g_weighted.add_edge(0, 3)  # 长 detour
    
    weights = {(0, 1): 1, (1, 2): 10, (2, 3): 1, (0, 3): 5}
    
    cc_weighted = closeness_centrality_weighted(g_weighted, weights)
    print("加权图各节点接近中心性:")
    for v, score in sorted(cc_weighted.items()):
        print(f"  节点 {v}: {score:.4f}")
    
    print("\n=== 测试完成 ===")
