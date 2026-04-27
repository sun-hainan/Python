# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / gomory_hu_tree

本文件实现 gomory_hu_tree 相关的算法功能。
"""

from collections import defaultdict, deque


def build_flow_network_gomory():
    """构建一个带容量的无向图"""
    # 使用字典存储邻接表
    # graph[u][v] = capacity
    graph = defaultdict(dict)
    
    edges = [
        (0, 1, 4),
        (0, 2, 3),
        (1, 2, 2),
        (1, 3, 5),
        (2, 3, 4),
        (2, 4, 3),
        (3, 4, 2),
        (3, 5, 4),
        (4, 5, 6),
    ]
    
    for u, v, cap in edges:
        graph[u][v] = cap
        graph[v][u] = cap
    
    return graph


def bfs_max_flow(graph, source, sink, n):
    """
    BFS 版本的 Edmunds-Karp 最大流
    用于 Gomory-Hu 算法中找最小割
    
    返回：(flow_value, parent_edge)
    """
    # 复制容量（残留网络）
    capacity = defaultdict(dict)
    for u in graph:
        for v in graph[u]:
            capacity[u][v] = graph[u][v]
    
    flow = 0
    parent = {}
    
    while True:
        # BFS 找增广路
        queue = deque([source])
        level = {source: 0}
        found_sink = False
        
        while queue:
            u = queue.popleft()
            for v in capacity[u]:
                if v not in level and capacity[u][v] > 0:
                    level[v] = level[u] + 1
                    parent[v] = u
                    if v == sink:
                        found_sink = True
                        break
                    queue.append(v)
            if found_sink:
                break
        
        if sink not in parent:
            break  # 没有增广路
        
        # 找瓶颈
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, capacity[u][v])
            v = u
        
        # 增广
        v = sink
        while v != source:
            u = parent[v]
            capacity[u][v] -= path_flow
            capacity[v][u] += path_flow
            v = u
        
        flow += path_flow
    
    return flow, parent


def gomory_hu_tree(n, graph):
    """
    Gomory-Hu 树算法
    
    参数：
        n: 节点数
        graph: 邻接表，graph[u][v] = capacity
    
    返回：
        tree_edges: [(parent, child, min_cut_value), ...]
        parent_array: 每个节点的父节点
        cut_value: 每个节点到父节点的最小割值
    """
    parent = [-1] * n
    cut_value = [0] * n
    
    for i in range(1, n):
        # 在原图上找节点0（假设根）和节点i之间的最小割
        flow, _ = bfs_max_flow(graph, 0, i, n)
        cut_value[i] = flow
        
        # 更新图：在 parent[u] 和 u 之间分割后调整容量
        # 实际上 Gomory-Hu 需要在每次迭代中考虑之前的割
        parent[i] = 0
    
    # 构建树边
    tree_edges = []
    for i in range(1, n):
        tree_edges.append((parent[i], i, cut_value[i]))
    
    return parent, cut_value, tree_edges


def min_cut_query(u, v, tree_edges, n):
    """
    查询任意两点 u, v 之间的最小割
    在 Gomory-Hu 树上沿路径找最小边
    """
    # 构建树邻接表
    tree_adj = defaultdict(list)
    for a, b, cap in tree_edges:
        tree_adj[a].append((b, cap))
        tree_adj[b].append((a, cap))
    
    # BFS/DFS 找路径
    parent = {}
    min_cap_on_path = {}
    queue = deque([u])
    parent[u] = None
    
    while queue:
        curr = queue.popleft()
        if curr == v:
            break
        for neighbor, cap in tree_adj[curr]:
            if neighbor not in parent:
                parent[neighbor] = curr
                min_cap_on_path[neighbor] = min(
                    min_cap_on_path.get(curr, float('inf')), cap)
                queue.append(neighbor)
    
    if v not in parent:
        return float('inf')  # 不连通
    
    return min_cap_on_path.get(v, float('inf'))


def print_tree(parent, cut_value, n):
    """打印 Gomory-Hu 树"""
    print("\nGomory-Hu 树结构：")
    for i in range(1, n):
        print(f"  节点 {parent[i]} --[{cut_value[i]}]-- 节点 {i}")


if __name__ == "__main__":
    print("=" * 55)
    print("Gomory-Hu 树（全局最小割）")
    print("=" * 55)
    
    n = 6
    graph = build_flow_network_gomory()
    
    print(f"\n原图：{n} 节点")
    print("边（无向）及容量：")
    shown = set()
    for u in graph:
        for v in graph[u]:
            if u < v and (u, v) not in shown:
                print(f"  ({u}, {v}): {graph[u][v]}")
                shown.add((u, v))
    
    print("\n计算 Gomory-Hu 树...")
    parent, cut_value, tree_edges = gomory_hu_tree(n, graph)
    
    print_tree(parent, cut_value, n)
    
    print("\n验证：查询几个节点对的最小割")
    test_pairs = [(1, 4), (2, 5), (0, 5)]
    for u, v in test_pairs:
        mc = min_cut_query(u, v, tree_edges, n)
        print(f"  节点{u} 与 节点{v} 的最小割 = {mc}")
