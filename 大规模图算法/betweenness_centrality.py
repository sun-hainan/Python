"""
介数中心性算法 (Betweenness Centrality)
=======================================
计算图中每个节点的介数中心性：经过该节点的最短路径数量占比。

介数中心性衡量一个节点在图中作为"桥梁"的重要程度。

使用Brandes算法实现，时间复杂度O(nm)。

参考：
    - Freeman, L.C. (1977). A set of measures of centrality based on betweenness.
    - Brandes, U. (2001). A faster algorithm for betweenness centrality.
"""

from typing import List, Dict, Set, Tuple
from collections import deque
import math


class Graph:
    """无向加权图数据结构"""
    
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [[] for _ in range(n)]  # adj[u] = [(v, weight), ...]
        self.weights = {}  # (u,v) -> weight
    
    def add_edge(self, u: int, v: int, weight: float = 1.0):
        """添加边"""
        self.adj[u].append((v, weight))
        self.adj[v].append((u, weight))
        self.weights[(min(u, v), max(u, v))] = weight
    
    def neighbors(self, u: int) -> List[Tuple[int, float]]:
        """返回邻居列表及权重"""
        return self.adj[u]
    
    def get_weight(self, u: int, v: int) -> float:
        """获取边权重"""
        key = (min(u, v), max(u, v))
        return self.weights.get(key, 1.0)


def brandes_betweenness_single_source(graph: Graph, source: int) -> Tuple[Dict[int, float], Dict[int, List[int]]]:
    """
    Brandes算法：从单个源节点计算对所有其他节点的依赖性
    
    参数:
        graph: 输入图
        source: 源节点
    
    返回:
        (delta: 每个节点的依赖值, predecessors: 前驱节点)
    """
    n = graph.n
    
    # 初始化
    S = []  # 栈：按BFS顺序存储节点
    P = {v: [] for v in range(n)}  # 前驱列表
    sigma = {v: 0 for v in range(n)}  # 最短路径数
    d = {v: math.inf for v in range(n)}  # 距离
    
    sigma[source] = 1
    d[source] = 0
    
    # BFS
    queue = deque([source])
    
    while queue:
        v = queue.popleft()
        S.append(v)
        
        for w, weight in graph.neighbors(v):
            # w第一次被发现
            if d[w] == math.inf:
                d[w] = d[v] + 1
                queue.append(w)
            
            # 最短路径更新
            if d[w] == d[v] + 1:
                sigma[w] += sigma[v]
                P[w].append(v)
    
    # 计算依赖性
    delta = {v: 0.0 for v in range(n)}
    
    while S:
        w = S.pop()
        for v in P[w]:
            # 计算v对w的依赖贡献
            sigma_v = sigma[v]
            sigma_w = sigma[w] if sigma[w] > 0 else 1
            delta[v] += (sigma_v / sigma_w) * (1 + delta[w])
    
    return delta, P


def betweenness_centrality(graph: Graph, normalized: bool = True) -> Dict[int, float]:
    """
    计算所有节点的介数中心性（Brandes算法）
    
    参数:
        graph: 输入图
        normalized: 是否归一化
    
    返回:
        节点 -> 介数中心性 的字典
    """
    n = graph.n
    
    if n == 0:
        return {}
    
    betweenness = {v: 0.0 for v in range(n)}
    
    # 对每个源节点运行SSSP
    for s in range(n):
        delta, _ = brandes_betweenness_single_source(graph, s)
        for v in range(n):
            betweenness[v] += delta[v]
    
    # 归一化
    if normalized:
        # 对于无向图，归一化因子是 (n-1)*(n-2)/2
        norm_factor = 2.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
        for v in range(n):
            betweenness[v] *= norm_factor
    
    return betweenness


def brandes_accelerated(graph: Graph, sources: List[int]) -> Dict[int, float]:
    """
    加速版Brandes：只从部分源节点计算
    
    用于大规模图的近似介数中心性
    
    参数:
        graph: 输入图
        sources: 源节点列表
    
    返回:
        近似的介数中心性
    """
    n = graph.n
    betweenness = {v: 0.0 for v in range(n)}
    
    for s in sources:
        delta, _ = brandes_betweenness_single_source(graph, s)
        for v in range(n):
            betweenness[v] += delta[v]
    
    # 归一化（考虑采样的源节点数量）
    if len(sources) < n:
        factor = (n - 1) / len(sources)
        for v in range(n):
            betweenness[v] *= factor
    
    return betweenness


def approximated_betweenness_centrality(graph: Graph, k: int, 
                                        seed: int = 42) -> Dict[int, float]:
    """
    近似介数中心性：随机采样k个源节点
    
    参数:
        graph: 输入图
        k: 采样数量
        seed: 随机种子
    
    返回:
        近似的介数中心性
    """
    import random
    random.seed(seed)
    
    n = graph.n
    sources = random.sample(range(n), min(k, n))
    
    return brandes_accelerated(graph, sources)


