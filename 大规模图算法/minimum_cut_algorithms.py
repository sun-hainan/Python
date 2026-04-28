"""
最小割算法 (Minimum Cut Algorithms)
====================================
实现Stoer-Wagner算法求无向图的全局最小割。

最小割：将图分成两个不相交集合S和T，使得割集（跨越S和T的边）的总权重最小。

Stoer-Wagner算法：使用最大邻接树(MST)思想，O(nm log n)时间复杂度。

参考：
    - Stoer, M. & Wagner, F. (1997). A simple min-cut algorithm.
    - Nagamochi, H. & Ibaraki, T. (1992). Computing edge-connectivity in O(nm).
"""

from typing import List, Dict, Set, Tuple, Optional
import math
import heapq


class WeightedGraph:
    """带权无向图"""
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [[] for _ in range(n)]  # adj[u] = [(v, weight), ...]
        self.weights = {}  # (min, max) -> weight
    
    def add_edge(self, u: int, v: int, weight: float = 1.0):
        self.adj[u].append((v, weight))
        self.adj[v].append((u, weight))
        key = (min(u, v), max(u, v))
        self.weights[key] = weight
    
    def get_weight(self, u: int, v: int) -> float:
        key = (min(u, v), max(u, v))
        return self.weights.get(key, 0.0)
    
    def neighbors(self, u: int) -> List[Tuple[int, float]]:
        return self.adj[u]


def contract_edge(graph: WeightedGraph, u: int, v: int) -> Tuple[WeightedGraph, float]:
    """
    收缩边(u, v)，合并v到u
    
    参数:
        graph: 输入图
        u, v: 要收缩的边端点
    
    返回:
        (收缩后的图, 收缩边的权重)
    """
    # 创建新图
    n = graph.n - 1
    new_graph = WeightedGraph(n)
    
    # 旧节点到新节点的映射
    # u被保留，v被删除，v的邻居都映射到u
    old_to_new = {}
    new_idx = 0
    for i in range(graph.n):
        if i == v:
            old_to_new[i] = u  # v映射到u
        else:
            old_to_new[i] = new_idx
            new_idx += 1
    
    # 添加边（跳过v）
    edge_weights = {}
    for i in range(graph.n):
        if i == v:
            continue
        for j, w in graph.adj[i]:
            if j == v:
                continue
            ni, nj = old_to_new[i], old_to_new[j]
            key = (min(ni, nj), max(ni, nj))
            edge_weights[key] = edge_weights.get(key, 0.0) + w
    
    # 构建新图
    for key, w in edge_weights.items():
        u_new, v_new = key
        new_graph.add_edge(u_new, v_new, w)
    
    # 获取收缩边的权重
    contracted_weight = graph.get_weight(u, v)
    
    return new_graph, contracted_weight


def maximum_adjacency_search(graph: WeightedGraph) -> Tuple[List[int], float]:
    """
    最大邻接搜索 (Maximum Adjacency Search)
    
    按最大"累积权重"顺序选择节点
    
    参数:
        graph: 带权图
    
    返回:
        (节点顺序, 最后加入节点对的最小割值)
    """
    n = graph.n
    
    if n == 0:
        return [], 0.0
    if n == 1:
        return [0], 0.0
    
    # 每个节点的累积权重
    acoeff = [0.0] * n
    # 是否已访问
    visited = [False] * n
    # 顺序
    order = []
    
    # 初始化：选择节点0作为起始
    current = 0
    visited[current] = True
    order.append(current)
    
    for _ in range(n - 1):
        # 更新邻居的acoeff
        for neighbor, weight in graph.adj[current]:
            if not visited[neighbor]:
                acoeff[neighbor] += weight
        
        # 选择未访问的、acoeff最大的节点
        max_a = -1
        next_node = -1
        for i in range(n):
            if not visited[i] and acoeff[i] > max_a:
                max_a = acoeff[i]
                next_node = i
        
        if next_node == -1:
            # 图可能不连通，选择下一个未访问节点
            for i in range(n):
                if not visited[i]:
                    next_node = i
                    break
        
        if next_node == -1:
            break
        
        visited[next_node] = True
        order.append(next_node)
        current = next_node
    
    # 最后加入的节点对(order[-2], order[-1])的acoeff值是这次搜索的最小割
    if len(order) >= 2:
        last = order[-1]
        second_last = order[-2]
        # acoeff[last] 包含了所有与last相连的边的权重
        cut_value = acoeff[last]
    else:
        cut_value = 0.0
    
    return order, cut_value


