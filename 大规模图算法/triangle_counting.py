"""
三角形计数算法 (Triangle Counting)
===================================
实现多种高效的大规模图三角形计数算法：

1. NodeIterator：按节点枚举，过滤已处理邻居
2. EdgeIterator：按边枚举，检查两端点的邻居交集
3. 矩阵乘法优化：利用邻接矩阵的性质

参考：
    - Schank, T. (2007). Algorithmic Aspects of Triangle-Based Network Analysis.
    - Cohen, J. (2009). Graph Twiddling in a MapReduce World.
"""

from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict, deque
import random


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


# ==================== NodeIterator 算法 ====================

def triangle_count_node_iterator(graph: Graph) -> int:
    """
    NodeIterator 三角形计数
    
    思路：对于每个节点u，遍历其邻居v（v > u以避免重复），
    然后检查u和v是否有共同邻居w（w > v）
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    count = 0
    n = graph.n
    
    for u in range(n):
        # 获取已排序的邻居
        neighbors = sorted(graph.neighbors(u))
        
        for v in neighbors:
            if v > u:  # 只处理编号更大的邻居，避免重复计数
                # 找u和v的共同邻居
                neighbors_u = graph.neighbors(u)
                neighbors_v = graph.neighbors(v)
                
                for w in neighbors_v:
                    if w > v and w in neighbors_u:  # w > v 确保每个三角形只计一次
                        count += 1
    
    return count


def triangle_count_node_iterator_optimized(graph: Graph) -> int:
    """
    NodeIterator 优化版本：使用度数排序和集合交集
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    n = graph.n
    count = 0
    
    # 构建邻居列表（按度数排序的邻居节点）
    neighbor_lists = []
    for u in range(n):
        # 按邻居度数排序（度小的在前）
        neighbors = sorted(graph.neighbors(u), key=lambda x: graph.degree(x))
        neighbor_lists.append(neighbors)
    
    for u in range(n):
        for v in neighbor_lists[u]:
            if v > u:  # 只处理更大的邻居
                # 找共同邻居：使用集合交集
                # 只考虑邻居中大于v的，以避免重复
                common = []
                for w in neighbor_lists[u]:
                    if w > v and w in graph.neighbors(v):
                        common.append(w)
                count += len(common)
    
    return count


# ==================== EdgeIterator 算法 ====================

def triangle_count_edge_iterator(graph: Graph) -> int:
    """
    EdgeIterator 三角形计数
    
    思路：对于每条边(u, v)，遍历度数较小的端点的邻居，
    检查是否存在第三个节点w使得(u, v, w)构成三角形
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    count = 0
    n = graph.n
    
    for u in range(n):
        for v in graph.neighbors(u):
            if v > u:  # 每条边只处理一次
                # 选择度数较小的端点
                if graph.degree(u) < graph.degree(v):
                    smaller, larger = u, v
                else:
                    smaller, larger = v, u
                
                # 遍历较小度端点的邻居
                for w in graph.neighbors(smaller):
                    # w需要大于较大的端点以避免重复
                    if w > larger and w in graph.neighbors(larger):
                        count += 1
    
    return count


def triangle_count_edge_iterator_hash(graph: Graph) -> int:
    """
    EdgeIterator 使用哈希集合优化的版本
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    count = 0
    n = graph.n
    
    for u in range(n):
        for v in graph.neighbors(u):
            if v > u:
                # 使用度数选择
                if graph.degree(u) < graph.degree(v):
                    smaller, larger = u, v
                else:
                    smaller, larger = v, u
                
                # 构建较小端点邻居的集合（只包含大于larger的）
                smaller_neighbors = {w for w in graph.neighbors(smaller) if w > larger}
                
                # 检查交集
                larger_neighbors = graph.neighbors(larger)
                count += len(smaller_neighbors & larger_neighbors)
    
    return count


# ==================== Forward 算法 ====================

def triangle_count_forward(graph: Graph) -> int:
    """
    Forward 三角形计数算法
    
    基于节点顺序（度数排序）的forward技术
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    n = graph.n
    
    # 计算每个节点的度数
    degrees = [graph.degree(i) for i in range(n)]
    
    # 按度数排序得到节点排名
    # rank[node] = 节点在度数排序中的位置
    nodes_by_degree = sorted(range(n), key=lambda x: degrees[x])
    rank = [0] * n
    for pos, node in enumerate(nodes_by_degree):
        rank[node] = pos
    
    count = 0
    
    for u in range(n):
        # 获取邻居，按rank排序
        neighbors = sorted(graph.neighbors(u), key=lambda x: rank[x])
        
        for v in neighbors:
            # 只考虑rank更小的邻居（forward邻居）
            if rank[v] < rank[u]:
                # 检查v的forward邻居是否也在u的邻居中
                for w in neighbors:
                    if rank[w] < rank[v] and w in graph.neighbors(v):
                        # 检查是否形成三角形 (u, v, w)
                        # 由于u是当前节点，v和w是forward邻居
                        if w in graph.neighbors(u):
                            count += 1
    
    return count


# ==================== 列表交集算法 ====================

def triangle_count_list_intersection(graph: Graph) -> int:
    """
    使用排序列表交集的三角形计数
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    n = graph.n
    
    # 构建排序的邻居列表（按节点ID排序）
    sorted_neighbors = []
    for u in range(n):
        neighbors = sorted(graph.neighbors(u))
        sorted_neighbors.append(neighbors)
    
    count = 0
    
    # 对于每条边(u,v)，计算交集
    for u in range(n):
        for v in graph.neighbors(u):
            if v > u:  # 每条边只处理一次
                # 找共同邻居
                neighbors_u = sorted_neighbors[u]
                neighbors_v = sorted_neighbors[v]
                
                # 合并两列表并找公共元素
                i, j = 0, 0
                while i < len(neighbors_u) and j < len(neighbors_v):
                    if neighbors_u[i] == neighbors_v[j]:
                        # 找到公共邻居
                        # 但需要确保w > v以避免重复
                        w = neighbors_u[i]
                        if w > v:
                            count += 1
                        i += 1
                        j += 1
                    elif neighbors_u[i] < neighbors_v[j]:
                        i += 1
                    else:
                        j += 1
    
    return count