def betweenness_centrality_directed(graph: 'DirectedGraph', 
                                    normalized: bool = True) -> Dict[int, float]:
    """
    有向图的介数中心性
    
    参数:
        graph: 有向图
        normalized: 是否归一化
    
    返回:
        节点 -> 介数中心性
    """
    n = graph.n
    
    betweenness = {v: 0.0 for v in range(n)}
    
    for s in range(n):
        # BFS from source
        sigma = {v: 0 for v in range(n)}
        d = {v: math.inf for v in range(n)}
        P = {v: [] for v in range(n)}
        
        sigma[s] = 1
        d[s] = 0
        
        queue = deque([s])
        
        while queue:
            v = queue.popleft()
            
            for w in graph.successors(v):
                if d[w] == math.inf:
                    d[w] = d[v] + 1
                    queue.append(w)
                
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]
                    P[w].append(v)
        
        # 计算依赖性
        delta = {v: 0.0 for v in range(n)}
        
        # 按距离降序处理
        nodes_by_dist = sorted([v for v in range(n) if d[v] != math.inf], key=lambda x: d[x], reverse=True)
        
        for w in nodes_by_dist:
            for v in P[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
        
        for v in range(n):
            betweenness[v] += delta[v]
    
    if normalized:
        norm_factor = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
        for v in range(n):
            betweenness[v] *= norm_factor
    
    return betweenness


class DirectedGraph:
    """有向图数据结构"""
    
    def __init__(self, n: int = 0):
        self.n = n
        self.succ = [[] for _ in range(n)]  # 后继
        self.pred = [[] for _ in range(n)]  # 前驱
    
    def add_edge(self, u: int, v: int):
        """添加有向边 u -> v"""
        self.succ[u].append(v)
        self.pred[v].append(u)
    
    def successors(self, u: int) -> List[int]:
        """返回后继节点"""
        return self.succ[u]
    
    def predecessors(self, u: int) -> List[int]:
        """返回前驱节点"""
        return self.pred[u]


def edge_betweenness_centrality(graph: Graph) -> Dict[Tuple[int, int], float]:
    """
    计算边的介数中心性
    
    参数:
        graph: 无向图
    
    返回:
        边 -> 介数中心性
    """
    n = graph.n
    edge_betweenness = {}
    
    for s in range(n):
        delta, P = brandes_betweenness_single_source(graph, s)
        
        # 收集边的依赖
        edge_delta = {e: 0.0 for e in graph.weights.keys()}
        
        # 按距离降序处理
        S = []  # 栈
        queue = deque([s])
        d = {v: math.inf for v in range(n)}
        d[s] = 0
        
        while queue:
            v = queue.popleft()
            S.append(v)
            for w, _ in graph.neighbors(v):
                if d[w] == math.inf:
                    d[w] = d[v] + 1
                    queue.append(w)
        
        while S:
            w = S.pop()
            for v in P[w]:
                # 边 (v, w)
                key = (min(v, w), max(v, w))
                sigma_v = 1  # 简化处理
                sigma_w = 1
                
                edge_delta[key] += 1 + delta[w]
        
        for e, val in edge_delta.items():
            edge_betweenness[e] = edge_betweenness.get(e, 0) + val
    
    # 归一化
    norm = 2.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    for e in edge_betweenness:
        edge_betweenness[e] *= norm
    
    return edge_betweenness


if __name__ == "__main__":
    print("=== 介数中心性算法测试 ===")
    
    # 创建测试图
    g = Graph(6)
    edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (3, 4), (4, 5)]
    for u, v in edges:
        g.add_edge(u, v)
    
    print("\n测试图:")
    print("   0 --- 1 --- 3 --- 4")
    print("    \\   /   \\   /")
    print("      2       5")
    
    # 计算介数中心性
    bc = betweenness_centrality(g, normalized=True)
    
    print("\n各节点介数中心性:")
    for v, score in sorted(bc.items()):
        print(f"  节点 {v}: {score:.4f}")
    
    # 近似介数中心性
    print("\n近似介数中心性 (k=3):")
    bc_approx = approximated_betweenness_centrality(g, k=3)
    for v, score in sorted(bc_approx.items()):
        print(f"  节点 {v}: {score:.4f}")
    
    # 边介数中心性
    print("\n边介数中心性:")
    edge_bc = edge_betweenness_centrality(g)
    for (u, v), score in sorted(edge_bc.items(), key=lambda x: x[1], reverse=True):
        print(f"  边 ({u}, {v}): {score:.4f}")
    
    # 有向图测试
    print("\n\n有向图测试:")
    dg = DirectedGraph(4)
    dg.add_edge(0, 1)
    dg.add_edge(0, 2)
    dg.add_edge(1, 2)
    dg.add_edge(2, 3)
    dg.add_edge(3, 1)
    
    bc_directed = betweenness_centrality_directed(dg, normalized=True)
    print("有向图各节点介数中心性:")
    for v, score in sorted(bc_directed.items()):
        print(f"  节点 {v}: {score:.4f}")
    
    print("\n=== 测试完成 ===")