def stoer_wagner_min_cut(graph: WeightedGraph) -> Tuple[float, List[Set[int]]]:
    """
    Stoer-Wagner算法求全局最小割
    
    参数:
        graph: 带权无向图
    
    返回:
        (最小割值, 最小割划分的两个集合)
    """
    n = graph.n
    
    if n == 0:
        return 0.0, [set(), set()]
    if n == 1:
        return 0.0, [set([0]), set()]
    
    # 当前图
    current_graph = graph
    current_n = n
    
    # 全局最优
    best_cut = float('inf')
    best_partition = (set(range(n)), set())
    
    # 节点映射
    node_map = list(range(n))  # current_graph的节点i对应原图的node_map[i]
    
    while current_n > 1:
        # 执行一次最大邻接搜索
        order, cut_value = maximum_adjacency_search(current_graph)
        
        # 更新全局最小割
        if cut_value < best_cut:
            # 分割：order[-1] vs 其他
            s_set = {node_map[order[-1]]}
            t_set = set(node_map[i] for i in order[:-1])
            best_cut = cut_value
            best_partition = (s_set, t_set)
        
        # 收缩 order[-2] 和 order[-1]
        u = order[-2]
        v = order[-1]
        
        # 收缩边
        new_graph, contracted_weight = contract_edge(current_graph, u, v)
        
        # 更新节点映射
        # u保留（但索引变成u），v被删除
        new_node_map = []
        for i, old_node in enumerate(node_map):
            if i == v:
                continue  # v被合并到u
            if i == u:
                new_node_map.append(old_node)  # u保留
            else:
                new_idx = len(new_node_map)
                new_node_map.append(old_node)
        
        current_graph = new_graph
        node_map = new_node_map
        current_n -= 1
    
    return best_cut, best_partition


def kargers_min_cut(graph: WeightedGraph, num_iterations: int = None) -> Tuple[float, Set[Tuple[int, int]]]:
    """
    Karger算法（随机化最小割）
    
    参数:
        graph: 带权图
        num_iterations: 迭代次数（默认 n^2）
    
    返回:
        (最小割估计值, 割集边集合)
    """
    n = graph.n
    
    if num_iterations is None:
        num_iterations = n * n
    
    best_cut = float('inf')
    best_cut_set = set()
    
    for _ in range(num_iterations):
        # 复制图
        import copy
        g = WeightedGraph(n)
        for (u, v), w in graph.weights.items():
            g.add_edge(u, v, w)
        
        # 当前节点数
        current_n = n
        
        # 当还有超过2个节点时，随机收缩边
        while current_n > 2:
            # 选择一条随机边
            edges = list(g.weights.keys())
            if not edges:
                break
            u, v = random.choice(edges)
            
            # 收缩
            new_n = current_n - 1
            new_g = WeightedGraph(new_n)
            
            # 旧到新的节点映射
            old_to_new = {}
            new_idx = 0
            for i in range(g.n):
                if i == v:
                    old_to_new[i] = u
                else:
                    old_to_new[i] = new_idx
                    new_idx += 1
            
            # 累加边权重
            edge_weights = {}
            for (i, j), w in g.weights.items():
                if i == v or j == v:
                    continue
                ni, nj = old_to_new[i], old_to_new[j]
                key = (min(ni, nj), max(ni, nj))
                edge_weights[key] = edge_weights.get(key, 0.0) + w
            
            for (ni, nj), w in edge_weights.items():
                new_g.add_edge(ni, nj, w)
            
            g = new_g
            current_n = new_n
        
        # 现在g有2个节点，计算割值
        cut_value = 0.0
        cut_set = set()
        for (u, v), w in g.weights.items():
            cut_value += w
            cut_set.add((u, v))
        
        if cut_value < best_cut:
            best_cut = cut_value
            best_cut_set = cut_set
    
    return best_cut, best_cut_set


import random


