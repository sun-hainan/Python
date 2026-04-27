# -*- coding: utf-8 -*-

"""

算法实现：数据挖掘 / pagerank



本文件实现 pagerank 相关的算法功能。

"""



import numpy as np

from typing import Dict, List, Set, Tuple, Optional

from collections import defaultdict

import random





class PageRank:

    """

    PageRank算法实现

    

    支持多种计算方法：

    - 幂迭代法 (Power Iteration)

    - 矩阵分解法

    - 随机游走模拟

    """

    

    def __init__(self, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6):

        """

        参数:

            damping: 阻尼因子

            max_iter: 最大迭代次数

            tol: 收敛阈值

        """

        self.damping = damping

        self.max_iter = max_iter

        self.tol = tol

        

        self.n_nodes = 0

        self.node_to_idx: Dict[str, int] = {}

        self.idx_to_node: Dict[int, str] = {}

        self.transition_matrix: Optional[np.ndarray] = None

        self.ranks: Optional[np.ndarray] = None

        self.converged = False

        self.n_iterations = 0

    

    def build_graph(self, edges: List[Tuple[str, str]]) -> 'PageRank':

        """

        从边列表构建图

        

        参数:

            edges: (source, target) 列表，表示从source到target的链接

        """

        # 构建节点映射

        nodes = set()

        for src, tgt in edges:

            nodes.add(src)

            nodes.add(tgt)

        

        self.n_nodes = len(nodes)

        self.node_to_idx = {node: i for i, node in enumerate(sorted(nodes))}

        self.idx_to_node = {i: node for node, i in self.node_to_idx.items()}

        

        # 构建转移矩阵

        # M[i,j] = 1/L(j) 如果j链接到i，否则0

        M = np.zeros((self.n_nodes, self.n_nodes))

        

        out_degree = defaultdict(int)

        for src, tgt in edges:

            out_degree[src] += 1

        

        for src, tgt in edges:

            i = self.node_to_idx[tgt]  # 目标节点（被链接的）

            j = self.node_to_idx[src]  # 源节点（链接的）

            

            # 从节点j到节点i的转移概率

            M[i, j] = 1.0 / out_degree[src]

        

        self.transition_matrix = M

        

        return self

    

    def power_iteration(self) -> 'PageRank':

        """

        幂迭代法计算PageRank

        

        迭代公式：

        r_{t+1} = (1-d)/N * 1 + d * M * r_t

        """

        n = self.n_nodes

        d = self.damping

        

        # 初始rank（均匀分布）

        r = np.ones(n) / n

        

        # 阻尼因子向量

        damping_vector = (1 - d) / n * np.ones(n)

        

        for iteration in range(self.max_iter):

            # 迭代计算

            r_new = damping_vector + d * self.transition_matrix @ r

            

            # 检查收敛

            diff = np.linalg.norm(r_new - r, 1)

            r = r_new

            self.n_iterations = iteration + 1

            

            if diff < self.tol:

                self.converged = True

                break

        

        self.ranks = r

        return self

    

    def compute(self) -> 'PageRank':

        """计算PageRank"""

        return self.power_iteration()

    

    def get_rank(self, node: str) -> float:

        """获取指定节点的PageRank"""

        if node not in self.node_to_idx:

            return 0.0

        idx = self.node_to_idx[node]

        return self.ranks[idx] if self.ranks is not None else 0.0

    

    def get_top_k(self, k: int = 10) -> List[Tuple[str, float]]:

        """获取PageRank最高的k个节点"""

        if self.ranks is None:

            return []

        

        indexed_ranks = [(self.idx_to_node[i], rank) for i, rank in enumerate(self.ranks)]

        return sorted(indexed_ranks, key=lambda x: -x[1])[:k]

    

    def get_all_ranks(self) -> Dict[str, float]:

        """获取所有节点的PageRank"""

        if self.ranks is None:

            return {}

        return {self.idx_to_node[i]: rank for i, rank in enumerate(self.ranks)}





