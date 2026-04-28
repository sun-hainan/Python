"""
K-核分解算法 (K-Core Decomposition)
===================================
计算图的k-核结构：k-核是删除所有度数小于k的节点后剩余的子图。

K-核分解是一种图的递归分解过程，每个节点被分配一个核心数（core number），
等于该节点所在的最高k-核。

参考：
    - Seidman, S.B. (1983). Network structure and minimum degree.
    - Batagelj, V. & Zaversnik, M. (2003). An O(m) algorithm for cores decomposition.
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import deque


class Graph:
    """无向图数据结构"""
    
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [set() for _ in range(n)]
    
    def add_edge(self, u: int, v: int):
        """添加无向边"""
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        """返回邻居集合"""
        return self.adj[u]
    
    def degree(self, u: int) -> int:
        """返回度数"""
        return len(self.adj[u])


def k_core_decomposition_naive(graph: Graph) -> Tuple[List[int], int]:
    """
    朴素K-核分解算法
    
    逐次删除度小于k的节点，逐步提升k值
    
    参数:
        graph: 输入图
    
    返回:
        (每个节点的核心数列表, 最大核数)
    """
    n = graph.n
    # 复制图以避免修改原图
    adj = [set(graph.adj[i]) for i in range(n)]
    degrees = [len(adj[i]) for i in range(n)]
    
    core_numbers = [0] * n
    max_k = 0
    
    # 初始化删除队列：度小于当前k的节点
    # 我们从k=0开始，逐步增加到最大度数
    min_degree = min(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0
    
    for k in range(min_degree, max_degree + 1):
        # 标记所有未处理节点中度<k的
        removed = [False] * n
        queue = deque()
        
        for i in range(n):
            if degrees[i] < k:
                queue.append(i)
                removed[i] = True
        
        # BFS删除过程
        while queue:
            u = queue.popleft()
            core_numbers[u] = k - 1  # 删除前的k值
            
            # 更新邻居的度数
            for v in adj[u]:
                if not removed[v]:
                    degrees[v] -= 1
                    if degrees[v] < k:
                        queue.append(v)
                        removed[v] = True
        
        # 重新初始化准备下一轮
        if k > max_k:
            max_k = k - 1
    
    # 对未删除的节点设置最终核心数
    for i in range(n):
        if core_numbers[i] == 0:
            core_numbers[i] = max_k
    
    return core_numbers, max_k


def k_core_decomposition_bin_sort(graph: Graph) -> Tuple[List[int], int]:
    """
    高效K-核分解算法：使用桶排序
    
    时间复杂度: O(m)
    空间复杂度: O(n + m)
    
    参数:
        graph: 输入图
    
    返回:
        (每个节点的核心数列表, 最大核数)
    """
    n = graph.n
    
    # 复制度数
    degrees = [graph.degree(i) for i in range(n)]
    max_degree = max(degrees) if degrees else 0
    
    # 创建度数桶：bucket[d] = [节点列表]
    buckets = [[] for _ in range(max_degree + 1)]
    for i in range(n):
        buckets[degrees[i]].append(i)
    
    # 邻接表副本
    adj = [set(graph.adj[i]) for i in range(n)]
    
    # 核心数
    core_numbers = [0] * n
    
    # 当前位置指针
    pos = [0] * (max_degree + 1)
    for d in range(max_degree + 1):
        pos[d] = 0
    
    # 标记已删除的节点
    removed = [False] * n
    
    # 当前最小度数
    min_deg = 0
    
    # 遍历所有节点
    for _ in range(n):
        # 找到当前最小度数
        while min_deg <= max_degree and (not buckets[min_deg] or pos[min_deg] >= len(buckets[min_deg])):
            min_deg += 1
        
        if min_deg > max_degree:
            break
        
        # 取出最小度数的节点
        u = buckets[min_deg][pos[min_deg]]
        pos[min_deg] += 1
        removed[u] = True
        core_numbers[u] = min_deg
        
        # 更新邻居的度数
        for v in adj[u]:
            if not removed[v]:
                # 将v从当前度数桶移到度数-1的桶
                old_deg = degrees[v]
                new_deg = old_deg - 1
                degrees[v] = new_deg
                
                if pos[old_deg] < len(buckets[old_deg]):
                    # 将v添加到新桶
                    buckets[new_deg].append(v)
                
                # 更新最小度数
                if new_deg < min_deg:
                    min_deg = new_deg
    
    return core_numbers, max(core_numbers)


def k_core_decomposition_peel(graph: Graph, k: int) -> Set[int]:
    """
    提取k-核：删除所有度数小于k的节点后的子图节点集合
    
    参数:
        graph: 输入图
        k: 核参数
    
    返回:
        k-核中的节点集合
    """
    n = graph.n
    degrees = [graph.degree(i) for i in range(n)]
    adj = [set(graph.adj[i]) for i in range(n)]
    
    removed = [False] * n
    queue = deque()
    
    # 初始化度<k的节点
    for i in range(n):
        if degrees[i] < k:
            queue.append(i)
            removed[i] = True
    
    # BFS删除
    while queue:
        u = queue.popleft()
        
        for v in adj[u]:
            if not removed[v]:
                degrees[v] -= 1
                if degrees[v] < k:
                    queue.append(v)
                    removed[v] = True
    
    # 返回未被删除的节点
    k_core = {i for i in range(n) if not removed[i]}
    return k_core


def k_shell_decomposition(graph: Graph) -> Dict[int, Set[int]]:
    """
    K-壳分解：返回每个k值对应的壳（同一核数的节点集合）
    
    参数:
        graph: 输入图
    
    返回:
        字典 {k: 节点集合}
    """
    n = graph.n
    core_numbers, max_k = k_core_decomposition_bin_sort(graph)
    
    shells = {k: set() for k in range(max_k + 1)}
    for i in range(n):
        shells[core_numbers[i]].add(i)
    
    return shells


def k_core_decomposition_bfs(graph: Graph) -> Tuple[List[int], int]:
    """
    BFS风格的K-核分解
    
    参数:
        graph: 输入图
    
    返回:
        (核心数列表, 最大核数)
    """
    n = graph.n
    degrees = [graph.degree(i) for i in range(n)]
    adj = [set(graph.adj[i]) for i in range(n)]
    
    core_numbers = [0] * n
    removed = [False] * n
    
    # 按度数排序节点
    nodes_by_deg = sorted(range(n), key=lambda x: degrees[x])
    
    # 使用映射：原始节点 -> 在排序中的位置
    rank = [0] * n
    for pos, node in enumerate(nodes_by_deg):
        rank[node] = pos
    
    # 构建排序后的度数数组
    sorted_degrees = [degrees[node] for node in nodes_by_deg]
    
    # 遍历节点
    for i, u in enumerate(nodes_by_deg):
        if removed[u]:
            continue
        
        k = sorted_degrees[i]
        core_numbers[u] = k
        
        # 标记u为已处理
        # 不实际删除，而是标记
        
        # 更新邻居的度数（只有邻居的度数>当前k时才考虑）
        for v in adj[u]:
            if removed[v]:
                continue
            
            # 找到v在排序中的位置
            pos_v = rank[v]
            
            # 只处理还未被"删除"的邻居（度数还没更新到<=k）
            if sorted_degrees[pos_v] > k:
                sorted_degrees[pos_v] -= 1
    
    # 标记已处理节点
    # 这里简化处理：设置core_numbers
    for i, u in enumerate(nodes_by_deg):
        if core_numbers[u] == 0:
            core_numbers[u] = sorted_degrees[i]
    
    return core_numbers, max(core_numbers)


def compute_cores_table(graph: Graph) -> Tuple[List[int], List[int]]:
    """
    计算核心数查找表
    
    返回:
        (核心数列表, 各核心数的节点计数)
    """
    core_numbers, max_k = k_core_decomposition_bin_sort(graph)
    
    counts = [0] * (max_k + 1)
    for cn in core_numbers:
        if cn <= max_k:
            counts[cn] += 1
    
    return core_numbers, counts


def k_truss_decomposition(graph: Graph) -> Tuple[List[int], int]:
    """
    K-桁架分解 (K-Truss)
    
    k-桁架是图中每个边都在至少(k-2)个三角形中的子图
    
    注意：这是简化的近似实现
    
    参数:
        graph: 输入图
    
    返回:
        (每条边的桁架数, 最大桁架数)
    """
    n = graph.n
    adj = [set(graph.adj[i]) for i in range(n)]
    
    # 计算每条边所在的三角形数量
    edge_triangles = {}  # (u,v) -> 三角形数量
    edges = []
    
    for u in range(n):
        for v in adj[u]:
            if u < v:
                # 计算包含边(u,v)的三角形数量
                count = len(adj[u] & adj[v])
                edge_triangles[(u, v)] = count
                edges.append((u, v))
    
    if not edges:
        return [], 0
    
    # 桁架数 = 2 + 最小三角形数量
    truss_numbers = [2 + edge_triangles[e] for e in edges]
    
    return truss_numbers, max(truss_numbers)


if __name__ == "__main__":
    print("=== K-核分解算法测试 ===")
    
    # 测试图1: 简单图
    g1 = Graph(6)
    g1.add_edge(0, 1)
    g1.add_edge(1, 2)
    g1.add_edge(2, 0)  # 三角形 0-1-2
    g1.add_edge(3, 4)
    g1.add_edge(4, 5)
    g1.add_edge(3, 5)  # 三角形 3-4-5
    g1.add_edge(2, 3)  # 连接两个三角形
    
    print("\n图1: 两个三角形共用一个顶点")
    print("   0---1")
    print("   | \\ |")
    print("   2---3---4")
    print("         \\ |")
    print("          5")
    
    core_nums, max_k = k_core_decomposition_bin_sort(g1)
    print(f"核心数: {core_nums}")
    print(f"最大核数: {max_k}")
    
    # 测试k-壳分解
    shells = k_shell_decomposition(g1)
    print("各核数节点:")
    for k, nodes in shells.items():
        print(f"  k={k}: {nodes}")
    
    # 测试k-核提取
    print("\n提取各k-核:")
    for k in range(max_k + 1):
        k_core = k_core_peel(g1, k)
        print(f"  {k}-核: {k_core}")
    
    # 测试图2: 复杂图
    print("\n\n图2: 更复杂图")
    g2 = Graph(10)
    edges = [(0,1), (1,2), (2,0), (2,3), (3,4), (4,5), (3,5),
             (5,6), (6,7), (7,8), (8,9), (6,9), (5,8)]
    for u, v in edges:
        g2.add_edge(u, v)
    
    core_nums2, max_k2 = k_core_decomposition_bin_sort(g2)
    print(f"核心数: {core_nums2}")
    print(f"最大核数: {max_k2}")
    
    # 验证朴素算法
    core_nums_naive, max_k_naive = k_core_decomposition_naive(g2)
    print(f"\n朴素算法验证:")
    print(f"核心数: {core_nums_naive}")
    print(f"最大核数: {max_k_naive}")
    
    # 测试桁架分解
    print("\n\nK-桁架分解:")
    truss_nums, max_truss = k_truss_decomposition(g2)
    print(f"边桁架数: {truss_nums}")
    print(f"最大桁架数: {max_truss}")
    
    print("\n=== 测试完成 ===")
