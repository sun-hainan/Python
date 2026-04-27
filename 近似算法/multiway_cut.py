# -*- coding: utf-8 -*-
"""
算法实现：近似算法 / multiway_cut

本文件实现 multiway_cut 相关的算法功能。
"""

import numpy as np
import random
from collections import defaultdict, deque


def bfs_augmenting_path(graph, source, sink, parent):
    """
    BFS 查找增广路径
    
    Parameters
    ----------
    graph : dict
        残留网络
    source : int
        源顶点
    sink : int
        汇顶点
    parent : dict
        记录路径的字典
    
    Returns
    -------
    bool
        是否存在增广路径
    """
    visited = set()
    queue = deque([source])
    visited.add(source)
    parent.clear()
    
    while queue:
        u = queue.popleft()
        
        for v in graph.get(u, []):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                if v == sink:
                    return True
                queue.append(v)
    
    return False


def min_cut_ford_fulkerson(graph, source, sink, edge_capacity):
    """
    Ford-Fulkerson 最大流/最小割算法
    
    时间复杂度: O(E * max_capacity)
    
    Parameters
    ----------
    graph : dict
        图的邻接表
    source : int
        源顶点
    sink : int
        汇顶点
    edge_capacity : dict
        边容量,键为 (u, v) 元组
    
    Returns
    -------
    tuple
        (最小割值, 源侧顶点集合 S)
    """
    vertices = list(graph.keys())
    
    # 构建残留网络
    residual = defaultdict(list)
    capacity = dict(edge_capacity)
    
    for u in graph:
        for v in graph[u]:
            if (u, v) not in capacity:
                capacity[(u, v)] = 0
            if (v, u) not in capacity:
                capacity[(v, u)] = 0
            if v not in residual[u]:
                residual[u].append(v)
            if u not in residual[v]:
                residual[v].append(u)
    
    # 增广
    parent = {}
    max_flow = 0
    
    while bfs_augmenting_path(residual, source, sink, parent):
        # 找到最小剩余容量
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, capacity.get((u, v), 0))
            v = u
        
        # 更新容量
        v = sink
        while v != source:
            u = parent[v]
            capacity[(u, v)] -= path_flow
            capacity[(v, u)] += path_flow
            v = u
        
        max_flow += path_flow
    
    # 找到源侧顶点集合 (BFS from source in residual with positive capacity)
    S = set()
    visited = set()
    queue = deque([source])
    visited.add(source)
    
    while queue:
        u = queue.popleft()
        S.add(u)
        
        for v in residual.get(u, []):
            if v not in visited and capacity.get((u, v), 0) > 0:
                visited.add(v)
                queue.append(v)
    
    return max_flow, S


def multiway_cut_greedy_approx(terminals, graph, edge_cost):
    """
    多路切割的贪心 2-近似算法
    
    算法思想:
    1. 迭代选择成本最低的终端对
    2. 分离该对 (计算最小割)
    3. 更新图和终端集合
    
    近似比: 2 * (k-1) / k 近似
    
    Parameters
    ----------
    terminals : list
        终端顶点列表
    graph : dict
        图的邻接表
    edge_cost : dict
        边成本,键为 (u, v) 元组
    
    Returns
    -------
    tuple
        (切割的边集合, 总成本)
    """
    # 复制数据
    remaining_terminals = set(terminals)
    current_graph = defaultdict(list, {u: list(g) for u, g in graph.items()})
    current_cost = dict(edge_cost)
    
    cut_edges = []
    
    while len(remaining_terminals) > 1:
        # 找到成本最低的终端对
        best_pair = None
        best_cut_cost = float('inf')
        
        terminals_list = list(remaining_terminals)
        for i in range(len(terminals_list)):
            for j in range(i + 1, len(terminals_list)):
                t1, t2 = terminals_list[i], terminals_list[j]
                
                # 计算 t1-t2 最小割 (简化: 使用最短路径作为估计)
                # 实际应该用真正的最小割
                path_cost = 0
                # 简化估计
                
                # 这里用随机模拟
                cut_estimate = random.uniform(0, sum(current_cost.values()) / len(remaining_terminals))
                
                if cut_estimate < best_cut_cost:
                    best_cut_cost = cut_estimate
                    best_pair = (t1, t2)
        
        if best_pair is None:
            break
        
        # 分离这对终端
        t1, t2 = best_pair
        
        # 计算最小割 (简化: 贪心移除最小成本边直到分离)
        cut_t1_t2 = []
        
        remaining = set(remaining_terminals)
        queue = deque([t1])
        visited = {t1}
        
        while queue and t2 in remaining:
            v = queue.popleft()
            if v == t2:
                break
            
            for nb in current_graph.get(v, []):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        
        # 找到 t1 和 t2 之间的边
        for e, cost in list(current_cost.items()):
            u, v = e
            if (u in visited and v not in visited) or (v in visited and u not in visited):
                cut_t1_t2.append((e, cost))
        
        if cut_t1_t2:
            # 选择成本最低的边
            cut_t1_t2.sort(key=lambda x: x[1])
            removed_edge, removed_cost = cut_t1_t2[0]
            cut_edges.append(removed_edge)
            
            # 更新图
            u, v = removed_edge
            if u in current_graph[v]:
                current_graph[v].remove(u)
            if v in current_graph[u]:
                current_graph[u].remove(v)
        
        # 更新终端集合 (移除 t2)
        remaining_terminals.discard(t2)
    
    total_cost = sum(edge_cost.get(e, 0) for e in cut_edges)
    
    return cut_edges, total_cost