class PersonalizedPageRank(PageRank):

    """

    个性化PageRank

    

    从一组种子节点进行随机游走

    用于推荐、链接预测等

    """

    

    def __init__(self, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6):

        super().__init__(damping, max_iter, tol)

        self.teleport_set: Set[int] = set()  # 种子节点

    

    def set_teleport_set(self, nodes: List[str]) -> 'PersonalizedPageRank':

        """设置跳转目标集合（种子节点）"""

        self.teleport_set = set()

        for node in nodes:

            if node in self.node_to_idx:

                self.teleport_set.add(self.node_to_idx[node])

        return self

    

    def power_iteration(self) -> 'PageRank':

        """带个性化跳转的幂迭代"""

        n = self.n_nodes

        d = self.damping

        

        # 初始化（均匀分布在种子节点）

        r = np.zeros(n)

        if self.teleport_set:

            prob = 1.0 / len(self.teleport_set)

            for idx in self.teleport_set:

                r[idx] = prob

        

        for iteration in range(self.max_iter):

            # 个性化跳转

            r_new = (1 - d) * r.copy()

            

            # 加上从其他节点的贡献

            r_new += d * self.transition_matrix @ r

            

            # 检查收敛

            diff = np.linalg.norm(r_new - r, 1)

            r = r_new

            self.n_iterations = iteration + 1

            

            if diff < self.tol:

                self.converged = True

                break

        

        self.ranks = r

        return self





class RandomWalkSimulator:

    """

    随机游走模拟器

    

    通过随机游走模拟估计PageRank

    适合大规模图

    """

    

    def __init__(self, edges: List[Tuple[str, str]], damping: float = 0.85):

        self.damping = damping

        

        # 构建邻接表

        self.graph: Dict[str, Set[str]] = defaultdict(set)

        self.inverse_graph: Dict[str, Set[str]] = defaultdict(set)

        

        for src, tgt in edges:

            self.graph[src].add(tgt)

            self.inverse_graph[tgt].add(src)

        

        self.nodes = list(self.graph.keys())

    

    def random_walk(self, start: str, n_steps: int, n_walks: int = 100) -> Dict[str, float]:

        """

        从start节点进行随机游走

        

        返回:

            各节点被访问的频率

        """

        visit_counts = defaultdict(int)

        

        for _ in range(n_walks):

            current = start

            

            for _ in range(n_steps):

                # 以概率d沿着链接走，否则随机跳转

                if random.random() < self.damping and current in self.graph:

                    # 沿着出链随机走一步

                    neighbors = list(self.graph[current])

                    if neighbors:

                        current = random.choice(neighbors)

                else:

                    # 随机跳转到任意节点

                    current = random.choice(self.nodes)

                

                visit_counts[current] += 1

        

        # 归一化

        total = sum(visit_counts.values())

        return {node: count / total for node, count in visit_counts.items()}





def generate_scale_free_graph(n: int, m: int = 2) -> List[Tuple[str, str]]:

    """

    生成无标度网络（Barabási-Albert模型）

    

    参数:

        n: 节点数

        m: 每个新节点连接的边数

    """

    edges = []

    

    # 初始完全图（m+1个节点）

    initial_nodes = [f"node_{i}" for i in range(m + 1)]

    for i in range(len(initial_nodes)):

        for j in range(i + 1, len(initial_nodes)):

            edges.append((initial_nodes[i], initial_nodes[j]))

    

    # 累计度

    degrees = {node: m for node in initial_nodes}

    

    # 添加剩余节点

    for new_id in range(m + 1, n):

        new_node = f"node_{new_id}"

        

        # 按度比例选择连接目标

        targets = set()

        total_degree = sum(degrees.values())

        

        while len(targets) < m:

            # 概率与度成正比

            r = random.random() * total_degree

            cumsum = 0

            for node in degrees:

                cumsum += degrees[node]

                if cumsum >= r:

                    targets.add(node)

                    if len(targets) == m:

                        break

        

        # 添加边

        for target in targets:

            edges.append((new_node, target))

            degrees[new_node] = degrees.get(new_node, 0) + 1

            degrees[target] += 1

    

    return edges





# ==================== 测试代码 ====================

