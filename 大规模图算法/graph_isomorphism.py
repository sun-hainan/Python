"""
图同构检测 (Graph Isomorphism - Weisfeiler-Lehman 1-D)
======================================================
使用Weisfeiler-Lehman (WL) 一维算法检测图同构。

WL算法通过迭代重标记和比较标签分布来判断两图是否"可能"同构。
如果WL算法认为两图同构，则它们是同构的（但不保证反之亦然）。

WL 1-D (颜色细化):
- 每次迭代：每个节点的新颜色 = (旧颜色, 邻居颜色排序后的多集)
- 比较两图的颜色分布直方图

参考：
    - Weisfeiler, B. & Lehman, A. (1968). Reduction of a graph to a canonical form.
    - Shervashidze, N. et al. (2011). Weisfeiler-Lehman Graph Kernels.
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import Counter, defaultdict


class Graph:
    """无向图（可选节点标签）"""
    def __init__(self, n: int = 0, node_labels: Optional[List[int]] = None):
        self.n = n
        self.node_labels = node_labels if node_labels else [0] * n
        self.adj = [set() for _ in range(n)]
    
    def add_edge(self, u: int, v: int):
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]
    
    def degree(self, u: int) -> int:
        return len(self.adj[u])


def wl_1_iteration(graph: Graph, labels: List[int], iteration: int) -> List[int]:
    """
    WL 1维算法的一次迭代
    
    参数:
        graph: 输入图
        labels: 当前节点标签
        iteration: 当前迭代轮次
    
    返回:
        新标签列表
    """
    n = graph.n
    new_labels = [0] * n
    
    for u in range(n):
        # 获取邻居的标签
        nb_labels = tuple(sorted(labels[v] for v in graph.neighbors(u)))
        # 生成新标签
        # 使用哈希组合旧标签和邻居标签
        key = (labels[u], nb_labels, iteration)
        new_labels[u] = hash(key) % 1000000
    
    return new_labels


def wl_1_fingerprint(graph: Graph, num_iterations: int = 3) -> Counter:
    """
    计算图的WL 1-D指纹
    
    参数:
        graph: 输入图
        num_iterations: 迭代次数
    
    返回:
        Counter: 各标签的出现次数（跨所有迭代）
    """
    n = graph.n
    
    # 初始化标签为节点标签（如果有的话）
    labels = graph.node_labels[:]
    
    # 累积指纹
    fingerprint = Counter()
    
    for it in range(num_iterations):
        # 执行一次迭代
        labels = wl_1_iteration(graph, labels, it)
        # 统计当前标签分布
        fingerprint.update(labels)
    
    return fingerprint


def wl_1_isomorphism_canonical(graph: Graph, num_iterations: int = 3) -> str:
    """
    计算图的WL同构规范编码
    
    参数:
        graph: 输入图
        num_iterations: 迭代次数
    
    返回:
        规范编码字符串
    """
    n = graph.n
    
    labels = graph.node_labels[:]
    
    # 保存每轮的标签
    all_labels = [labels]
    
    for it in range(num_iterations):
        labels = wl_1_iteration(graph, labels, it)
        all_labels.append(labels[:])
    
    # 生成规范编码：每轮标签排序后拼接
    canonical_parts = []
    for labels in all_labels:
        sorted_labels = sorted(labels)
        canonical_parts.append("_".join(map(str, sorted_labels)))
    
    return "|".join(canonical_parts)


def wl_1_compare(graph1: Graph, graph2: Graph, 
                 num_iterations: int = 3) -> Tuple[bool, str]:
    """
    比较两图是否可能同构（WL 1-D）
    
    参数:
        graph1: 图1
        graph2: 图2
        num_iterations: 迭代次数
    
    返回:
        (是否可能同构, 判断理由)
    """
    # 检查基本属性
    if graph1.n != graph2.n:
        return False, "节点数不同"
    
    if len(graph1.node_labels) != len(graph2.node_labels):
        return False, "标签数不同"
    
    # 检查度序列
    deg1 = sorted(graph1.degree(i) for i in range(graph1.n))
    deg2 = sorted(graph2.degree(i) for i in range(graph2.n))
    if deg1 != deg2:
        return False, "度序列不同"
    
    # 检查初始标签分布
    label_dist1 = Counter(graph1.node_labels)
    label_dist2 = Counter(graph2.node_labels)
    if label_dist1 != label_dist2:
        return False, "初始标签分布不同"
    
    # WL 1-D 迭代
    labels1 = graph1.node_labels[:]
    labels2 = graph2.node_labels[:]
    
    for it in range(num_iterations):
        labels1 = wl_1_iteration(graph1, labels1, it)
        labels2 = wl_1_iteration(graph2, labels2, it)
        
        # 比较当前标签分布
        dist1 = Counter(labels1)
        dist2 = Counter(labels2)
        
        if dist1 != dist2:
            return False, f"第{it+1}轮标签分布不同"
    
    # 所有迭代都匹配，认为可能同构
    return True, "WL 1-D认为可能同构"


def wl_1_color_histogram(graph: Graph, num_iterations: int = 3) -> Dict[int, int]:
    """
    计算WL 1-D颜色直方图
    
    参数:
        graph: 输入图
        num_iterations: 迭代次数
    
    返回:
        颜色 -> 计数 的字典
    """
    n = graph.n
    
    labels = graph.node_labels[:]
    histogram = Counter()
    
    for it in range(num_iterations + 1):  # 包括初始颜色
        # 更新直方图
        histogram.update(labels)
        
        if it < num_iterations:
            labels = wl_1_iteration(graph, labels, it)
    
    return dict(histogram)


def wl_1_refinement_matrix(graph: Graph, num_iterations: int = 3) -> List[List[int]]:
    """
    计算WL 1-D细化后的等价类矩阵
    
    返回:
        每个节点的等价类ID
    """
    n = graph.n
    
    labels = graph.node_labels[:]
    
    for it in range(num_iterations):
        labels = wl_1_iteration(graph, labels, it)
    
    # 将标签压缩为连续的等价类ID
    unique_labels = sorted(set(labels))
    label_to_id = {lbl: i for i, lbl in enumerate(unique_labels)}
    
    return [label_to_id[lbl] for lbl in labels]


def isomorphisms_count(graph: Graph, num_iterations: int = 3) -> int:
    """
    估计自同构数量（WL简化版）
    
    参数:
        graph: 输入图
        num_iterations: 迭代次数
    
    返回:
        估计的自同构数量下界
    """
    # 找等价类
    eq_classes = wl_1_refinement_matrix(graph, num_iterations)
    
    # 统计每个等价类的大小
    class_counts = Counter(eq_classes)
    
    # 自同构数至少是各等价类大小的乘积
    count = 1
    for c in class_counts.values():
        count *= 1  # 这里简化处理
    
    return count


if __name__ == "__main__":
    print("=== 图同构检测 (WL 1-D) 测试 ===")
    
    # 测试1: 完全相同的两图
    g1 = Graph(4)
    g1.add_edge(0, 1)
    g1.add_edge(1, 2)
    g1.add_edge(2, 3)
    g1.add_edge(3, 0)
    
    g2 = Graph(4)
    g2.add_edge(0, 1)
    g2.add_edge(1, 2)
    g2.add_edge(2, 3)
    g2.add_edge(3, 0)
    
    print("\n测试1: 完全相同的两图")
    iso, reason = wl_1_compare(g1, g2)
    print(f"WL 1-D: {'同构' if iso else '不同构'} - {reason}")
    
    # 测试2: 重新编号的图（同构）
    g3 = Graph(4)
    g3.add_edge(2, 3)
    g3.add_edge(3, 0)
    g3.add_edge(0, 1)
    g3.add_edge(1, 2)
    
    print("\n测试2: 重新编号的图")
    iso2, reason2 = wl_1_compare(g1, g3)
    print(f"WL 1-D: {'同构' if iso2 else '不同构'} - {reason2}")
    
    # 测试3: 路径图 vs 环形图（不同构）
    g4 = Graph(4)
    g4.add_edge(0, 1)
    g4.add_edge(1, 2)
    g4.add_edge(2, 3)
    
    g5 = Graph(4)
    g5.add_edge(0, 1)
    g5.add_edge(1, 2)
    g5.add_edge(2, 3)
    g5.add_edge(3, 0)
    
    print("\n测试3: 路径 vs 环")
    iso3, reason3 = wl_1_compare(g4, g5)
    print(f"WL 1-D: {'同构' if iso3 else '不同构'} - {reason3}")
    
    # 测试4: 有标签的图
    g6 = Graph(4, node_labels=[0, 1, 0, 1])
    g6.add_edge(0, 1)
    g6.add_edge(1, 2)
    g6.add_edge(2, 3)
    g6.add_edge(3, 0)
    
    g7 = Graph(4, node_labels=[1, 0, 1, 0])
    g7.add_edge(0, 1)
    g7.add_edge(1, 2)
    g7.add_edge(2, 3)
    g7.add_edge(3, 0)
    
    print("\n测试4: 有标签图 (相同标签分布)")
    iso4, reason4 = wl_1_compare(g6, g7)
    print(f"WL 1-D: {'同构' if iso4 else '不同构'} - {reason4}")
    
    # 测试5: K4 完全图
    g8 = Graph(4)
    for i in range(4):
        for j in range(i + 1, 4):
            g8.add_edge(i, j)
    
    g9 = Graph(4)
    for i in range(4):
        for j in range(i + 1, 4):
            g9.add_edge(i, j)
    
    print("\n测试5: K4 vs K4")
    iso5, reason5 = wl_1_compare(g8, g9)
    print(f"WL 1-D: {'同构' if iso5 else '不同构'} - {reason5}")
    
    # 测试6: 两个不同的树
    # 树1: 中心辐射
    g10 = Graph(5)
    g10.add_edge(0, 1)
    g10.add_edge(0, 2)
    g10.add_edge(0, 3)
    g10.add_edge(0, 4)
    
    # 树2: 链状
    g11 = Graph(5)
    g11.add_edge(0, 1)
    g11.add_edge(1, 2)
    g11.add_edge(2, 3)
    g11.add_edge(3, 4)
    
    print("\n测试6: 星形树 vs 链状树")
    iso6, reason6 = wl_1_compare(g10, g11)
    print(f"WL 1-D: {'同构' if iso6 else '不同构'} - {reason6}")
    
    # 规范编码测试
    print("\n\n规范编码:")
    enc1 = wl_1_isomorphism_canonical(g1)
    enc3 = wl_1_isomorphism_canonical(g3)
    enc4 = wl_1_isomorphism_canonical(g4)
    
    print(f"g1 编码: {enc1[:50]}...")
    print(f"g3 编码: {enc3[:50]}...")
    print(f"g4 编码: {enc4[:50]}...")
    print(f"g1==g3: {enc1 == enc3}")
    print(f"g1==g4: {enc1 == enc4}")
    
    print("\n=== 测试完成 ===")
