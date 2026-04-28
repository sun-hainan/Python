"""
图核方法 (Graph Kernel Methods)
===============================
实现 Weisfeiler-Lehman (WL) 核和随机游走核，用于图相似度计算。

WL核：通过迭代重标记过程提取图的结构特征，基于多集匹配计算相似度。
随机游走核：通过比较两图中相同长度随机游走路径的数量计算相似度。

参考：
    - Shervashidze, N. et al. (2011). Weisfeiler-Lehman graph kernels.
    - Gärtner, T. et al. (2003). On graph kernels.
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter
import copy


class Graph:
    """图数据结构（无向图）"""
    
    def __init__(self, n: int = 0, node_labels: Optional[List[int]] = None):
        self.n = n  # 节点数量
        # 节点标签：如果未提供，使用节点索引作为标签
        self.node_labels = node_labels if node_labels else list(range(n))
        self.adj = [set() for _ in range(n)]  # 邻接集合
    
    def add_edge(self, u: int, v: int):
        """添加无向边"""
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        """返回节点u的邻居集合"""
        return self.adj[u]
    
    def degree(self, u: int) -> int:
        """返回节点u的度数"""
        return len(self.adj[u])


# ==================== Weisfeiler-Lehman 核 ====================

def wl_relabel(graph: Graph, labels: Dict[int, int], 
               iteration: int) -> Tuple[Dict[int, int], Dict[str, int]]:
    """
    Weisfeiler-Lehman 重标记步骤
    
    参数:
        graph: 输入图
        labels: 当前节点标签
        iteration: 当前迭代次数
    
    返回:
        (新标签字典, 标签频率统计)
    """
    new_labels = {}
    label_counts = Counter()
    
    for node in range(graph.n):
        # 获取邻居的当前标签（排序以保证一致性）
        neighbor_labels = tuple(sorted(labels[nb] for nb in graph.neighbors(node)))
        # 构造多集字符串
        multiset_str = f"{labels[node]}|{neighbor_labels}"
        # 哈希生成新标签
        new_label = hash((multiset_str, iteration)) % 100000
        new_labels[node] = new_label
        label_counts[new_label] += 1
    
    return new_labels, dict(label_counts)


def wl_kernel_single_iteration(graph: Graph, labels: Dict[int, int], 
                                 iteration: int) -> Tuple[Dict[int, int], int]:
    """
    执行一次WL迭代
    
    返回:
        (新标签, 哈希冲突计数)
    """
    # 简化版本：使用邻居标签的排序列表作为键
    new_labels = {}
    label_set = set()
    
    for node in range(graph.n):
        # 收集邻居标签
        nb_labels = [labels[nb] for nb in graph.neighbors(node)]
        nb_labels.sort()
        # 创建新标签
        key = (labels[node], tuple(nb_labels), iteration)
        new_label = hash(key) % 1000000
        new_labels[node] = new_label
        label_set.add(new_label)
    
    return new_labels, len(label_set)


def compute_wl_fingerprint(graph: Graph, num_iterations: int = 3) -> Counter:
    """
    计算图的WL指纹（多次迭代后的标签分布）
    
    参数:
        graph: 输入图
        num_iterations: WL迭代次数
    
    返回:
        Counter: 各标签的出现次数
    """
    # 初始化标签为节点索引
    labels = {i: graph.node_labels[i] for i in range(graph.n)}
    
    # 累积标签计数（使用列表保存每轮的计数）
    all_counts = []
    
    for it in range(num_iterations):
        labels, _ = wl_kernel_single_iteration(graph, labels, it)
        # 统计当前标签分布
        count = Counter(labels.values())
        all_counts.append(count)
    
    # 合并所有迭代的标签计数
    fingerprint = Counter()
    for count in all_counts:
        fingerprint.update(count)
    
    return fingerprint


def wl_kernel(graph1: Graph, graph2: Graph, num_iterations: int = 3) -> float:
    """
    Weisfeiler-Lehman 核：计算两图的相似度
    
    参数:
        graph1: 图1
        graph2: 图2
        num_iterations: WL迭代次数
    
    返回:
        float: WL核值（公共子结构计数）
    """
    # 初始化标签
    labels1 = {i: graph1.node_labels[i] for i in range(graph1.n)}
    labels2 = {i: graph2.node_labels[i] for i in range(graph2.n)}
    
    kernel_value = 0.0
    
    for it in range(num_iterations):
        # 执行一次WL重标记
        labels1, _ = wl_kernel_single_iteration(graph1, labels1, it)
        labels2, _ = wl_kernel_single_iteration(graph2, labels2, it)
        
        # 统计当前标签分布
        count1 = Counter(labels1.values())
        count2 = Counter(labels2.values())
        
        # 计算公共标签的数量（内积）
        common_labels = set(count1.keys()) & set(count2.keys())
        iter_kernel = sum(min(count1[l], count2[l]) for l in common_labels)
        
        kernel_value += iter_kernel
    
    return kernel_value


def wl_subtree_kernel(graph1: Graph, graph2: Graph, num_iterations: int = 3) -> float:
    """
    WL子树核：只考虑当前节点标签，不考虑邻居多集
    
    参数:
        graph1: 图1
        graph2: 图2
        num_iterations: 迭代次数
    
    返回:
        float: 子树核值
    """
    labels1 = {i: graph1.node_labels[i] for i in range(graph1.n)}
    labels2 = {i: graph2.node_labels[i] for i in range(graph2.n)}
    
    kernel_value = 0.0
    
    for it in range(num_iterations):
        # 统计标签分布
        count1 = Counter(labels1.values())
        count2 = Counter(labels2.values())
        
        # 计算内积
        common_labels = set(count1.keys()) & set(count2.keys())
        iter_kernel = sum(count1[l] * count2[l] for l in common_labels)
        
        kernel_value += iter_kernel
        
        # 重标记（简化版本：只用迭代次数影响哈希）
        new_labels1 = {}
        new_labels2 = {}
        for node in range(graph1.n):
            new_labels1[node] = hash((labels1[node], it)) % 1000000
        for node in range(graph2.n):
            new_labels2[node] = hash((labels2[node], it)) % 1000000
        labels1 = new_labels1
        labels2 = new_labels2
    
    return kernel_value


def wl_optimal_assignment_kernel(graph1: Graph, graph2: Graph, 
                                  num_iterations: int = 3) -> float:
    """
    WL最优分配核 (WL-OA)
    使用匈牙利算法找最优节点匹配，基于匹配数计算核值
    
    参数:
        graph1: 图1
        graph2: 图2
        num_iterations: 迭代次数
    
    返回:
        float: OA核值
    """
    labels1 = {i: graph1.node_labels[i] for i in range(graph1.n)}
    labels2 = {i: graph2.node_labels[i] for i in range(graph2.n)}
    
    n1, n2 = graph1.n, graph2.n
    max_n = max(n1, n2)
    
    kernel_value = 0.0
    
    for it in range(num_iterations):
        # 构建标签相似度矩阵
        similarity_matrix = [[0.0] * max_n for _ in range(max_n)]
        
        for i in range(n1):
            for j in range(n2):
                similarity_matrix[i][j] = 1.0 if labels1[i] == labels2[j] else 0.0
        
        # 使用贪心匹配作为匈牙利算法的近似
        matched = [False] * n2
        match_count = 0
        
        # 按相似度降序贪婪匹配
        pairs = []
        for i in range(n1):
            for j in range(n2):
                if labels1[i] == labels2[j]:
                    pairs.append((i, j))
        
        # 贪心匹配
        for i, j in pairs:
            if not matched[j]:
                matched[j] = True
                match_count += 1
                break
        
        kernel_value += match_count
        
        # WL重标记
        labels1, _ = wl_kernel_single_iteration(graph1, labels1, it)
        labels2, _ = wl_kernel_single_iteration(graph2, labels2, it)
    
    return kernel_value


# ==================== 随机游走核 ====================

def random_walk_kernel(graph1: Graph, graph2: Graph, 
                       walk_length: int = 3, num_walks: int = 100) -> float:
    """
    随机游走核：通过比较随机游走路径计算图相似度
    
    参数:
        graph1: 图1
        graph2: 图2
        walk_length: 随机游走长度
        num_walks: 每节点的游走次数
    
    返回:
        float: 核值
    """
    import random
    
    def generate_walk_proba(graph: Graph, start: int, length: int) -> List[int]:
        """生成一条随机游走路径（返回节点序列的概率分布）"""
        walk = [start]
        current = start
        for _ in range(length - 1):
            neighbors = list(graph.neighbors(current))
            if not neighbors:
                break
            # 均匀随机选择
            current = random.choice(neighbors)
            walk.append(current)
        return walk
    
    def walk_spectrum(graph: Graph, walk_length: int, num_walks: int) -> Counter:
        """计算图的游走谱（游走路径的多重集指纹）"""
        walk_counts = Counter()
        
        for start in range(graph.n):
            for _ in range(num_walks):
                walk = generate_walk_proba(graph, start, walk_length)
                # 将游走转换为字符串作为键
                walk_key = tuple(walk)
                walk_counts[walk_key] += 1
        
        return walk_counts
    
    # 生成两图的游走谱
    spectrum1 = walk_spectrum(graph1, walk_length, num_walks)
    spectrum2 = walk_spectrum(graph2, walk_length, num_walks)
    
    # 计算核值（共同游走的数量）
    kernel = 0.0
    for walk, count1 in spectrum1.items():
        if walk in spectrum2:
            kernel += count1 * spectrum2[walk]
    
    return kernel


def shortest_path_kernel(graph1: Graph, graph2: Graph) -> float:
    """
    最短路径核：基于两节点间最短路径长度的分布计算核值
    
    参数:
        graph1: 图1
        graph2: 图2
    
    返回:
        float: 核值
    """
    from collections import deque
    
    def bfs_shortest_path(graph: Graph, start: int) -> Dict[int, int]:
        """BFS计算从start到所有节点的最短路径"""
        dist = {start: 0}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            for neighbor in graph.neighbors(current):
                if neighbor not in dist:
                    dist[neighbor] = dist[current] + 1
                    queue.append(neighbor)
        
        return dist
    
    def compute_distance_distribution(graph: Graph) -> Counter:
        """计算图中所有节点对距离的分布"""
        all_pairs = []
        
        for start in range(graph.n):
            dist = bfs_shortest_path(graph, start)
            for target, d in dist.items():
                if start < target:  # 只计一次
                    all_pairs.append(d)
        
        return Counter(all_pairs)
    
    dist1 = compute_distance_distribution(graph1)
    dist2 = compute_distance_distribution(graph2)
    
    # 计算核值（共同距离计数的内积）
    all_distances = set(dist1.keys()) | set(dist2.keys())
    kernel = sum(dist1[d] * dist2[d] for d in all_distances)
    
    return float(kernel)


def compute_kernel_matrix(graphs: List[Graph], kernel_type: str = "wl",
                          num_iterations: int = 3) -> List[List[float]]:
    """
    为一组图计算核矩阵
    
    参数:
        graphs: 图列表
        kernel_type: 核类型 ("wl", "random_walk", "shortest_path")
        num_iterations: WL迭代次数
    
    返回:
        n x n 核矩阵
    """
    n = len(graphs)
    kernel_matrix = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i, n):
            if kernel_type == "wl":
                k = wl_kernel(graphs[i], graphs[j], num_iterations)
            elif kernel_type == "random_walk":
                k = random_walk_kernel(graphs[i], graphs[j])
            elif kernel_type == "shortest_path":
                k = shortest_path_kernel(graphs[i], graphs[j])
            else:
                raise ValueError(f"Unknown kernel type: {kernel_type}")
            
            kernel_matrix[i][j] = k
            kernel_matrix[j][i] = k
    
    return kernel_matrix


if __name__ == "__main__":
    print("=== 图核方法测试 ===")
    
    # 创建测试图：两个三角形
    g1 = Graph(3)
    g1.add_edge(0, 1)
    g1.add_edge(1, 2)
    g1.add_edge(2, 0)
    
    g2 = Graph(3)
    g2.add_edge(0, 1)
    g2.add_edge(1, 2)
    g2.add_edge(2, 0)
    
    # 创建测试图：一条路径
    g3 = Graph(3)
    g3.add_edge(0, 1)
    g3.add_edge(1, 2)
    
    print("\n--- WL核测试 ---")
    k1 = wl_kernel(g1, g2, num_iterations=3)
    print(f"三角形 vs 三角形 WL核 = {k1}")
    
    k2 = wl_kernel(g1, g3, num_iterations=3)
    print(f"三角形 vs 路径 WL核 = {k2}")
    
    print("\n--- WL子树核测试 ---")
    k3 = wl_subtree_kernel(g1, g2, num_iterations=3)
    print(f"三角形 vs 三角形 WL子树核 = {k3}")
    
    print("\n--- WL-OA核测试 ---")
    k4 = wl_optimal_assignment_kernel(g1, g2, num_iterations=3)
    print(f"三角形 vs 三角形 WL-OA核 = {k4}")
    
    print("\n--- 最短路径核测试 ---")
    k5 = shortest_path_kernel(g1, g2)
    print(f"三角形 vs 三角形 最短路径核 = {k5}")
    
    k6 = shortest_path_kernel(g1, g3)
    print(f"三角形 vs 路径 最短路径核 = {k6}")
    
    print("\n--- 核矩阵计算 ---")
    all_graphs = [g1, g2, g3]
    K = compute_kernel_matrix(all_graphs, kernel_type="wl", num_iterations=3)
    print("WL核矩阵:")
    for row in K:
        print([f"{x:.1f}" for x in row])
    
    print("\n=== 测试完成 ===")