if __name__ == "__main__":

    print("=" * 50)

    print("PageRank算法测试")

    print("=" * 50)

    

    # 测试图

    edges = [

        ('A', 'B'), ('A', 'C'), ('A', 'D'),

        ('B', 'A'), ('B', 'D'),

        ('C', 'A'), ('C', 'D'),

        ('D', 'A'), ('D', 'B'), ('D', 'C'),

        ('E', 'D'), ('E', 'A'),

        ('F', 'D'), ('G', 'D'),

    ]

    

    print("\n--- 基本PageRank测试 ---")

    

    # 构建图并计算

    pr = PageRank(damping=0.85)

    pr.build_graph(edges).compute()

    

    print(f"收敛: {pr.converged}, 迭代次数: {pr.n_iterations}")

    print("\nPageRank结果:")

    

    for node, rank in pr.get_all_ranks().items():

        print(f"  {node}: {rank:.4f}")

    

    print("\nTop 3:")

    for node, rank in pr.get_top_k(3):

        print(f"  {node}: {rank:.4f}")

    

    # 个性化PageRank测试

    print("\n--- 个性化PageRank测试 ---")

    

    ppr = PersonalizedPageRank(damping=0.85)

    ppr.build_graph(edges)

    ppr.set_teleport_set(['A', 'B'])  # 只从A和B跳转

    ppr.compute()

    

    print("从节点A和B个性化PageRank:")

    for node, rank in ppr.get_all_ranks().items():

        print(f"  {node}: {rank:.4f}")

    

    # 无标度网络测试

    print("\n--- 无标度网络测试 ---")

    

    import time

    

    # 生成网络

    n_nodes = 1000

    print(f"生成 BA模型网络: {n_nodes} 节点")

    

    ba_edges = generate_scale_free_graph(n_nodes, m=2)

    print(f"边数: {len(ba_edges)}")

    

    # 计算PageRank

    pr_ba = PageRank(damping=0.85, max_iter=200)

    

    start = time.time()

    pr_ba.build_graph(ba_edges).compute()

    elapsed = time.time() - start

    

    print(f"计算时间: {elapsed:.3f}秒")

    print(f"收敛: {pr_ba.converged}, 迭代次数: {pr_ba.n_iterations}")

    

    # PageRank分布

    ranks = list(pr_ba.ranks)

    print(f"\nPageRank分布:")

    print(f"  最小值: {min(ranks):.6f}")

    print(f"  最大值: {max(ranks):.6f}")

    print(f"  均值: {np.mean(ranks):.6f}")

    print(f"  标准差: {np.std(ranks):.6f}")

    

    # Top 10

    print("\nTop 10 页面:")

    for node, rank in pr_ba.get_top_k(10):

        print(f"  {node}: {rank:.6f}")

    

    # 随机游走对比

    print("\n--- 随机游走 vs 幂迭代 ---")

    

    small_edges = generate_scale_free_graph(100, m=2)

    

    # 幂迭代

    pr1 = PageRank()

    start = time.time()

    pr1.build_graph(small_edges).compute()

    power_time = time.time() - start

    

    # 随机游走

    rws = RandomWalkSimulator(small_edges)

    start = time.time()

    rw_result = rws.random_walk('node_0', n_steps=1000, n_walks=100)

    rw_time = time.time() - start

    

    print(f"幂迭代: {power_time:.4f}秒")

    print(f"随机游走: {rw_time:.4f}秒")

    

    # 对比结果

    pr_result = pr1.get_all_ranks()

    

    print("\n结果对比 (前5个):")

    print(f"{'节点':<10} {'幂迭代':<12} {'随机游走':<12}")

    for node in list(pr1.nodes)[:5]:

        print(f"{node:<10} {pr_result.get(node, 0):.6f}      {rw_result.get(node, 0):.6f}")

    

    # 实际应用：网页重要性排序

    print("\n--- 实际应用：网页重要性 ---")

    

    web_edges = [

        ('主页', '产品页'),

        ('主页', '关于我们'),

        ('主页', '联系页'),

        ('产品页', '主页'),

        ('产品页', '详情页1'),

        ('产品页', '详情页2'),

        ('详情页1', '产品页'),

        ('详情页2', '产品页'),

        ('关于我们', '主页'),

        ('联系页', '主页'),

        ('博客1', '主页'),

        ('博客2', '主页'),

        ('博客3', '主页'),

        ('产品页', '博客1'),

        ('产品页', '博客2'),

    ]

    

    pr_web = PageRank()

    pr_web.build_graph(web_edges).compute()

    

    print("网页重要性排名:")

    for rank, (node, score) in enumerate(pr_web.get_top_k(len(web_edges)), 1):

        print(f"  {rank}. {node}: {score:.4f}")