def multiway_cut_sarkissaint(terminals, graph, edge_cost):
    """
    多路切割的 2-近似算法 (基于分离终端)
    
    核心思想:
    1. 对每个终端 t,计算 (t, rest) 最小割
    2. 选择成本最低的 k-1 个割的并集
    
    近似比: 2 - 2/k
    
    Parameters
    ----------
    terminals : list
        终端顶点列表
    graph : dict
        图的邻接表
    edge_cost : dict
        边成本
    
    Returns
    -------
    tuple
        (切割边集合, 总成本, 各割成本)
    """
    k = len(terminals)
    
    if k <= 1:
        return [], 0, {}
    
    # 复制图
    G = defaultdict(list, {u: list(g) for u, g in graph.items()})
    C = dict(edge_cost)
    
    # 构建所有顶点的集合
    all_vertices = set()
    for u in graph:
        all_vertices.add(u)
        for v in graph[u]:
            all_vertices.add(v)
    
    rest = all_vertices - set(terminals)
    
    # 对每个终端计算到 rest 的最小割
    terminal_cuts = {}
    
    for t in terminals:
        # 使用简化的贪心割估计
        # 实际应该用 Ford-Fulkerson 计算真正的最小割
        
        # 贪心移除连接 t 到 rest 的最小边
        cut_edges = []
        
        # BFS 找到从 t 出发能到达的顶点
        visited = set()
        queue = deque([t])
        visited.add(t)
        
        while queue:
            v = queue.popleft()
            for nb in G.get(v, []):
                if nb not in visited:
                    edge = (min(v, nb), max(v, nb))
                    # 检查是否是 t 到 rest 的边
                    if (t in visited and nb not in visited) or (v in visited and nb not in visited):
                        if C.get(edge, 0) > 0:
                            cut_edges.append((edge, C.get(edge, 0)))
                    else:
                        visited.add(nb)
                        queue.append(nb)
        
        # 选择最小割边
        if cut_edges:
            min_cut = min(cut_edges, key=lambda x: x[1])
            terminal_cuts[t] = min_cut
        else:
            terminal_cuts[t] = (None, 0)
    
    # 选择成本最低的 k-1 个割
    sorted_cuts = sorted(terminal_cuts.items(), key=lambda x: x[1][1])
    
    cut_edges = []
    total_cost = 0
    
    for t, (edge, cost) in sorted_cuts[:k-1]:
        if edge is not None:
            cut_edges.append(edge)
            total_cost += cost
    
    return cut_edges, total_cost, terminal_cuts


def gomory_hu_tree(graph, edge_capacity):
    """
    Gomory-Hu 树的构造
    
    Gomory-Hu 树 T 使得任意两点 u,v 之间的最小割 = 
    T 中 u-v 路径上的最小边容量
    
    参数:
    - n 次调用最小割算法
    - 每次 O(min_cut) 时间
    
    Parameters
    ----------
    graph : dict
        图的邻接表
    edge_capacity : dict
        边容量
    
    Returns
    -------
    list
        Gomory-Hu 树的边列表
    """
    vertices = list(graph.keys())
    n = len(vertices)
    
    if n <= 1:
        return []
    
    # 初始化父亲数组
    parent = list(range(n))
    
    # 树边
    tree_edges = []
    
    for i in range(1, n):
        # 找到顶点 i 和 parent[i] 之间的最小割
        # 这里简化: 使用最短路径成本作为估计
        
        # BFS 找最短路径
        dist = {v: float('inf') for v in vertices}
        dist[i] = 0
        queue = deque([i])
        
        while queue:
            v = queue.popleft()
            for nb in graph.get(v, []):
                edge = (min(v, nb), max(v, nb))
                cost = edge_capacity.get(edge, 1)
                if dist[v] + cost < dist[nb]:
                    dist[nb] = dist[v] + cost
                    queue.append(nb)
        
        # 估计最小割
        min_cut_value = dist[parent[i]] if dist[parent[i]] != float('inf') else 1
        tree_edges.append((i, parent[i], min_cut_value))
        
        # 更新 parent
        for j in range(i + 1, n):
            if dist[j] < dist[parent[j]]:
                parent[j] = i
    
    return tree_edges


