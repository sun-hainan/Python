# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / graph_sampling_graphsaint



本文件实现 graph_sampling_graphsaint 相关的算法功能。

"""



import numpy as np

import random





# ============================

# 图数据结构的辅助函数

# ============================



def build_adj_list(adj):

    """

    从邻接矩阵构建邻接表

    

    参数:

        adj: 邻接矩阵 (N, N)

    返回:

        adj_list: 邻接表 {node: [neighbors]}

    """

    N = adj.shape[0]

    adj_list = {i: [] for i in range(N)}

    

    for i in range(N):

        for j in range(N):

            if adj[i, j] > 0 and i != j:

                adj_list[i].append(j)

    

    return adj_list





def build_edge_list(adj):

    """

    从邻接矩阵构建边列表

    

    参数:

        adj: 邻接矩阵

    返回:

        edges: 边列表 [(src, dst), ...]

        edge_weights: 边权重列表

    """

    edges = []

    edge_weights = []

    

    N = adj.shape[0]

    for i in range(N):

        for j in range(i + 1, N):  # 无向图，只取上三角

            if adj[i, j] > 0:

                edges.append((i, j))

                edges.append((j, i))  # 双向

                edge_weights.append(adj[i, j])

                edge_weights.append(adj[i, j])

    

    return np.array(edges), np.array(edge_weights)





# ============================

# 节点采样

# ============================



def node_sampling(adj, num_samples, prob_distribution=None):

    """

    节点采样

    

    参数:

        adj: 邻接矩阵 (N, N)

        num_samples: 采样节点数

        prob_distribution: 节点采样概率（可选）

    返回:

        sampled_nodes: 采样的节点列表

        subgraph_adj: 子图邻接矩阵

    """

    N = adj.shape[0]

    

    if prob_distribution is None:

        # 均匀采样

        prob_distribution = np.ones(N) / N

    else:

        prob_distribution = prob_distribution / prob_distribution.sum()

    

    # 采样节点

    sampled_nodes = np.random.choice(N, size=min(num_samples, N), replace=False, p=prob_distribution)

    sampled_nodes = list(sampled_nodes)

    

    # 构建子图邻接矩阵

    subgraph_adj = adj[np.ix_(sampled_nodes, sampled_nodes)]

    

    return sampled_nodes, subgraph_adj





def degree_based_node_sampling(adj, num_samples):

    """

    基于度的节点采样（优先采样高度节点）

    

    参数:

        adj: 邻接矩阵

        num_samples: 采样数

    返回:

        sampled_nodes: 采样的节点

        subgraph_adj: 子图邻接矩阵

    """

    N = adj.shape[0]

    

    # 度作为采样概率

    degrees = np.sum(adj > 0, axis=1).astype(float)

    degrees = degrees ** 0.5  # 开方避免极端偏向

    prob = degrees / degrees.sum()

    

    return node_sampling(adj, num_samples, prob)





def importance_based_node_sampling(adj, num_samples, node_importance=None):

    """

    基于重要性的节点采样

    

    参数:

        adj: 邻接矩阵

        num_samples: 采样数

        node_importance: 节点重要性分数（PageRank等）

    返回:

        sampled_nodes, subgraph_adj

    """

    if node_importance is None:

        # 默认使用度

        return degree_based_node_sampling(adj, num_samples)

    

    prob = node_importance / node_importance.sum()

    return node_sampling(adj, num_samples, prob)





# ============================

# 边采样

# ============================



def edge_sampling(adj, num_samples, method='uniform'):

    """

    边采样

    

    参数:

        adj: 邻接矩阵 (N, N)

        num_samples: 采样边数

        method: 采样方法 ('uniform', 'degree_biased')

    返回:

        sampled_edges: 采样的边列表

        sampled_adj: 采样后的邻接矩阵

    """

    N = adj.shape[0]

    

    # 构建边列表

    edges = []

    edge_probs = []

    

    for i in range(N):

        for j in range(i + 1, N):

            if adj[i, j] > 0:

                edges.append((i, j))

                if method == 'uniform':

                    edge_probs.append(1.0)

                elif method == 'degree_biased':

                    # 基于两端点的度

                    deg_i = np.sum(adj[i] > 0)

                    deg_j = np.sum(adj[j] > 0)

                    edge_probs.append(deg_i + deg_j)

    

    if len(edges) == 0:

        return [], np.zeros((0, 0))

    

    edge_probs = np.array(edge_probs)

    edge_probs = edge_probs / edge_probs.sum()

    

    # 采样边

    num_to_sample = min(num_samples, len(edges))

    sampled_indices = np.random.choice(len(edges), size=num_to_sample, replace=False, p=edge_probs)

    sampled_edges = [edges[i] for i in sampled_indices]

    

    # 构建采样后的邻接矩阵

    sampled_adj = np.zeros((N, N))

    for i, j in sampled_edges:

        sampled_adj[i, j] = adj[i, j]

        sampled_adj[j, i] = adj[j, i]

    

    return sampled_edges, sampled_adj





def stratified_edge_sampling(adj, num_samples):

    """

    分层边采样：确保不同度的边都被采样

    

    参数:

        adj: 邻接矩阵

        num_samples: 采样数

    返回:

        sampled_edges, sampled_adj

    """

    N = adj.shape[0]

    

    # 将边按度分组

    low_degree = []

    mid_degree = []

    high_degree = []

    

    for i in range(N):

        for j in range(i + 1, N):

            if adj[i, j] > 0:

                deg_i = np.sum(adj[i] > 0)

                deg_j = np.sum(adj[j] > 0)

                avg_deg = (deg_i + deg_j) / 2

                

                edge = (i, j)

                if avg_deg < 3:

                    low_degree.append(edge)

                elif avg_deg < 7:

                    mid_degree.append(edge)

                else:

                    high_degree.append(edge)

    

    # 每层采样相同数量的边

    edges_per_stratum = num_samples // 3

    sampled_edges = []

    

    for stratum in [low_degree, mid_degree, high_degree]:

        if len(stratum) > 0:

            num = min(edges_per_stratum, len(stratum))

            indices = np.random.choice(len(stratum), size=num, replace=False)

            sampled_edges.extend([stratum[i] for i in indices])

    

    # 构建邻接矩阵

    sampled_adj = np.zeros((N, N))

    for i, j in sampled_edges:

        sampled_adj[i, j] = adj[i, j]

        sampled_adj[j, i] = adj[j, i]

    

    return sampled_edges, sampled_adj





# ============================

# 路径/子图采样

# ============================



def random_walk_sampling(adj, start_node, walk_length):

    """

    随机游走采样：从起始节点开始随机游走

    

    参数:

        adj: 邻接矩阵

        start_node: 起始节点

        walk_length: 游走步数

    返回:

        walk: 游走路径节点列表

    """

    N = adj.shape[0]

    adj_list = build_adj_list(adj)

    

    walk = [start_node]

    current = start_node

    

    for _ in range(walk_length):

        neighbors = adj_list[current]

        if len(neighbors) == 0:

            break

        current = random.choice(neighbors)

        walk.append(current)

    

    return walk





def subgraph_sampling(adj, num_seed_nodes, expansion=3, num_walks=5):

    """

    子图采样：从种子节点出发，通过随机游走扩展

    

    参数:

        adj: 邻接矩阵

        num_seed_nodes: 种子节点数

        expansion: 每个种子节点的扩展邻居层数

        num_walks: 每个节点的游走次数

    返回:

        sampled_nodes: 采样的节点集合

        subgraph_adj: 子图邻接矩阵

    """

    N = adj.shape[0]

    adj_list = build_adj_list(adj)

    

    # 采样种子节点

    seed_nodes = np.random.choice(N, size=num_seed_nodes, replace=False)

    

    # 收集采样的节点

    sampled_nodes = set(seed_nodes)

    

    for seed in seed_nodes:

        for _ in range(num_walks):

            walk = random_walk_sampling(adj, seed, expansion)

            sampled_nodes.update(walk)

    

    sampled_nodes = list(sampled_nodes)

    

    # 构建子图

    subgraph_adj = adj[np.ix_(sampled_nodes, sampled_nodes)]

    

    return sampled_nodes, subgraph_adj





# ============================

# GraphSAINT采样器

# ============================



class GraphSAINTSampler:

    """

    GraphSAINT采样器

    

    支持多种采样策略：

    - node_sampling: 节点采样

    - edge_sampling: 边采样

    - stratified_sampling: 分层边采样

    - subgraph_sampling: 子图采样

    """

    

    def __init__(self, adj, sampling_method='node', num_samples=1000):

        self.adj = adj

        self.N = adj.shape[0]

        self.sampling_method = sampling_method

        self.num_samples = num_samples

        

        self.adj_list = build_adj_list(adj)

        

        # 预计算采样概率（用于归一化）

        self._compute_sampling_probs()

    

    def _compute_sampling_probs(self):

        """预计算采样概率"""

        degrees = np.array([len(self.adj_list[i]) for i in range(self.N)])

        

        if self.sampling_method == 'node':

            # 节点采样：基于度

            self.node_probs = degrees / (degrees.sum() + 1e-8)

        elif self.sampling_method == 'edge':

            # 边采样：基于两端点的度

            self.edge_probs = None  # 动态计算

        elif self.sampling_method == 'subgraph':

            # 子图采样：均匀

            self.node_probs = np.ones(self.N) / self.N

    

    def sample(self):

        """

        执行一次采样

        

        返回:

            sampled_nodes: 采样的节点列表

            subgraph_adj: 子图邻接矩阵

        """

        if self.sampling_method == 'node':

            return node_sampling(self.adj, self.num_samples, self.node_probs)

        elif self.sampling_method == 'edge':

            return edge_sampling(self.adj, self.num_samples, method='degree_biased')

        elif self.sampling_method == 'subgraph':

            return subgraph_sampling(self.adj, num_seed_nodes=50, expansion=2, num_walks=3)

        elif self.sampling_method == 'stratified':

            return stratified_edge_sampling(self.adj, self.num_samples)

        else:

            return node_sampling(self.adj, self.num_samples)

    

    def get_subgraph(self, sampled_nodes):

        """获取子图邻接矩阵"""

        return self.adj[np.ix_(sampled_nodes, sampled_nodes)]





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    random.seed(42)

    

    print("=" * 55)

    print("图采样算法测试")

    print("=" * 55)

    

    # 创建测试图

    N = 20

    adj = np.zeros((N, N))

    

    # 创建一个小世界网络

    for i in range(N):

        for j in range(i + 1, min(i + 4, N)):

            adj[i, j] = adj[j, i] = 1

        # 添加一些随机边

        if np.random.random() < 0.2:

            k = np.random.randint(0, N)

            if k != i:

                adj[i, k] = adj[k, i] = 1

    

    # 确保连通

    for i in range(1, N):

        adj[i-1, i] = adj[i, i-1] = 1

    

    print(f"节点数: {N}")

    print(f"边数: {int(np.sum(adj) / 2)}")

    

    # 测试1：节点采样

    print("\n--- 节点采样测试 ---")

    sampled_nodes, subgraph_adj = node_sampling(adj, num_samples=10)

    

    print(f"采样节点数: {len(sampled_nodes)}")

    print(f"子图形状: {subgraph_adj.shape}")

    print(f"子图边数: {int(np.sum(subgraph_adj) / 2)}")

    

    # 测试2：边采样

    print("\n--- 边采样测试 ---")

    sampled_edges, sampled_adj = edge_sampling(adj, num_samples=15)

    

    print(f"采样边数: {len(sampled_edges)}")

    print(f"子图边数: {int(np.sum(sampled_adj) / 2)}")

    

    # 测试3：分层边采样

    print("\n--- 分层边采样测试 ---")

    edges_strat, adj_strat = stratified_edge_sampling(adj, num_samples=20)

    

    print(f"采样边数: {len(edges_strat)}")

    

    # 测试4：随机游走

    print("\n--- 随机游走采样 ---")

    walk = random_walk_sampling(adj, start_node=0, walk_length=10)

    

    print(f"游走路径: {walk}")

    print(f"游走长度: {len(walk)}")

    

    # 测试5：子图采样

    print("\n--- 子图采样测试 ---")

    nodes_sub, adj_sub = subgraph_sampling(adj, num_seed_nodes=3, expansion=3, num_walks=5)

    

    print(f"采样节点数: {len(nodes_sub)}")

    print(f"子图形状: {adj_sub.shape}")

    print(f"子图边数: {int(np.sum(adj_sub) / 2)}")

    

    # 测试6：GraphSAINT采样器

    print("\n--- GraphSAINT采样器测试 ---")

    for method in ['node', 'edge', 'subgraph', 'stratified']:

        sampler = GraphSAINTSampler(adj, sampling_method=method, num_samples=15)

        result = sampler.sample()

        

        if method in ['node', 'subgraph']:

            nodes, sub_adj = result

            print(f"  {method:10s}: 节点数={len(nodes)}, 边数={int(np.sum(sub_adj)/2)}")

        else:

            edges, sub_adj = result

            print(f"  {method:10s}: 边数={len(edges)}, 边密度={np.sum(sub_adj)/(2*N):.3f}")

    

    # 测试7：采样对图统计量的影响

    print("\n--- 采样对图统计量的影响 ---")

    original_density = np.sum(adj > 0) / (N * N)

    original_avg_deg = np.mean(np.sum(adj > 0, axis=1))

    

    print(f"原始图: 密度={original_density:.4f}, 平均度={original_avg_deg:.2f}")

    

    # 多次采样取平均

    densities = []

    avg_degs = []

    

    for _ in range(10):

        nodes, sub_adj = node_sampling(adj, num_samples=N // 2)

        densities.append(np.sum(sub_adj > 0) / (len(nodes) ** 2))

        avg_degs.append(np.mean(np.sum(sub_adj > 0, axis=1)))

    

    print(f"采样图(50%): 密度={np.mean(densities):.4f}, 平均度={np.mean(avg_degs):.2f}")

    

    # 测试8：基于度的采样

    print("\n--- 基于度的节点采样 ---")

    degree_nodes, degree_sub = degree_based_node_sampling(adj, num_samples=10)

    

    print(f"度采样节点: {sorted(degree_nodes)}")

    print(f"采样节点平均度: {np.mean([len(sampler.adj_list[n]) for n in degree_nodes]):.2f}")

    

    print("\n图采样算法测试完成！")

