"""
子图同构检测算法 (Subgraph Isomorphism)
========================================
实现Ullmann算法和VF2算法，用于检测查询图Q是否在目标图G中存在子图同构。

Ullmann算法：基于邻接矩阵的枚举+剪枝，通过细化步骤过滤不可能的节点映射。
VF2算法：基于状态空间搜索，按语义匹配规则逐步扩展映射。

参考：
    - Ullmann, J.R. (1976). An algorithm for subgraph isomorphism.
    - Cordella, L.P. et al. (2004). A (sub)graph isomorphism algorithm for matching large graphs.
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import deque


class Graph:
    """图数据结构，使用邻接表表示"""
    
    def __init__(self, n: int = 0):
        self.n = n  # 节点数量
        self.adj = [[] for _ in range(n)]  # 邻接表: adj[u] = [v1, v2, ...]
    
    def add_edge(self, u: int, v: int):
        """添加无向边 (u, v)"""
        if v not in self.adj[u]:
            self.adj[u].append(v)
        if u not in self.adj[v]:
            self.adj[v].append(u)
    
    def degree(self, u: int) -> int:
        """返回节点u的度数"""
        return len(self.adj[u])


def build_adjacency_matrix(graph: Graph) -> List[List[int]]:
    """根据图构建邻接矩阵 (1=有边, 0=无边)"""
    n = graph.n
    matrix = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in graph.adj[u]:
            matrix[u][v] = 1
    return matrix


def ullmann_refine(M: List[List[int]], graph_g: Graph, graph_q: Graph, 
                   current_map: List[Optional[int]]) -> bool:
    """
    Ullmann算法的细化(refine)步骤
    检查当前映射矩阵M是否可以通过细化得到有效解
    
    参数:
        M: 当前候选映射矩阵，M[u][v]=1表示q的节点u可能映射到g的节点v
        graph_g: 目标图G
        graph_q: 查询图Q
        current_map: 当前已确定的映射，current_map[q_node] = g_node
    
    返回:
        bool: 是否存在有效映射
    """
    n_q = graph_q.n
    n_g = graph_g.n
    
    # 复制M作为工作矩阵
    M_current = [row[:] for row in M]
    
    # 迭代细化直到稳定
    changed = True
    while changed:
        changed = False
        
        # 对查询图Q中的每个节点u
        for u in range(n_q):
            # 如果u已经有确定映射，跳过
            if current_map[u] != -1:
                continue
            
            # 计算u在Q中的邻居
            neighbors_q = set(graph_q.adj[u])
            
            # 对G中每个候选节点v
            for v in range(n_g):
                if M_current[u][v] == 0:
                    continue
                
                # 检查1: v在G中的邻居必须覆盖Q中u的已映射邻居
                neighbors_g = set(graph_g.adj[v])
                for u_prime in neighbors_q:
                    if current_map[u_prime] != -1:
                        g_prime = current_map[u_prime]
                        if g_prime not in neighbors_g:
                            M_current[u][v] = 0
                            changed = True
                            break
                
                if M_current[u][v] == 0:
                    continue
                
                # 检查2: 度约束，v的度必须>=u的邻居数（对于未映射邻居也要满足）
                required_neighbors = 0
                for u_prime in neighbors_q:
                    if current_map[u_prime] == -1:
                        required_neighbors += 1
                if len(neighbors_g) < required_neighbors:
                    M_current[u][v] = 0
                    changed = True
                    continue
    
    # 检查是否每个未映射节点都有至少一个候选
    for u in range(n_q):
        if current_map[u] == -1:
            if not any(M_current[u][v] for v in range(n_g)):
                return False
    
    # 更新M
    for u in range(n_q):
        for v in range(n_g):
            M[u][v] = M_current[u][v]
    
    return True


def ullmann_search(M: List[List[int]], graph_g: Graph, graph_q: Graph,
                  current_map: List[Optional[int]], depth: int) -> bool:
    """
    Ullmann算法的深度优先搜索
    
    参数:
        M: 候选映射矩阵
        graph_g: 目标图G
        graph_q: 查询图Q
        current_map: 当前映射
        depth: 当前搜索深度（处理的查询节点索引）
    
    返回:
        bool: 是否找到有效映射
    """
    n_q = graph_q.n
    
    # 所有节点都已映射，找到解
    if depth == n_q:
        return True
    
    # 找到下一个需要映射的节点（按度递减顺序，选择候选最少的）
    candidates = []
    for u in range(n_q):
        if current_map[u] == -1:
            count = sum(1 for v in range(graph_g.n) if M[u][v] == 1)
            candidates.append((count, u))
    
    if not candidates:
        return True
    
    candidates.sort()
    u = candidates[0][1]  # 选择候选最少的节点
    
    # 尝试每个候选映射
    for v in range(graph_g.n):
        if M[u][v] == 1:
            # 临时应用映射
            old_map_u = current_map[u]
            current_map[u] = v
            
            # 备份M
            M_backup = [row[:] for row in M]
            
            # 细化
            if ullmann_refine(M, graph_g, graph_q, current_map):
                # 递归搜索
                if ullmann_search(M, graph_g, graph_q, current_map, depth + 1):
                    return True
            
            # 回溯
            current_map[u] = old_map_u
            M[:] = M_backup
    
    return False


def ullmann_isomorphism(graph_g: Graph, graph_q: Graph) -> bool:
    """
    Ullmann算法主函数：检测graph_q是否是graph_g的子图
    
    参数:
        graph_g: 目标图G
        graph_q: 查询图Q
    
    返回:
        bool: Q是否同构于G的某个子图
    """
    if graph_q.n > graph_g.n:
        return False
    
    n_g = graph_g.n
    n_q = graph_q.n
    
    # 初始化候选映射矩阵
    M = [[0] * n_g for _ in range(n_q)]
    for u in range(n_q):
        deg_q = graph_q.degree(u)
        for v in range(n_g):
            deg_g = graph_g.degree(v)
            # 初始候选：v的度必须>=u的度
            if deg_g >= deg_q:
                M[u][v] = 1
    
    current_map = [-1] * n_q
    
    return ullmann_search(M, graph_g, graph_q, current_map, 0)


class VF2State:
    """VF2算法的状态"""
    
    def __init__(self, graph_g: Graph, graph_q: Graph):
        self.graph_g = graph_g
        self.graph_q = graph_q
        self.mapping = {}  # mapping[q_node] = g_node
        self.reverse_mapping = {}  # reverse_mapping[g_node] = q_node
    
    def is_feasible(self, q_node: int, g_node: int) -> bool:
        """检查将q_node映射到g_node是否可行"""
        # 规则1: 标签匹配（这里假设无标签图）
        
        # 规则2: 度约束
        deg_q = self.graph_q.degree(q_node)
        deg_g = self.graph_g.degree(g_node)
        if deg_q > deg_g:
            return False
        
        # 规则3: 邻居约束（已映射邻居的连接性）
        for q_prime in self.graph_q.adj[q_node]:
            if q_prime in self.mapping:
                g_prime = self.mapping[q_prime]
                # q_prime已映射，q_node和q_prime必须有边 -> g_node和g_prime也必须有边
                if g_prime not in self.graph_g.adj[g_node]:
                    return False
        
        # 规则4: 逆邻居约束
        for q_prime in self.graph_q.adj[q_node]:
            if q_prime not in self.mapping:
                # q_prime未映射，但g_node的邻居中应该能找到匹配的
                count = 0
                for g_prime in self.graph_g.adj[g_node]:
                    if g_prime not in self.reverse_mapping:
                        count += 1
                if count < 1:  # 至少要有一个候选
                    pass  # 简化处理
        
        return True
    
    def apply_mapping(self, q_node: int, g_node: int):
        """应用映射"""
        self.mapping[q_node] = g_node
        self.reverse_mapping[g_node] = q_node
    
    def undo_mapping(self, q_node: int, g_node: int):
        """撤销映射"""
        del self.mapping[q_node]
        del self.reverse_mapping[g_node]


def vf2_search(state: VF2State, level: int) -> bool:
    """VF2深度优先搜索"""
    n_q = state.graph_q.n
    
    if len(state.mapping) == n_q:
        return True
    
    # 选择下一个要映射的查询节点（使用PITHO规则，选择邻居已在映射中的节点）
    candidates = []
    for q_node in range(n_q):
        if q_node in state.mapping:
            continue
        # 计算有多少已映射邻居
        mapped_neighbors = sum(1 for nb in state.graph_q.adj[q_node] if nb in state.mapping)
        candidates.append((mapped_neighbors, q_node))
    
    if not candidates:
        # 没有已映射邻居的节点，选择度最小的
        for q_node in range(n_q):
            if q_node not in state.mapping:
                candidates.append((0, q_node))
                break
    
    candidates.sort(reverse=True)
    q_node = candidates[0][1]
    
    # 遍历可能的G节点
    for g_node in range(state.graph_g.n):
        if g_node in state.reverse_mapping:
            continue
        
        if state.is_feasible(q_node, g_node):
            state.apply_mapping(q_node, g_node)
            
            if vf2_search(state, level + 1):
                return True
            
            state.undo_mapping(q_node, g_node)
    
    return False


def vf2_isomorphism(graph_g: Graph, graph_q: Graph) -> bool:
    """
    VF2算法主函数：检测graph_q是否是graph_g的子图
    
    参数:
        graph_g: 目标图G
        graph_q: 查询图Q
    
    返回:
        bool: Q是否同构于G的某个子图
    """
    if graph_q.n > graph_g.n:
        return False
    
    state = VF2State(graph_g, graph_q)
    return vf2_search(state, 0)


if __name__ == "__main__":
    # 测试用例1: 简单路径
    print("=== 测试1: 简单路径子图匹配 ===")
    g = Graph(5)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 4)
    g.add_edge(0, 2)
    
    q = Graph(3)
    q.add_edge(0, 1)
    q.add_edge(1, 2)
    
    print(f"Ullmann: 路径(3节点) 在 图中? {ullmann_isomorphism(g, q)}")
    print(f"VF2: 路径(3节点) 在 图中? {vf2_isomorphism(g, q)}")
    
    # 测试用例2: 三角形检测
    print("\n=== 测试2: 三角形子图匹配 ===")
    g2 = Graph(4)
    g2.add_edge(0, 1)
    g2.add_edge(1, 2)
    g2.add_edge(2, 0)
    g2.add_edge(2, 3)
    
    q2 = Graph(3)
    q2.add_edge(0, 1)
    q2.add_edge(1, 2)
    q2.add_edge(2, 0)
    
    print(f"Ullmann: 三角形 在 图中? {ullmann_isomorphism(g2, q2)}")
    print(f"VF2: 三角形 在 图中? {vf2_isomorphism(g2, q2)}")
    
    # 测试用例3: 不存在的子图
    print("\n=== 测试3: 不存在的子图 ===")
    g3 = Graph(4)
    g3.add_edge(0, 1)
    g3.add_edge(1, 2)
    g3.add_edge(2, 3)
    
    q3 = Graph(3)
    q3.add_edge(0, 1)
    q3.add_edge(1, 2)
    q3.add_edge(2, 0)  # 需要三角形，但图是路径
    
    print(f"Ullmann: 三角形 在 路径图中? {ullmann_isomorphism(g3, q3)}")
    print(f"VF2: 三角形 在 路径图中? {vf2_isomorphism(g3, q3)}")
    
    print("\n=== 所有测试完成 ===")
