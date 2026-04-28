"""
子图模式挖掘 (Subgraph Pattern Mining - gSpan)
=============================================
实现gSpan算法，用于从图数据库中挖掘频繁子图模式。

gSpan (graph-based Substructure pattern mining):
- 基于深度优先搜索和最小编码原则
- 使用DFS编码表示子图
- 通过右most路径扩展生成候选

参考：
    - Yan, X. & Han, J. (2002). gSpan: Graph-Based Substructure Pattern Mining.
"""

from typing import List, Dict, Set, Tuple, Optional, FrozenSet
from collections import defaultdict
import sys


class Graph:
    """无向图"""
    def __init__(self, n: int = 0, edge_list: Optional[List[Tuple[int, int]]] = None):
        self.n = n
        self.adj = [set() for _ in range(n)]
        if edge_list:
            for u, v in edge_list:
                self.adj[u].add(v)
                self.adj[v].add(u)
    
    def add_edge(self, u: int, v: int):
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]
    
    def degree(self, u: int) -> int:
        return len(self.adj[u])


class Edge:
    """边数据结构"""
    def __init__(self, u: int, v: int, label: int = 0):
        self.u = u
        self.v = v
        self.label = label
    
    def __hash__(self):
        return hash((self.u, self.v, self.label))
    
    def __eq__(self, other):
        return self.u == other.u and self.v == other.v and self.label == other.label


class DFSCode:
    """DFS编码"""
    def __init__(self):
        self.edges = []  # [(from, to, from_label, edge_label, to_label), ...]
    
    def add_edge(self, fr: int, to: int, fr_label: int, edge_label: int, to_label: int):
        self.edges.append((fr, to, fr_label, edge_label, to_label))
    
    def __str__(self):
        return "_".join(f"({e[0]},{e[1]},{e[2]},{e[3]},{e[4]})" for e in self.edges)
    
    def __hash__(self):
        return hash(tuple(self.edges))
    
    def __eq__(self, other):
        return self.edges == other.edges


class Subgraph:
    """子图模式"""
    def __init__(self):
        self.edges = []  # [(u, v, edge_label), ...]
        self.edge_set = set()
    
    def add_edge(self, u: int, v: int, edge_label: int = 0):
        key = (min(u, v), max(u, v), edge_label)
        self.edge_set.add(key)
        self.edges.append((u, v, edge_label))
    
    def right_most_path(self) -> List[int]:
        """获取右most路径"""
        if not self.edges:
            return []
        
        # 简单实现：返回最后一个节点
        last_edge = self.edges[-1]
        return [last_edge[1]]  # to节点
    
    def get_min_dfs_code(self):
        """获取最小的DFS编码"""
        code = DFSCode()
        # 这里简化处理：按边添加顺序
        for i, (u, v, el) in enumerate(self.edges):
            code.add_edge(0, 1, 0, el, 0)  # 简化
        return code


def build_graph_database(graphs: List[Graph]) -> List[Tuple[Graph, int]]:
    """
    构建图数据库
    
    返回:
        [(图, 支持度计数), ...]
    """
    return [(g, 1) for g in graphs]


def support(graph_db: List[Tuple[Graph, int]], subgraph: Subgraph) -> int:
    """
    计算子图的支持度（包含该子图的图的数量）
    
    参数:
        graph_db: 图数据库
        subgraph: 子图
    
    返回:
        支持度
    """
    count = 0
    for g, _ in graph_db:
        if subgraph_is_in_graph(g, subgraph):
            count += 1
    return count


def subgraph_is_in_graph(graph: Graph, subgraph: Subgraph) -> bool:
    """检查子图是否在图中"""
    # 简化检查：边集合包含
    return subgraph.edge_set.issubset(graph.edge_set if hasattr(graph, 'edge_set') else set())


def frequent_edge_mining(graph_db: List[Tuple[Graph, int]], 
                         min_support: int) -> List[Tuple[int, int]]:
    """
    挖掘频繁边（1-边子图）
    
    参数:
        graph_db: 图数据库
        min_support: 最小支持度
    
    返回:
        频繁边列表 [(edge_label, support), ...]
    """
    edge_counts = defaultdict(int)
    
    for g, count in graph_db:
        seen_edges = set()
        for u in range(g.n):
            for v in g.neighbors(u):
                key = (min(u, v), max(u, v))
                if key not in seen_edges:
                    seen_edges.add(key)
                    # 边标签（如果有的话，默认0）
                    edge_counts[0] += count
    
    return [(el, cnt) for el, cnt in edge_counts.items() if cnt >= min_support]


def gspan_mine(graph_db: List[Tuple[Graph, int]], 
               min_support: int, 
               max_num_patterns: int = 100) -> List[Subgraph]:
    """
    gSpan主算法
    
    参数:
        graph_db: 图数据库
        min_support: 最小支持度
        max_num_patterns: 最大挖掘模式数
    
    返回:
        频繁子图列表
    """
    patterns = []
    
    # Step 1: 挖掘频繁边
    freq_edges = frequent_edge_mining(graph_db, min_support)
    
    for edge_label, edge_support in freq_edges:
        # 创建单边子图
        subgraph = Subgraph()
        subgraph.add_edge(0, 1, edge_label)
        patterns.append(subgraph)
        
        # 递归扩展
        _gspan_recursive(graph_db, subgraph, min_support, patterns, max_num_patterns)
    
    return patterns


