# -*- coding: utf-8 -*-
"""
算法实现：06_网络流与匹配 / primal_dual_flow

本文件实现 primal_dual_flow 相关的算法功能。
"""

from collections import deque
import heapq


def build_primal_dual_network():
    """构建一个测试网络"""
    # 使用字典存储邻接表
    graph = {}
    edges = {}
    
    # 节点列表
    nodes = [0, 1, 2, 3, 4]
    
    def add_edge(frm, to, cap, cost):
        if frm not in graph:
            graph[frm] = []
        if to not in graph:
            graph[to] = []
        idx = len(edges)
        edges[idx] = {'from': frm, 'to': to, 'cap': cap, 'cost': cost, 'flow': 0}
        graph[frm].append(idx)
        # 反向边
        rev_idx = len(edges)
        edges[rev_idx] = {'from': to, 'to': frm, 'cap': 0, 'cost': -cost, 'flow': 0}
        graph[to].append(rev_idx)
    
    # 源点0，汇点4
    add_edge(0, 1, 5, 3)
    add_edge(0, 2, 4, 2)
    add_edge(1, 2, 2, 1)
    add_edge(1, 3, 3, 2)
    add_edge(2, 3, 4, 3)
    add_edge(2, 4, 2, 4)
    add_edge(3, 4, 6, 1)
    
    return graph, edges, nodes


def dijkstra_reduced_cost(graph, edges, n, source, potentials):
    """
    使用 Dijkstra + reduced cost 找最短路
    reduced_cost(e) = cost(e) + pi(u) - pi(v)
    """
    INF = float('inf')
    dist = [INF] * n
    parent = [-1] * n  # (prev_node, edge_idx)
    visited = [False] * n
    
    dist[source] = 0
    
    # 使用最小堆
    pq = [(0, source)]
    
    while pq:
        d, u = heapq.heappop(pq)
        if visited[u]:
            continue
        visited[u] = True
        
        if u not in graph:
            continue
            
        for edge_idx in graph[u]:
            edge = edges[edge_idx]
            v = edge['to']
            
            if edge['cap'] > 0 and not visited[v]:
                # 计算 reduced cost
                rcost = edge['cost'] + potentials[u] - potentials[v]
                nd = d + rcost
                if nd < dist[v]:
                    dist[v] = nd
                    parent[v] = (u, edge_idx)
                    heapq.heappush(pq, (nd, v))
    
    return dist, parent


def primal_dual_min_cost_flow(graph, edges, n, source, sink, demand):
    """
    原始对偶算法求解最小费用流
    
    参数：
        graph: 邻接表（边索引列表）
        edges: 边信息字典
        n: 节点数
        source: 源
        sink: 汇
        demand: 目标流量
    
    返回：(total_flow, total_cost)
    """
    total_flow = 0
    total_cost = 0
    
    # 初始化势（node potentials）
    potentials = [0] * n
    
    iteration = 0
    while total_flow < demand:
        iteration += 1
        
        # Step 1: 使用当前势找最短增广路
        dist, parent = dijkstra_reduced_cost(graph, edges, n, source, potentials)
        
        if parent[sink] == -1:
            print(f"  无法找到增广路（已输送 {total_flow}/{demand}）")
            break
        
        # Step 2: 找瓶颈容量
        bottleneck = demand - total_flow
        v = sink
        while v != source:
            u, ei = parent[v]
            bottleneck = min(bottleneck, edges[ei]['cap'])
            v = u
        
        # Step 3: 增广
        v = sink
        while v != source:
            u, ei = parent[v]
            edge = edges[ei]
            
            # 更新容量
            edge['cap'] -= bottleneck
            # 反向边
            rev_idx = ei ^ 1  # 假设反向边是相邻的奇偶索引
            edges[rev_idx]['cap'] += bottleneck
            
            # 更新费用
            total_cost += bottleneck * edge['cost']
            v = u
        
        total_flow += bottleneck
        
        # Step 4: 更新势
        for i in range(n):
            if dist[i] < float('inf'):
                potentials[i] += dist[i]
        
        print(f"  迭代 {iteration}: 增广 {bottleneck}，累计 {total_flow}/{demand}，费用 {total_cost}")
    
    return total_flow, total_cost


def verify_optimality(graph, edges, n, source, sink, potentials):
    """
    验证最优性条件：对于所有边，reduced cost >= 0
    """
    print("\n最优性验证（reduced cost >= 0）：")
    all_nonnegative = True
    
    for u in graph:
        for ei in graph[u]:
            edge = edges[ei]
            v = edge['to']
            if edge['cap'] > 0:
                rcost = edge['cost'] + potentials[u] - potentials[v]
                if rcost < -1e-9:
                    print(f"  警告: 边 {u}->{v} 的 reduced cost = {rcost:.4f} < 0")
                    all_nonnegative = False
    
    if all_nonnegative:
        print("  验证通过：满足最优性条件")


if __name__ == "__main__":
    print("=" * 55)
    print("原始对偶算法（Primal-Dual）求解最小费用流")
    print("=" * 55)
    
    graph, edges, nodes = build_primal_dual_network()
    n = 5
    source, sink = 0, 4
    demand = 7
    
    print(f"\n源点={source}, 汇点={sink}, 目标流量={demand}")
    print("\n迭代过程：")
    
    flow, cost = primal_dual_min_cost_flow(graph, edges, n, source, sink, demand)
    
    print(f"\n结果：流量={flow}, 费用={cost}")
    print(f"单位流量成本={flow > 0 and cost / flow:.2f}")
    
    # 重建势（从最后一次迭代）
    potentials = [0] * n
    # 势已经更新过了