# ==================== 节点分组算法 ====================

def triangle_count_node_partitioning(graph: Graph) -> int:
    """
    基于节点分区的三角形计数
    
    将节点按度数分成小组，每组内的边进行局部计数
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    n = graph.n
    degrees = [graph.degree(i) for i in range(n)]
    
    # 估算平均度数
    avg_degree = sum(degrees) / n
    
    # 设置阈值
    T = avg_degree
    
    # 分类节点
    high_degree = []  # 度 > T
    low_degree = []   # 度 <= T
    
    for u in range(n):
        if degrees[u] > T:
            high_degree.append(u)
        else:
            low_degree.append(u)
    
    count = 0
    visited_triangles = set()  # 用于去重
    
    # 处理涉及高节点的三角形
    for u in high_degree:
        for v in graph.neighbors(u):
            if v > u:
                for w in graph.neighbors(v):
                    if w > v and w in graph.neighbors(u):
                        # 检查是否涉及高节点
                        if u in high_degree or v in high_degree or w in high_degree:
                            tri = (min(u, v, w), sorted([u, v, w])[1], max(u, v, w))
                            if tri not in visited_triangles:
                                visited_triangles.add(tri)
                                count += 1
    
    # 处理全为低度节点的三角形
    for u in low_degree:
        for v in graph.neighbors(u):
            if v > u and v in low_degree:
                common = graph.neighbors(u) & graph.neighbors(v)
                for w in common:
                    if w > v:
                        tri = (u, v, w)
                        if tri not in visited_triangles:
                            visited_triangles.add(tri)
                            count += 1
    
    return count


# ==================== 并行/MapReduce 概念算法 ====================

def triangle_count_mapreduce_style(graph: Graph) -> int:
    """
    模拟 MapReduce 风格的三角形计数
    
    Map阶段：发射边和对应的邻居
    Reduce阶段：合并并计数
    
    参数:
        graph: 输入图
    
    返回:
        三角形数量
    """
    n = graph.n
    
    # Map: 为每条边生成 (key, value) 对
    # key = (min(u,v), max(u,v))
    # value = (端点u的邻居列表, 端点v的邻居列表)
    
    # 构建边到邻居的映射
    edge_map = {}
    
    for u in range(n):
        for v in graph.neighbors(u):
            if v > u:
                key = (u, v)
                # 只存储大于v的邻居
                edge_map[key] = {
                    'neighbors_u': {w for w in graph.neighbors(u) if w > v},
                    'neighbors_v': {w for w in graph.neighbors(v) if w > v}
                }
    
    # Reduce: 计数
    count = 0
    
    for (u, v), data in edge_map.items():
        # 找共同邻居
        common = data['neighbors_u'] & data['neighbors_v']
        count += len(common)
    
    return count


def enumerate_triangles(graph: Graph) -> List[Tuple[int, int, int]]:
    """
    枚举图中的所有三角形
    
    参数:
        graph: 输入图
    
    返回:
        三角形列表 [(u, v, w), ...]
    """
    n = graph.n
    triangles = []
    
    for u in range(n):
        for v in graph.neighbors(u):
            if v > u:
                for w in graph.neighbors(v):
                    if w > v and w in graph.neighbors(u):
                        triangles.append((u, v, w))
    
    return triangles


if __name__ == "__main__":
    print("=== 三角形计数算法测试 ===")
    
    # 创建测试图：三角形
    g1 = Graph(3)
    g1.add_edge(0, 1)
    g1.add_edge(1, 2)
    g1.add_edge(2, 0)
    print(f"\n三角形图: {triangle_count_node_iterator(g1)} 个三角形")
    
    # 创建测试图：完全图 K4
    g2 = Graph(4)
    for i in range(4):
        for j in range(i + 1, 4):
            g2.add_edge(i, j)
    print(f"K4 完全图: {triangle_count_node_iterator(g2)} 个三角形")
    
    # 创建测试图：网格
    g3 = Graph(9)
    # 3x3 网格
    for i in range(3):
        for j in range(3):
            idx = i * 3 + j
            if j < 2:
                g3.add_edge(idx, idx + 1)
            if i < 2:
                g3.add_edge(idx, idx + 3)
    print(f"3x3 网格图: {triangle_count_node_iterator(g3)} 个三角形")
    
    # 创建随机图测试
    print("\n--- 随机图测试 ---")
    random.seed(42)
    g_random = Graph(100)
    for i in range(100):
        for j in range(i + 1, 100):
            if random.random() < 0.05:  # 5% 边概率
                g_random.add_edge(i, j)
    
    triangles = enumerate_triangles(g_random)
    print(f"随机图(100节点, 5%边概率): {len(triangles)} 个三角形")
    
    # 比较各算法
    algorithms = [
        ("NodeIterator", triangle_count_node_iterator),
        ("EdgeIterator", triangle_count_edge_iterator),
        ("ListIntersection", triangle_count_list_intersection),
        ("Forward", triangle_count_forward),
        ("NodePartitioning", triangle_count_node_partitioning),
        ("MapReduce", triangle_count_mapreduce_style),
    ]
    
    print("\n算法比较:")
    for name, func in algorithms:
        result = func(g_random)
        print(f"  {name}: {result}")
    
    print("\n=== 测试完成 ===")