def edmonds_karp_max_flow(capacity_graph: 'CapacityGraph', 
                          source: int, sink: int) -> Tuple[float, Dict[Tuple[int, int], float]]:
    """
    Edmonds-Karp算法（EK最大流 = 最小割）
    
    参数:
        capacity_graph: 容量图
        source: 源节点
        sink: 汇节点
    
    返回:
        (最大流值, 流量分配)
    """
    n = capacity_graph.n
    
    # 残量图
    capacity = [row[:] for row in capacity_graph.capacity]
    flow = [[0.0] * n for _ in range(n)]
    
    max_flow = 0.0
    
    while True:
        # BFS找增广路径
        parent = [-1] * n
        parent[source] = source
        
        queue = [source]
        while queue and parent[sink] == -1:
            u = queue.pop(0)
            for v in range(n):
                if parent[v] == -1 and capacity[u][v] - flow[u][v] > 0:
                    parent[v] = u
                    queue.append(v)
        
        if parent[sink] == -1:
            break  # 没有增广路径
        
        # 找瓶颈
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, capacity[u][v] - flow[u][v])
            v = u
        
        # 更新流量
        v = sink
        while v != source:
            u = parent[v]
            flow[u][v] += path_flow
            flow[v][u] -= path_flow
            v = u
        
        max_flow += path_flow
    
    return max_flow, {}


class CapacityGraph:
    """容量图（用于最大流）"""
    def __init__(self, n: int = 0):
        self.n = n
        self.capacity = [[0.0] * n for _ in range(n)]
    
    def add_edge(self, u: int, v: int, cap: float):
        self.capacity[u][v] = cap


def minimum_cut_by_max_flow(graph: WeightedGraph, source: int = 0) -> Tuple[float, Set[int]]:
    """
    通过最大流求最小割（s-t最小割）
    
    参数:
        graph: 带权图
        source: 源节点
    
    返回:
        (s-t最小割值, S集合)
    """
    n = graph.n
    
    # 构建容量图
    cap_graph = CapacityGraph(n)
    for (u, v), w in graph.weights.items():
        cap_graph.capacity[u][v] = w
        cap_graph.capacity[v][u] = w  # 对偶边
    
    # 对每个可能的汇点求最大流
    best_cut = float('inf')
    best_s_set = set()
    
    for sink in range(1, n):
        max_flow, _ = edmonds_karp_max_flow(cap_graph, source, sink)
        if max_flow < best_cut:
            best_cut = max_flow
            # BFS找S集合（从source可达且残量>0）
            residual = [[cap_graph.capacity[u][v] for v in range(n)] for u in range(n)]
            # 简化处理
    
    return best_cut, best_s_set


if __name__ == "__main__":
    print("=== 最小割算法测试 ===")
    
    # 测试图1: 简单例子
    #     2
    #    /|\
    #   1 | 1
    #  / \|/\
    # 0---3---4
    #     |  |
    #     2  3
    g1 = WeightedGraph(5)
    g1.add_edge(0, 1, 1)
    g1.add_edge(0, 3, 2)
    g1.add_edge(1, 2, 2)
    g1.add_edge(1, 3, 1)
    g1.add_edge(2, 4, 3)
    g1.add_edge(3, 4, 2)
    
    print("\n测试图1: 5节点带权图")
    min_cut, partition = stoer_wagner_min_cut(g1)
    print(f"Stoer-Wagner 最小割: {min_cut}")
    print(f"划分: S={partition[0]}, T={partition[1]}")
    
    # Karger算法
    karger_cut, _ = kargers_min_cut(g1, 100)
    print(f"Karger 最小割估计: {karger_cut}")
    
    # 测试图2: 完全图 K4
    print("\n\n完全图 K4:")
    g2 = WeightedGraph(4)
    for i in range(4):
        for j in range(i + 1, 4):
            g2.add_edge(i, j, 1)
    
    min_cut2, _ = stoer_wagner_min_cut(g2)
    print(f"最小割: {min_cut2}")  # 期望是3（每个节点连出去3条边，选中的割集有3条边）
    
    # 测试图3: 树（最小割为最小边权重）
    print("\n\n树图:")
    g3 = WeightedGraph(4)
    g3.add_edge(0, 1, 3)
    g3.add_edge(1, 2, 5)
    g3.add_edge(1, 3, 2)
    
    min_cut3, partition3 = stoer_wagner_min_cut(g3)
    print(f"最小割: {min_cut3}")
    print(f"划分: {partition3}")
    
    # 测试图4: 验证最大邻接搜索
    print("\n\n验证最大邻接搜索:")
    order, cut_val = maximum_adjacency_search(g1)
    print(f"顺序: {order}")
    print(f"这次搜索的cut值: {cut_val}")
    
    print("\n=== 测试完成 ===")
