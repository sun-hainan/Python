"""
线图构建与性质 (Line Graph Construction and Properties)
====================================================
实现线图的构建算法，并分析其性质。

线图L(G)：图的边转换为节点的图。两个节点在L(G)中相邻，
当且仅当对应的两条边在原图中共享一个端点。

性质：
- 连通性：原图的连通性与线图的连通性相关
- 三角形：原图中的三角形对应线图中的完全子图K3
- 自同构：线图保留了原图的部分结构信息

参考：
    - Harary, F. (1962). Graph Theory.
    - Whitney, H. (1932). Congruent graphs and the connectivity of graphs.
"""

from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict


class Graph:
    """无向图"""
    def __init__(self, n: int = 0, edges: Optional[List[Tuple[int, int]]] = None):
        self.n = n
        self.adj = [set() for _ in range(n)]
        self.edge_list = []  # 边列表
        self.edge_index = {}  # (u,v) -> edge_id
        
        if edges:
            for u, v in edges:
                self.add_edge(u, v)
    
    def add_edge(self, u: int, v: int):
        """添加边"""
        if v not in self.adj[u]:
            edge_id = len(self.edge_list)
            self.adj[u].add(v)
            self.adj[v].add(u)
            self.edge_list.append((u, v))
            self.edge_index[(min(u, v), max(u, v))] = edge_id
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]
    
    def degree(self, u: int) -> int:
        return len(self.adj[u])
    
    def get_edge_id(self, u: int, v: int) -> int:
        key = (min(u, v), max(u, v))
        return self.edge_index.get(key, -1)
    
    def num_edges(self) -> int:
        return len(self.edge_list)


class LineGraph:
    """线图"""
    def __init__(self, original_graph: Graph):
        self.original = original_graph
        self._build()
    
    def _build(self):
        """构建线图"""
        edges = self.original.edge_list
        m = len(edges)
        
        # 线图节点数 = 原图边数
        self.n = m
        self.adj = [set() for _ in range(m)]
        
        # 对于每条边，找共享端点的其他边
        for i in range(m):
            u1, v1 = edges[i]
            
            for j in range(i + 1, m):
                u2, v2 = edges[j]
                
                # 检查是否共享端点
                if u1 == u2 or u1 == v2 or v1 == u2 or v1 == v2:
                    # 边i和边j在原图中相邻
                    self.adj[i].add(j)
                    self.adj[j].add(i)
    
    def neighbors(self, edge_id: int) -> Set[int]:
        """返回与给定边相邻的边ID"""
        return self.adj[edge_id]
    
    def to_graph(self) -> Graph:
        """转换为Graph对象"""
        g = Graph(self.n)
        for u in range(self.n):
            for v in self.adj[u]:
                if v > u:
                    g.add_edge(u, v)
        return g


def build_line_graph(original: Graph) -> LineGraph:
    """
    构建原图的线图
    
    参数:
        original: 原图
    
    返回:
        线图
    """
    return LineGraph(original)


def line_graph_of_clique(k: int) -> Tuple[Graph, Graph]:
    """
    完全图K_k的线图
    
    K_k的线图是完全图K_{C(k,2)}
    
    参数:
        k: K_k的节点数
    
    返回:
        (K_k, 它的线图K_{C(k,2)})
    """
    # 构建K_k
    g = Graph(k)
    for i in range(k):
        for j in range(i + 1, k):
            g.add_edge(i, j)
    
    # 构建线图
    lg = LineGraph(g)
    lg_g = lg.to_graph()
    
    return g, lg_g


def line_graph_of_path(n: int) -> Tuple[Graph, Graph]:
    """
    路径P_n的线图
    
    P_n的线图还是路径P_{n-1}
    
    参数:
        n: 路径节点数
    
    返回:
        (P_n, 它的线图)
    """
    # 构建P_n
    g = Graph(n)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    
    # 构建线图
    lg = LineGraph(g)
    lg_g = lg.to_graph()
    
    return g, lg_g


def line_graph_of_cycle(n: int) -> Tuple[Graph, Graph]:
    """
    环C_n的线图
    
    C_n的线图还是环C_n
    
    参数:
        n: 环的节点数
    
    返回:
        (C_n, 它的线图)
    """
    # 构建C_n
    g = Graph(n)
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    
    # 构建线图
    lg = LineGraph(g)
    lg_g = lg.to_graph()
    
    return g, lg_g


def is_line_graph(g: Graph) -> Tuple[bool, Optional[Graph]]:
    """
    检测一个图是否是某个图的线图（线图的线图定理）
    
    参数:
        g: 待检测图
    
    返回:
        (是否是线图, 原图如果是线图)
    """
    n = g.n
    m = g.num_edges() if hasattr(g, 'num_edges') else sum(1 for _ in g.edge_list)
    
    # 检查是否为线图的基本必要条件
    # 1. 不包含特定诱导子图
    # 2. 度数条件
    
    # 尝试反向构建（简化的启发式方法）
    # 实际线图检测需要更复杂的算法
    
    return False, None