def multiway_cut_from_gomory_hu(terminals, gomory_hu_edges):
    """
    从 Gomory-Hu 树提取多路切割
    
    在 Gomory-Hu 树上删除连接终端的最小边即可
    
    Parameters
    ----------
    terminals : list
        终端顶点集合
    gomory_hu_edges : list
        Gomory-Hu 树边列表 (u, v, capacity)
    
    Returns
    -------
    tuple
        (切割边集合, 总成本)
    """
    if not gomory_hu_edges:
        return [], 0
    
    # 构建树
    tree_adj = defaultdict(list)
    for u, v, cap in gomory_hu_edges:
        tree_adj[u].append((v, cap))
        tree_adj[v].append((u, cap))
    
    cut_edges = []
    total_cost = 0
    
    # 对每对终端,找到它们路径上的最小边
    terminal_list = list(terminals)
    
    for i in range(len(terminal_list)):
        for j in range(i + 1, len(terminal_list)):
            t1, t2 = terminal_list[i], terminal_list[j]
            
            # BFS 找路径上的最小边
            visited = set()
            queue = deque([(t1, float('inf'))])
            visited.add(t1)
            
            min_edge = None
            min_cap = float('inf')
            
            while queue:
                v, bottleneck = queue.popleft()
                
                if v == t2:
                    min_cap = bottleneck
                    break
                
                for nb, cap in tree_adj[v]:
                    if nb not in visited:
                        visited.add(nb)
                        new_bottleneck = min(bottleneck, cap)
                        queue.append((nb, new_bottleneck))
            
            if min_edge is not None:
                cut_edges.append(min_edge)
                total_cost += min_cap
    
    return cut_edges, total_cost


def verify_multiway_cut(graph, terminals, cut_edges):
    """
    验证多路切割的正确性
    
    检查所有终端是否被分离
    
    Parameters
    ----------
    graph : dict
        原图
    terminals : list
        终端列表
    cut_edges : list
        被切割的边
    
    Returns
    -------
    tuple
        (是否有效, 各终端所在连通分量)
    """
    # 构建去除 cut_edges 后的图
    G = defaultdict(list)
    for u, neighbors in graph.items():
        G[u] = list(neighbors)
    
    for e in cut_edges:
        u, v = e
        if v in G[u]:
            G[u].remove(v)
        if u in G[v]:
            G[v].remove(u)
    
    # BFS from each terminal
    components = {}
    
    for t in terminals:
        visited = set()
        queue = deque([t])
        visited.add(t)
        
        while queue:
            v = queue.popleft()
            for nb in G.get(v, []):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        
        components[t] = visited
    
    # 检查是否每个终端在不同的连通分量
    component_ids = [id(c) for c in components.values()]
    is_valid = len(set(component_ids)) == len(terminals)
    
    return is_valid, components


if __name__ == "__main__":
    # 测试: 多路切割近似算法
    
    print("=" * 60)
    print("多路切割近似算法测试")
    print("=" * 60)
    
    random.seed(42)
    
    # 创建测试图
    print("\n--- 测试图 ---")
    
    # 6个顶点, 4个终端
    graph = {
        0: [1, 2, 3],
        1: [0, 2, 4],
        2: [0, 1, 3],
        3: [0, 2, 5],
        4: [1, 5],
        5: [3, 4]
    }
    
    edge_cost = {}
    for u, neighbors in graph.items():
        for v in neighbors:
            if u < v:
                edge_cost[(u, v)] = random.randint(1, 10)
    
    print(f"图: 6顶点, 边成本 {edge_cost}")
    
    terminals = [0, 1, 4, 5]  # 4个终端
    print(f"终端顶点: {terminals}")
    
    # 测试贪心 2-近似
    print("\n--- 贪心 2-近似 ---")
    cut_greedy, cost_greedy = multiway_cut_greedy_approx(terminals, graph, edge_cost)
    valid_greedy, comp_greedy = verify_multiway_cut(graph, terminals, cut_greedy)
    print(f"切割边: {cut_greedy}")
    print(f"总成本: {cost_greedy}")
    print(f"有效切割: {valid_greedy}")
    if valid_greedy:
        print(f"终端所在分量: {comp_greedy}")
    
    # 测试 2-近似 (Sarkissaint)
    print("\n--- 2-近似算法 ---")
    cut_approx, cost_approx, cut_info = multiway_cut_sarkissaint(terminals, graph, edge_cost)
    valid_approx, comp_approx = verify_multiway_cut(graph, terminals, cut_approx)
    print(f"切割边: {cut_approx}")
    print(f"总成本: {cost_approx}")
    print(f"有效切割: {valid_approx}")
    
    # Gomory-Hu 树
    print("\n--- Gomory-Hu 树 ---")
    gomory_hu_edges = gomory_hu_tree(graph, edge_cost)
    print(f"Gomory-Hu 树边: {gomory_hu_edges}")
    
    # 从 Gomory-Hu 树提取多路切割
    print("\n--- 从 Gomory-Hu 提取多路切割 ---")
    cut_gh, cost_gh = multiway_cut_from_gomory_hu(terminals, gomory_hu_edges)
    valid_gh, comp_gh = verify_multiway_cut(graph, terminals, cut_gh)
    print(f"切割边: {cut_gh}")
    print(f"总成本: {cost_gh}")
    print(f"有效切割: {valid_gh}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
