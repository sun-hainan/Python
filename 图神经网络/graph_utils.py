# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / graph_utils

本文件实现 graph_utils 相关的算法功能。
"""

import numpy as np


def normalize_node_features(features, method='standard'):
    """
    节点特征标准化
    
    参数:
        features: 节点特征矩阵 (N, d)
        method: 'standard' (Z-score) 或 'minmax'
    返回:
        normalized_features: 标准化后的特征
    """
    if method == 'standard':
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0)
        std = np.where(std == 0, 1.0, std)
        return (features - mean) / std
    
    elif method == 'minmax':
        min_val = np.min(features, axis=0)
        max_val = np.max(features, axis=0)
        range_val = max_val - min_val
        range_val = np.where(range_val == 0, 1.0, range_val)
        return (features - min_val) / range_val
    
    return features


def normalize_adjacency(adj, method='sym'):
    """
    邻接矩阵规范化
    
    参数:
        adj: 邻接矩阵 (N, N)
        method: 'sym' (对称归一化) 或 'rw' (随机游走归一化)
    返回:
        规范化后的邻接矩阵
    """
    # 添加自环
    adj = adj + np.eye(adj.shape[0])
    
    # 度矩阵
    degrees = np.sum(adj, axis=1)
    
    if method == 'sym':
        # 对称归一化: D^(-1/2) * A * D^(-1/2)
        d_inv_sqrt = np.power(degrees, -0.5)
        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
        d_mat_inv_sqrt = np.diag(d_inv_sqrt)
        return d_mat_inv_sqrt @ adj @ d_mat_inv_sqrt
    
    elif method == 'rw':
        # 随机游走归一化: D^(-1) * A
        d_inv = 1.0 / (degrees + 1e-8)
        d_mat_inv = np.diag(d_inv)
        return d_mat_inv @ adj
    
    return adj


def add_self_loops(adj):
    """为邻接矩阵添加自环"""
    n = adj.shape[0]
    return adj + np.eye(n)


def remove_self_loops(adj):
    """移除自环"""
    adj = adj.copy()
    np.fill_diagonal(adj, 0)
    return adj


def to_sparse(adj):
    """将邻接矩阵转为稀疏表示"""
    n = adj.shape[0]
    rows, cols = np.where(adj > 0)
    values = adj[rows, cols]
    
    return {
        'indices': np.stack([rows, cols]),
        'values': values,
        'shape': adj.shape
    }


def from_sparse(sparse_dict):
    """从稀疏表示恢复邻接矩阵"""
    indices = sparse_dict['indices']
    values = sparse_dict['values']
    shape = sparse_dict['shape']
    
    adj = np.zeros(shape)
    adj[indices[0], indices[1]] = values
    
    return adj


def create_random_graph(n, p=0.3, directed=False):
    """
    创建Erdős-Rényi随机图
    
    参数:
        n: 节点数
        p: 连边概率
        directed: 是否为有向图
    返回:
        adj: 邻接矩阵
    """
    adj = np.random.binomial(1, p, (n, n)).astype(float)
    
    if not directed:
        adj = (adj + adj.T) / 2
        np.fill_diagonal(adj, 0)
    
    return adj


def create_barabasi_albert_graph(n, m=2, seed=None):
    """
    创建Barabási-Albert优先attachment图
    
    参数:
        n: 总节点数
        m: 每个新节点连接的边数
        seed: 随机种子
    返回:
        adj: 邻接矩阵
    """
    if seed is not None:
        np.random.seed(seed)
    
    adj = np.zeros((n, n))
    
    # 初始完全图
    for i in range(m + 1):
        for j in range(i + 1, m + 1):
            adj[i, j] = adj[j, i] = 1
    
    # 优先attachment
    degrees = np.sum(adj, axis=1)
    
    for new_node in range(m + 1, n):
        # 按度加权概率选择目标节点
        probs = degrees / (np.sum(degrees) + 1e-8)
        
        targets = np.random.choice(new_node, size=m, replace=False, p=probs[:new_node])
        
        for t in targets:
            adj[new_node, t] = adj[t, new_node] = 1
            degrees[t] += 1
        degrees[new_node] = m
    
    return adj


def create_watts_strogatz_graph(n, k=4, p=0.1, seed=None):
    """
    创建Watts-Strogatz小世界图
    
    参数:
        n: 节点数
        k: 每个节点的初始邻居数（偶数）
        p: 重连概率
        seed: 随机种子
    """
    if seed is not None:
        np.random.seed(seed)
    
    adj = np.zeros((n, n))
    
    # 初始环状最近邻耦合
    for i in range(n):
        for j in range(1, k // 2 + 1):
            adj[i, (i + j) % n] = adj[(i + j) % n, i] = 1
    
    # 随机重连
    for i in range(n):
        for j in range(1, k // 2 + 1):
            if np.random.random() < p:
                # 断开(i, (i+j)%n)边
                target = (i + j) % n
                adj[i, target] = adj[target, i] = 0
                
                # 重新连接到随机节点
                new_target = np.random.randint(0, n)
                while new_target == i or adj[i, new_target] > 0:
                    new_target = np.random.randint(0, n)
                
                adj[i, new_target] = adj[new_target, i] = 1
    
    return adj


def compute_graph_laplacian(adj):
    """计算拉普拉斯矩阵"""
    degrees = np.sum(adj, axis=1)
    D = np.diag(degrees)
    L = D - adj
    return L


def compute_normalized_laplacian(adj):
    """计算对称归一化拉普拉斯矩阵"""
    adj = add_self_loops(adj)
    degrees = np.sum(adj, axis=1)
    d_inv_sqrt = np.power(degrees, -0.5)
    d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
    d_mat = np.diag(d_inv_sqrt)
    L = np.eye(adj.shape[0]) - d_mat @ adj @ d_mat
    return L


def compute_spectral_gap(adj):
    """计算谱隙（第二小特征值）"""
    L = compute_normalized_laplacian(adj)
    eigenvalues = np.linalg.eigvalsh(L)
    eigenvalues = np.sort(eigenvalues)
    return eigenvalues[1] - eigenvalues[0]


def is_connected(adj):
    """检查图是否连通"""
    n = adj.shape[0]
    visited = set([0])
    queue = [0]
    
    while queue:
        node = queue.pop(0)
        neighbors = np.where(adj[node] > 0)[0]
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return len(visited) == n


def get_largest_connected_component(adj):
    """获取最大连通分量"""
    n = adj.shape[0]
    visited = set()
    components = []
    
    for start in range(n):
        if start in visited:
            continue
        
        component = set([start])
        queue = [start]
        
        while queue:
            node = queue.pop(0)
            neighbors = np.where(adj[node] > 0)[0]
            for neighbor in neighbors:
                if neighbor not in component:
                    component.add(neighbor)
                    queue.append(neighbor)
        
        components.append(component)
        visited.update(component)
    
    # 找最大分量
    largest = max(components, key=len)
    largest_list = sorted(largest)
    
    return largest_list, np.ix_(largest_list, largest_list)


def augment_by_dropout(adj, node_features, dropout_rate=0.1):
    """
    使用Dropout增强图数据
    
    参数:
        adj: 邻接矩阵
        node_features: 节点特征
        dropout_rate: 节点dropout率
    返回:
        augmented_adj, augmented_features
    """
    n = adj.shape[0]
    
    # Dropout节点
    keep_mask = np.random.rand(n) > dropout_rate
    keep_indices = np.where(keep_mask)[0]
    
    # 子图
    aug_adj = adj[np.ix_(keep_indices, keep_indices)]
    aug_features = node_features[keep_indices]
    
    return aug_adj, aug_features


def augment_by_edge_dropout(adj, dropout_rate=0.1):
    """
    边Dropout增强
    
    参数:
        adj: 邻接矩阵
        dropout_rate: 边dropout率
    返回:
        augmented_adj
    """
    aug_adj = adj.copy()
    
    # 随机丢弃边
    mask = np.random.rand(*adj.shape) > dropout_rate
    aug_adj = aug_adj * mask
    
    # 保持对称性
    aug_adj = (aug_adj + aug_adj.T) / 2
    
    return aug_adj


class GraphStatistics:
    """图统计计算器"""
    
    def __init__(self, adj, node_features=None):
        self.adj = adj
        self.node_features = node_features
        self.n = adj.shape[0]
    
    def num_nodes(self):
        return self.n
    
    def num_edges(self):
        return int(np.sum(self.adj) / 2)
    
    def average_degree(self):
        return np.mean(np.sum(self.adj, axis=1))
    
    def degree_distribution(self):
        return np.sum(self.adj, axis=1)
    
    def density(self):
        max_edges = self.n * (self.n - 1) / 2
        return self.num_edges() / max_edges if max_edges > 0 else 0
    
    def clustering_coefficient(self):
        coeffs = []
        for i in range(self.n):
            neighbors = np.where(self.adj[i] > 0)[0]
            k = len(neighbors)
            if k < 2:
                coeffs.append(0.0)
                continue
            
            edges_between = 0
            for ni in neighbors:
                for nj in neighbors:
                    if ni < nj and self.adj[ni, nj] > 0:
                        edges_between += 1
            
            max_edges = k * (k - 1) / 2
            coeffs.append(edges_between / max_edges if max_edges > 0 else 0)
        
        return np.mean(coeffs)
    
    def spectral_radius(self):
        eigenvalues = np.linalg.eigvalsh(self.adj)
        return np.max(np.abs(eigenvalues))
    
    def summary(self):
        return {
            'num_nodes': self.num_nodes(),
            'num_edges': self.num_edges(),
            'avg_degree': self.average_degree(),
            'density': self.density(),
            'clustering_coef': self.clustering_coefficient(),
            'spectral_radius': self.spectral_radius()
        }


if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("图神经网络实用工具测试")
    print("=" * 55)
    
    # 创建测试图
    n = 20
    adj = create_random_graph(n, p=0.2)
    features = np.random.randn(n, 8)
    
    print(f"\n测试图: {n}节点")
    print(f"边数: {int(np.sum(adj) / 2)}")
    
    # 特征标准化
    print("\n--- 特征标准化 ---")
    feat_std = normalize_node_features(features, 'standard')
    feat_minmax = normalize_node_features(features, 'minmax')
    
    print(f"原始均值: {features.mean():.4f}, 标准差: {features.std():.4f}")
    print(f"Standardized均值: {feat_std.mean():.4f}, 标准差: {feat_std.std():.4f}")
    print(f"MinMax范围: [{feat_minmax.min():.4f}, {feat_minmax.max():.4f}]")
    
    # 邻接矩阵规范化
    print("\n--- 邻接矩阵规范化 ---")
    adj_sym = normalize_adjacency(adj, 'sym')
    adj_rw = normalize_adjacency(adj, 'rw')
    
    print(f"对称归一化后行和: {np.sum(adj_sym, axis=1)[:5].round(3)}")
    print(f"RW归一化后行和: {np.sum(adj_rw, axis=1)[:5].round(3)}")
    
    # 图生成算法
    print("\n--- 不同图模型 ---")
    
    # Erdős-Rényi
    er_graph = create_random_graph(20, p=0.3)
    print(f"Erdős-Rényi: {int(np.sum(er_graph)/2)}边, 连通={is_connected(er_graph)}")
    
    # Barabási-Albert
    ba_graph = create_barabasi_albert_graph(20, m=2)
    print(f"Barabási-Albert: {int(np.sum(ba_graph)/2)}边, 连通={is_connected(ba_graph)}")
    
    # Watts-Strogatz
    ws_graph = create_watts_strogatz_graph(20, k=4, p=0.1)
    print(f"Watts-Strogatz: {int(np.sum(ws_graph)/2)}边, 连通={is_connected(ws_graph)}")
    
    # 图统计
    print("\n--- 图统计 ---")
    stats = GraphStatistics(adj)
    summary = stats.summary()
    
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 数据增强
    print("\n--- 数据增强 ---")
    aug_adj, aug_feat = augment_by_dropout(adj, features, dropout_rate=0.2)
    print(f"节点Dropout: {adj.shape[0]} -> {aug_adj.shape[0]}节点")
    
    aug_adj2 = augment_by_edge_dropout(adj, dropout_rate=0.2)
    print(f"边Dropout: {int(np.sum(adj)/2)} -> {int(np.sum(aug_adj2)/2)}边")
    
    # 拉普拉斯矩阵
    print("\n--- 拉普拉斯矩阵 ---")
    L = compute_graph_laplacian(adj)
    L_norm = compute_normalized_laplacian(adj)
    
    print(f"普通拉普拉斯特征值: {np.linalg.eigvalsh(L)[:3].round(3)}")
    print(f"归一化拉普拉斯特征值: {np.linalg.eigvalsh(L_norm)[:3].round(3)}")
    
    # 连通分量
    print("\n--- 连通分量检测 ---")
    largest_nodes, largest_adj = get_largest_connected_component(adj)
    print(f"最大连通分量节点数: {len(largest_nodes)}")
    print(f"子图大小: {largest_adj.shape}")
    
    # 谱隙
    print("\n--- 谱隙分析 ---")
    for p in [0.1, 0.2, 0.3, 0.5]:
        g = create_random_graph(30, p=p)
        gap = compute_spectral_gap(g)
        conn = is_connected(g)
        print(f"  p={p}: 谱隙={gap:.4f}, 连通={conn}")
    
    print("\n图神经网络实用工具测试完成！")