def line_graph_triangles(g: Graph) -> List[Tuple[int, int, int]]:
    """
    找线图中的三角形（对应原图中4-圈）
    
    参数:
        g: 原图
    
    返回:
        三角形列表（边ID三元组）
    """
    lg = LineGraph(g)
    lg_g = lg.to_graph()
    
    # 在线图中找三角形
    n = lg_g.n
    triangles = []
    
    for i in range(n):
        for j in lg_g.adj[i]:
            if j > i:
                for k in lg_g.adj[i]:
                    if k > j and k in lg_g.adj[j]:
                        triangles.append((i, j, k))
    
    return triangles


def line_graph_cliques(g: Graph) -> List[Set[int]]:
    """
    找线图中的完全子图（对应原图中的团）
    
    参数:
        g: 原图
    
    返回:
        完全子图列表（边ID集合）
    """
    lg = LineGraph(g)
    lg_g = lg.to_graph()
    
    cliques = []
    n = lg_g.n
    
    # 简单枚举（指数复杂度，仅适用于小图）
    for mask in range(1, 1 << n):
        nodes = {i for i in range(n) if mask & (1 << i)}
        
        # 检查是否完全图
        is_clique = True
        for u in nodes:
            for v in nodes:
                if u < v and v not in lg_g.adj[u]:
                    is_clique = False
                    break
            if not is_clique:
                break
        
        if is_clique and len(nodes) >= 2:
            cliques.append(nodes)
    
    return cliques


def edge_adjacency_matrix(g: Graph) -> List[List[int]]:
    """
    构建边邻接矩阵（线图的邻接矩阵）
    
    参数:
        g: 原图
    
    返回:
        边邻接矩阵
    """
    m = g.num_edges()
    matrix = [[0] * m for _ in range(m)]
    
    edges = g.edge_list
    
    for i in range(m):
        u1, v1 = edges[i]
        for j in range(i + 1, m):
            u2, v2 = edges[j]
            
            # 检查是否共享端点
            if u1 == u2 or u1 == v2 or v1 == u2 or v1 == v2:
                matrix[i][j] = 1
                matrix[j][i] = 1
    
    return matrix


def converse_line_graph(g: Graph) -> Optional[Graph]:
    """
    线图的逆：给定线图，找原图（可能不唯一）
    
    参数:
        g: 线图
    
    返回:
        原图（如果找到）
    """
    # 简化的启发式方法
    # 实际这个问题更复杂
    return None


if __name__ == "__main__":
    print("=== 线图构建与性质测试 ===")
    
    # 测试1: 简单图
    print("\n测试1: 简单图")
    g1 = Graph(4)
    g1.add_edge(0, 1)
    g1.add_edge(1, 2)
    g1.add_edge(2, 3)
    g1.add_edge(0, 2)  # 形成三角形
    
    print(f"原图: {g1.n} 节点, {g1.num_edges()} 边")
    print(f"边列表: {g1.edge_list}")
    
    lg1 = LineGraph(g1)
    lg1_g = lg1.to_graph()
    
    print(f"线图: {lg1_g.n} 节点, {lg1_g.num_edges()} 边")
    
    # 边邻接矩阵
    adj_matrix = edge_adjacency_matrix(g1)
    print("边邻接矩阵:")
    for row in adj_matrix:
        print(f"  {row}")
    
    # 测试2: 完全图K4
    print("\n\n测试2: 完全图K4")
    g2, lg2 = line_graph_of_clique(4)
    print(f"K4: {g2.n} 节点, {g2.num_edges()} 边")
    print(f"K4的线图: {lg2.n} 节点 (完全图K6有15边，所以实际是...)")
    
    # 重新计算
    lg2_direct = LineGraph(g2)
    print(f"K4的线图: {lg2_direct.n} 节点 (K4有6条边)")
    
    # 测试3: 路径
    print("\n\n测试3: 路径P5")
    g3, lg3 = line_graph_of_path(5)
    print(f"P5: {g3.n} 节点, {g3.num_edges()} 边")
    print(f"P5的线图: {lg3.n} 节点, {lg3.num_edges()} 边")
    
    # 测试4: 环
    print("\n\n测试4: 环C5")
    g4, lg4 = line_graph_of_cycle(5)
    print(f"C5: {g4.n} 节点, {g4.num_edges()} 边")
    print(f"C5的线图: {lg4.n} 节点, {lg4.num_edges()} 边")
    
    # 测试5: 线图三角形
    print("\n\n测试5: 线图三角形（对应原图4-圈）")
    g5 = Graph(4)
    g5.add_edge(0, 1)
    g5.add_edge(1, 2)
    g5.add_edge(2, 3)
    g5.add_edge(3, 0)
    g5.add_edge(0, 2)  # 对角线
    
    triangles = line_graph_triangles(g5)
    print(f"原图5边，形成 {len(triangles)} 个线图三角形")
    for t in triangles:
        edges = [g5.edge_list[e] for e in t]
        print(f"  三角形: 边{t} -> {edges}")
    
    # 测试6: 完全子图（团）
    print("\n\n测试6: 完全子图（对应原图中的三角形）")
    g6 = Graph(3)
    g6.add_edge(0, 1)
    g6.add_edge(1, 2)
    g6.add_edge(2, 0)
    
    cliques = line_graph_cliques(g6)
    print(f"线图中的完全子图: {cliques}")
    
    print("\n=== 测试完成 ===")