def _gspan_recursive(graph_db: List[Tuple[Graph, int]], 
                     subgraph: Subgraph,
                     min_support: int,
                     patterns: List[Subgraph],
                     max_num_patterns: int):
    """
    gSpan递归扩展
    
    参数:
        graph_db: 图数据库
        subgraph: 当前子图
        min_support: 最小支持度
        patterns: 收集的模式
        max_num_patterns: 最大模式数
    """
    if len(patterns) >= max_num_patterns:
        return
    
    # 找所有可以扩展的图和嵌入
    embeddings = find_minimal_embeddings(graph_db, subgraph, min_support)
    
    if not embeddings:
        return
    
    # 生成右most路径扩展
    extensions = generate_right_most_extensions(subgraph, embeddings)
    
    for new_subgraph in extensions:
        # 检查支持度
        if support(graph_db, new_subgraph) >= min_support:
            patterns.append(new_subgraph)
            _gspan_recursive(graph_db, new_subgraph, min_support, patterns, max_num_patterns)


def find_minimal_embeddings(graph_db: List[Tuple[Graph, int]], 
                            subgraph: Subgraph,
                            min_support: int) -> List[Tuple[Graph, Dict[int, int]]]:
    """
    找到子图在图数据库中的所有嵌入
    
    返回:
        [(图, 嵌入映射), ...]
    """
    embeddings = []
    
    for g, count in graph_db:
        # 简化：只返回计数
        if support([(g, 1)], subgraph) >= 1:
            embeddings.append((g, {}))  # 简化
    
    return embeddings


def generate_right_most_extensions(subgraph: Subgraph, 
                                   embeddings: List) -> List[Subgraph]:
    """
    生成右most路径扩展
    
    参数:
        subgraph: 当前子图
        embeddings: 嵌入列表
    
    返回:
        扩展后的子图列表
    """
    extensions = []
    
    # 获取右most路径
    rm_path = subgraph.right_most_path()
    if not rm_path:
        return extensions
    
    rm_node = rm_path[-1]
    
    # 在右most路径的最后一个节点上扩展
    # 方式1：前向扩展（添加新节点）
    new_subgraph1 = Subgraph()
    for e in subgraph.edges:
        new_subgraph1.add_edge(e[0], e[1], e[2])
    new_subgraph1.add_edge(rm_node, len(subgraph.edges), 0)  # 新节点
    extensions.append(new_subgraph1)
    
    # 方式2：后向扩展（连接到已有节点）
    for i in range(len(subgraph.edges)):
        new_subgraph2 = Subgraph()
        for e in subgraph.edges:
            new_subgraph2.add_edge(e[0], e[1], e[2])
        new_subgraph2.add_edge(rm_node, i, 0)  # 回边
        extensions.append(new_subgraph2)
    
    return extensions


def compute_dfs_code(subgraph: Subgraph) -> DFSCode:
    """
    计算子图的DFS编码
    
    参数:
        subgraph: 子图
    
    返回:
        DFSCode
    """
    code = DFSCode()
    
    # 简化：从边列表生成DFS编码
    # 假设子图是连通的，按顺序添加边
    node_labels = [0] * (max(max(e[0], e[1]) for e in subgraph.edges) + 1)
    
    for u, v, el in subgraph.edges:
        fr = u
        to = v
        fr_label = node_labels[fr]
        to_label = node_labels[to]
        code.add_edge(fr, to, fr_label, el, to_label)
    
    return code


def canonical_dfs_code(subgraph: Subgraph) -> DFSCode:
    """
    计算子图的规范DFS编码（所有可能DFS序中的最小者）
    
    参数:
        subgraph: 子图
    
    返回:
        最小DFSCode
    """
    # 简化：直接使用compute_dfs_code
    return compute_dfs_code(subgraph)


def _build_graph_with_edge_set(n: int, edges: List[Tuple[int, int]]) -> Graph:
    """构建带edge_set的图"""
    g = Graph(n)
    g.edge_set = set()
    for u, v in edges:
        g.add_edge(u, v)
        key = (min(u, v), max(u, v), 0)
        g.edge_set.add(key)
    return g


if __name__ == "__main__":
    print("=== gSpan子图模式挖掘测试 ===")
    
    # 创建测试图数据库
    # 图1: 三角形
    g1 = _build_graph_with_edge_set(3, [(0, 1), (1, 2), (2, 0)])
    
    # 图2: 菱形（两个三角形共享一条边）
    g2 = _build_graph_with_edge_set(4, [(0, 1), (1, 2), (2, 0), (0, 3), (3, 2)])
    
    # 图3: 四边形
    g3 = _build_graph_with_edge_set(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    
    graph_db = [(g1, 1), (g2, 1), (g3, 1)]
    
    print(f"图数据库: {len(graph_db)} 个图")
    
    # 挖掘频繁子图
    min_support = 2
    print(f"\n最小支持度: {min_support}")
    
    patterns = gspan_mine(graph_db, min_support, max_num_patterns=20)
    
    print(f"\n挖掘到 {len(patterns)} 个频繁子图:")
    for i, p in enumerate(patterns[:10]):
        print(f"  模式{i+1}: {len(p.edges)} 条边")
    
    # 测试支持度计算
    print("\n\n子图支持度测试:")
    sub_tri = Subgraph()
    sub_tri.add_edge(0, 1, 0)
    sub_tri.add_edge(1, 2, 0)
    sub_tri.add_edge(2, 0, 0)
    
    sup_tri = support(graph_db, sub_tri)
    print(f"三角形支持度: {sup_tri}")
    
    sub_edge = Subgraph()
    sub_edge.add_edge(0, 1, 0)
    sup_edge = support(graph_db, sub_edge)
    print(f"单边支持度: {sup_edge}")
    
    # DFS编码测试
    print("\n\nDFS编码测试:")
    code = compute_dfs_code(sub_tri)
    print(f"三角形DFS编码: {code}")
    
    print("\n=== 测试完成 ===")
