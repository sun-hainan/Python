"""
图的连通性算法 (Graph Connectivity)
===================================
实现割点、割边（桥）和双连通分量算法。

- 割点（Articulation Point）：删除后增加连通分量的节点
- 割边/桥（Bridge）：删除后增加连通分量的边
- 双连通分量（Biconnected Component）：没有割点的极大子图

使用Tarjan算法基于DFS树和lowlink值计算。

参考：
    - Tarjan, R.E. (1972). Depth-first search and linear graph algorithms.
    - Hopcroft, J. & Tarjan, R. (1973). Algorithm 447: Efficient root...
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import deque


class UndirectedGraph:
    """无向图"""
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [set() for _ in range(n)]
        self.edges = set()  # 存储所有边 (min, max)
    
    def add_edge(self, u: int, v: int):
        self.adj[u].add(v)
        self.adj[v].add(u)
        self.edges.add((min(u, v), max(u, v)))
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]


def find_cut_vertices_and_bridges(graph: UndirectedGraph) -> Tuple[List[int], List[Tuple[int, int]]]:
    """
    找割点和桥（Tarjan算法）
    
    参数:
        graph: 无向图
    
    返回:
        (割点列表, 桥列表)
    """
    n = graph.n
    
    # DFS状态
    disc = [-1] * n  # 发现时间
    low = [0] * n    # lowlink值
    parent = [-1] * n
    time = [0]  # 全局时间
    
    cut_vertices = []
    bridges = []
    
    def dfs(u: int):
        disc[u] = low[u] = time[0]
        time[0] += 1
        
        children = 0
        is_cut = False
        
        for v in graph.neighbors(u):
            if disc[v] == -1:
                # v未被访问，是u的子节点
                parent[v] = u
                children += 1
                dfs(v)
                
                # 更新low值
                low[u] = min(low[u], low[v])
                
                # 割点条件1：u是根节点且有多个子树
                if parent[u] == -1 and children > 1:
                    is_cut = True
                
                # 割点条件2：u非根且有子节点的low >= disc[u]
                if parent[u] != -1 and low[v] >= disc[u]:
                    is_cut = True
                
                # 桥条件：边(u,v)是桥 iff low[v] > disc[u]
                if low[v] > disc[u]:
                    bridges.append((min(u, v), max(u, v)))
            
            elif v != parent[u]:
                # 回边
                low[u] = min(low[u], disc[v])
        
        if is_cut:
            cut_vertices.append(u)
    
    for v in range(n):
        if disc[v] == -1:
            dfs(v)
    
    return cut_vertices, bridges


def find_biconnected_components(graph: UndirectedGraph) -> List[Set[int]]:
    """
    找双连通分量（边双连通分量）
    
    参数:
        graph: 无向图
    
    返回:
        双连通分量列表，每个分量是节点集合
    """
    n = graph.n
    
    disc = [-1] * n
    low = [0] * n
    parent = [-1] * n
    time = [0]
    
    stack = []  # 边栈
    components = []
    
    def dfs(u: int):
        disc[u] = low[u] = time[0]
        time[0] += 1
        
        for v in graph.neighbors(u):
            if disc[v] == -1:
                parent[v] = u
                stack.append((min(u, v), max(u, v)))
                dfs(v)
                
                low[u] = min(low[u], low[v])
                
                # 如果low[v] >= disc[u]，找到一个BCC
                if low[v] >= disc[u]:
                    component = set()
                    while stack and stack[-1] != (min(u, v), max(u, v)):
                        edge = stack.pop()
                        component.add(edge[0])
                        component.add(edge[1])
                    if stack:
                        edge = stack.pop()
                        component.add(edge[0])
                        component.add(edge[1])
                    components.append(component)
            
            elif v != parent[u] and disc[v] < disc[u]:
                # 回边
                stack.append((min(u, v), max(u, v)))
                low[u] = min(low[u], disc[v])
    
    for v in range(n):
        if disc[v] == -1:
            dfs(v)
            
            # 处理剩余的边
            if stack:
                component = set()
                while stack:
                    edge = stack.pop()
                    component.add(edge[0])
                    component.add(edge[1])
                components.append(component)
    
    return components


def find_edge_biconnected_components(graph: UndirectedGraph) -> List[Set[int]]:
    """
    边双连通分量（不含桥的极大子图）
    
    参数:
        graph: 无向图
    
    返回:
        边双连通分量列表
    """
    cut_verts, bridges = find_cut_vertices_and_bridges(graph)
    
    # 标记桥
    bridge_set = set(bridges)
    
    # 删除所有桥后的连通分量
    visited = [False] * graph.n
    components = []
    
    def dfs(u: int, component: Set[int]):
        visited[u] = True
        component.add(u)
        for v in graph.neighbors(u):
            edge = (min(u, v), max(u, v))
            if not visited[v] and edge not in bridge_set:
                dfs(v, component)
    
    for v in range(graph.n):
        if not visited[v]:
            component = set()
            dfs(v, component)
            components.append(component)
    
    return components


def find_vertex_biconnected_components(graph: UndirectedGraph) -> List[Set[int]]:
    """
    点双连通分量（块）
    
    参数:
        graph: 无向图
    
    返回:
        点双连通分量列表
    """
    n = graph.n
    
    disc = [-1] * n
    low = [0] * n
    parent = [-1] * n
    time = [0]
    
    stack = []  # 边栈
    components = []
    
    def dfs(u: int):
        disc[u] = low[u] = time[0]
        time[0] += 1
        
        children = 0
        is_articulation = False
        
        for v in graph.neighbors(u):
            if disc[v] == -1:
                parent[v] = u
                children += 1
                stack.append((min(u, v), max(u, v)))
                dfs(v)
                
                low[u] = min(low[u], low[v])
                
                # 点双连通分量：low[v] >= disc[u]
                if low[v] >= disc[u]:
                    is_articulation = True
                    component = set()
                    while stack and stack[-1] != (min(u, v), max(u, v)):
                        edge = stack.pop()
                        component.add(edge[0])
                        component.add(edge[1])
                    if stack:
                        edge = stack.pop()
                        component.add(edge[0])
                        component.add(edge[1])
                    components.append(component)
            
            elif v != parent[u] and disc[v] < disc[u]:
                stack.append((min(u, v), max(u, v)))
                low[u] = min(low[u], disc[v])
        
        # 根节点特殊处理
        if parent[u] == -1 and children > 1:
            is_articulation = True
        
        if not is_articulation and parent[u] != -1 and children == 0:
            # 单独的点（没有子树的叶子）形成单独的BCC
            component = {u}
            components.append(component)
    
    for v in range(n):
        if disc[v] == -1:
            dfs(v)
    
    return components


def is_biconnected(graph: UndirectedGraph) -> bool:
    """
    检查图是否双连通（没有割点）
    
    参数:
        graph: 无向图
    
    返回:
        是否双连通
    """
    if graph.n < 3:
        return graph.n <= 1
    
    cut_verts, _ = find_cut_vertices_and_bridges(graph)
    return len(cut_verts) == 0


def find_connected_components(graph: UndirectedGraph) -> List[Set[int]]:
    """
    找连通分量（BFS/DFS）
    
    参数:
        graph: 无向图
    
    返回:
        连通分量列表
    """
    n = graph.n
    visited = [False] * n
    components = []
    
    def dfs(u: int, component: Set[int]):
        visited[u] = True
        component.add(u)
        for v in graph.neighbors(u):
            if not visited[v]:
                dfs(v, component)
    
    for v in range(n):
        if not visited[v]:
            component = set()
            dfs(v, component)
            components.append(component)
    
    return components


def count_connected_components(graph: UndirectedGraph) -> int:
    """
    统计连通分量数量
    
    参数:
        graph: 无向图
    
    返回:
        连通分量数
    """
    return len(find_connected_components(graph))


def is_connected(graph: UndirectedGraph) -> bool:
    """
    检查图是否连通
    
    参数:
        graph: 无向图
    
    返回:
        是否连通
    """
    return count_connected_components(graph) == 1


if __name__ == "__main__":
    print("=== 图连通性算法测试 ===")
    
    # 测试图1: 有割点的图
    #     0
    #    / |
    #   1  2
    #   | /
    #   3
    #  / \
    # 4   5
    g1 = UndirectedGraph(6)
    g1.add_edge(0, 1)
    g1.add_edge(0, 2)
    g1.add_edge(1, 3)
    g1.add_edge(2, 3)
    g1.add_edge(3, 4)
    g1.add_edge(3, 5)
    
    print("\n测试图1: 树状图")
    print("    0")
    print("   /|")
    print("  1 2")
    print("  |/")
    print("  3")
    print(" /|")
    print("4 5")
    
    cut_verts, bridges = find_cut_vertices_and_bridges(g1)
    print(f"割点: {cut_verts}")
    print(f"桥: {bridges}")
    
    bcc = find_edge_biconnected_components(g1)
    print(f"边双连通分量: {bcc}")
    
    v_bcc = find_vertex_biconnected_components(g1)
    print(f"点双连通分量: {v_bcc}")
    
    # 测试图2: 完全图 K4（无割点）
    g2 = UndirectedGraph(4)
    for i in range(4):
        for j in range(i + 1, 4):
            g2.add_edge(i, j)
    
    print("\n\n完全图 K4:")
    cut_verts2, bridges2 = find_cut_vertices_and_bridges(g2)
    print(f"割点: {cut_verts2}")
    print(f"桥: {bridges2}")
    print(f"是否双连通: {is_biconnected(g2)}")
    
    # 测试图3: 含有桥的图
    #   0 --- 1 --- 2
    #         |
    #         3
    g3 = UndirectedGraph(4)
    g3.add_edge(0, 1)
    g3.add_edge(1, 2)
    g3.add_edge(1, 3)
    
    print("\n\n图3: 含桥的图")
    print("  0 --- 1 --- 2")
    print("        |")
    print("        3")
    
    cut_verts3, bridges3 = find_cut_vertices_and_bridges(g3)
    print(f"割点: {cut_verts3}")
    print(f"桥: {bridges3}")
    
    # 测试图4: 两个双连通分量通过割点连接
    #     0
    #    / \
    #   1   2
    #   |   |
    #   3---4---5
    g4 = UndirectedGraph(6)
    g4.add_edge(0, 1)
    g4.add_edge(0, 2)
    g4.add_edge(1, 3)
    g4.add_edge(2, 4)
    g4.add_edge(3, 4)
    g4.add_edge(4, 5)
    
    print("\n\n图4: 两个BCC通过割点连接")
    cut_verts4, bridges4 = find_cut_vertices_and_bridges(g4)
    print(f"割点: {cut_verts4}")
    print(f"桥: {bridges4}")
    
    bcc4 = find_edge_biconnected_components(g4)
    print(f"边双连通分量: {bcc4}")
    
    print("\n=== 测试完成 ===")
