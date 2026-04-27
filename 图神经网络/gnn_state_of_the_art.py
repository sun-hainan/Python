# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / gnn_state_of_the_art

本文件实现 gnn_state_of_the_art 相关的算法功能。
"""

import numpy as np


# ============================
# 身份识别GNN（ID-GNN）
# ============================

class IdentityGNNLayer:
    """
    身份识别图神经网络
    
    核心思想：在消息传递中保留节点身份信息
    
    参数:
        node_dim: 节点特征维度
        hidden_dim: 隐藏层维度
    """
    
    def __init__(self, node_dim, hidden_dim):
        self.node_dim = node_dim
        self.hidden_dim = hidden_dim
        
        # 节点变换
        self.W_node = np.random.randn(node_dim + hidden_dim, hidden_dim) * np.sqrt(2.0 / (node_dim + hidden_dim))
        
        # 环路检测（检测节点到自身的路径）
        self.W_cycle = np.random.randn(1, hidden_dim) * 0.01
    
    def detect_self_loops(self, adj):
        """
        检测自环：计算每个节点到自身的路径数
        
        返回:
            cycle_counts: 每个节点的自环计数
        """
        n = adj.shape[0]
        
        # A^2 对角线元素表示经过两步回到自身的路径数
        A2 = adj @ adj
        cycle_counts = np.diag(A2)
        
        # 也可以考虑更长路径
        A3 = A2 @ adj
        cycle_counts += np.diag(A3) * 0.5
        
        return cycle_counts
    
    def forward(self, node_features, adj):
        """前馈"""
        n = node_features.shape[0]
        
        # 检测自环
        cycle_counts = self.detect_self_loops(adj)
        
        # 邻居聚合
        neighbor_agg = adj @ node_features
        neighbor_count = np.sum(adj, axis=1, keepdims=True) + 1e-8
        neighbor_agg = neighbor_agg / neighbor_count
        
        # 添加身份信息
        identity = np.eye(n)  # 节点身份编码
        
        # 组合：原始特征 + 邻居聚合 + 身份 + 环路
        combined = np.concatenate([
            node_features,
            neighbor_agg,
            0.1 * identity,
            self.W_cycle.flatten()[0] * cycle_counts.reshape(-1, 1)
        ], axis=1)
        
        # 变换
        output = np.maximum(0, combined @ self.W_node)
        
        return output


# ============================
# 持续同调GNN（PH-GNN）
# ============================

class PersistentHomologyGNN:
    """
    持续同调图神经网络
    
    使用持续同调来捕获图的拓扑特征
    
    参数:
        node_dim: 节点特征维度
        hidden_dim: 隐藏层维度
    """
    
    def __init__(self, node_dim, hidden_dim):
        self.node_dim = node_dim
        self.hidden_dim = hidden_dim
        
        self.W = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)
    
    def compute_filtration(self, adj, node_features):
        """
        计算过滤函数（使用度作为简单过滤）
        
        返回:
            filtration_order: 节点按照过滤值排序
            filtration_values: 每个节点的过滤值
        """
        degrees = np.sum(adj, axis=1)
        filtration_values = degrees + np.linalg.norm(node_features, axis=1) * 0.1
        filtration_order = np.argsort(filtration_values)
        
        return filtration_order, filtration_values
    
    def compute_simplex_tree(self, adj, max_dim=2):
        """
        简化单纯形树计算
        
        参数:
            adj: 邻接矩阵
            max_dim: 最大单纯形维度
        返回:
            simplex_counts: 各维度单纯形数量
        """
        n = adj.shape[0]
        
        # 0-单纯形（顶点）
        simplices = {0: n}
        
        # 1-单纯形（边）
        edges = np.sum(adj > 0) / 2
        simplices[1] = int(edges)
        
        # 2-单纯形（三角形）
        triangles = 0
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    if adj[i, j] > 0 and adj[j, k] > 0 and adj[i, k] > 0:
                        triangles += 1
        simplices[2] = triangles
        
        return simplices
    
    def compute_betti_numbers(self, simplices):
        """
        计算Betti数
        
        Betti-0: 连通分量数
        Betti-1: 环路数
        Betti-2: 空洞数
        """
        n = simplices.get(0, 0)
        e = simplices.get(1, 0)
        f = simplices.get(2, 0)
        
        # 简化的Betti数计算
        # 实际需要使用同调群计算
        betti_0 = 1  # 假设连通
        betti_1 = e - n + betti_0  # 欧拉公式
        betti_2 = max(0, f - e + n - betti_0)  # 简化估计
        
        return {
            'betti_0': betti_0,
            'betti_1': max(0, betti_1),
            'betti_2': betti_2
        }
    
    def forward(self, node_features, adj):
        """前馈"""
        # 基础图卷积
        h = node_features @ self.W
        h = np.maximum(0, h)
        
        # 计算拓扑特征
        filtration_order, filtration_values = self.compute_filtration(adj, node_features)
        simplices = self.compute_simplex_tree(adj)
        betti = self.compute_betti_numbers(simplices)
        
        # 将拓扑特征融入节点表示
        topo_feature = np.array([
            betti['betti_0'],
            betti['betti_1'],
            betti['betti_2']
        ])
        
        # 每个节点加上全局拓扑特征的影响
        for i in range(node_features.shape[0]):
            h[i] = h[i] + 0.1 * topo_feature * (1 / (filtration_values[i] + 1))
        
        return h


# ============================
# 位置编码GNN（PE-GNN）
# ============================

class PositionalEncodingGNN:
    """
    位置编码图神经网络
    
    结合结构化位置编码增强GNN的表达能力
    
    参数:
        node_dim: 节点特征维度
        hidden_dim: 隐藏层维度
        pe_dim: 位置编码维度
    """
    
    def __init__(self, node_dim, hidden_dim, pe_dim=16):
        self.node_dim = node_dim
        self.hidden_dim = hidden_dim
        self.pe_dim = pe_dim
        
        # 特征投影
        self.W_feat = np.random.randn(node_dim + pe_dim, hidden_dim) * np.sqrt(2.0 / (node_dim + pe_dim))
        
        # 位置编码
        self.pe_type = 'laplacian'
    
    def compute_laplacian_pe(self, adj, k=16):
        """
        拉普拉斯位置编码
        
        使用拉普拉斯特征向量作为位置编码
        """
        n = adj.shape[0]
        
        # 归一化拉普拉斯
        adj = adj + np.eye(n)
        d = np.sum(adj, axis=1)
        d_inv_sqrt = np.power(d, -0.5)
        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
        L = np.eye(n) - np.diag(d_inv_sqrt) @ adj @ np.diag(d_inv_sqrt)
        
        # 特征分解
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        
        # 取最小的k个特征向量
        pe = eigenvectors[:, 1:k+1]
        
        # 填充
        if pe.shape[1] < self.pe_dim:
            pe = np.concatenate([pe, np.zeros((n, self.pe_dim - pe.shape[1]))], axis=1)
        
        return pe[:, :self.pe_dim]
    
    def compute_rw_pe(self, adj, walk_length=20, num_walks=10):
        """
        随机游走位置编码
        
        统计从每个节点出发的随机游走访问分布
        """
        n = adj.shape[0]
        adj_list = {i: np.where(adj[i] > 0)[0] for i in range(n)}
        
        rwpe = np.zeros((n, self.pe_dim))
        
        for start in range(n):
            visits = np.zeros(n)
            
            for _ in range(num_walks):
                current = start
                for step in range(walk_length):
                    visits[current] += 1
                    neighbors = adj_list.get(current, np.array([current]))
                    current = np.random.choice(neighbors)
            
            rwpe[start] = visits / (num_walks * walk_length)
        
        return rwpe
    
    def compute_svd_pe(self, adj, k=16):
        """
        SVD位置编码
        
        使用邻接矩阵的SVD分解
        """
        # SVD分解
        U, S, Vt = np.linalg.svd(adj)
        
        # 取前k个奇异向量
        pe = U[:, :k]
        
        n = adj.shape[0]
        if pe.shape[1] < self.pe_dim:
            pe = np.concatenate([pe, np.zeros((n, self.pe_dim - pe.shape[1]))], axis=1)
        
        return pe[:, :self.pe_dim]
    
    def get_positional_encoding(self, adj):
        """获取位置编码"""
        if self.pe_type == 'laplacian':
            return self.compute_laplacian_pe(adj, self.pe_dim)
        elif self.pe_type == 'random_walk':
            return self.compute_rw_pe(adj)
        elif self.pe_type == 'svd':
            return self.compute_svd_pe(adj, self.pe_dim)
        else:
            return np.zeros((adj.shape[0], self.pe_dim))
    
    def forward(self, node_features, adj):
        """前馈"""
        # 获取位置编码
        pe = self.get_positional_encoding(adj)
        
        # 拼接节点特征和位置编码
        combined = np.concatenate([node_features, pe], axis=1)
        
        # 投影
        output = np.maximum(0, combined @ self.W_feat)
        
        return output


# ============================
# 子图感知GNN
# ============================

class SubgraphAwareGNN:
    """
    子图感知图神经网络
    
    通过局部子图结构增强节点表示
    
    参数:
        node_dim: 节点特征维度
        hidden_dim: 隐藏层维度
        subgraph_radius: 子图半径
    """
    
    def __init__(self, node_dim, hidden_dim, subgraph_radius=2):
        self.node_dim = node_dim
        self.hidden_dim = hidden_dim
        self.subgraph_radius = subgraph_radius
        
        self.W_node = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)
        self.W_subgraph = np.random.randn(hidden_dim * 3, hidden_dim) * 0.01
    
    def extract_subgraph(self, adj, center_node, radius):
        """
        提取以某节点为中心的子图
        
        返回:
            subgraph_nodes: 子图节点列表
            subgraph_adj: 子图邻接矩阵
            distances: 各节点到中心节点的距离
        """
        n = adj.shape[0]
        
        # BFS获取radius内的节点
        visited = {center_node: 0}
        queue = [(center_node, 0)]
        
        while queue:
            node, dist = queue.pop(0)
            if dist >= radius:
                continue
            
            neighbors = np.where(adj[node] > 0)[0]
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))
        
        subgraph_nodes = sorted(visited.keys())
        node_to_idx = {node: i for i, node in enumerate(subgraph_nodes)}
        
        # 构建子图邻接矩阵
        subgraph_adj = np.zeros((len(subgraph_nodes), len(subgraph_nodes)))
        for i, node_i in enumerate(subgraph_nodes):
            for j, node_j in enumerate(subgraph_nodes):
                if adj[node_i, node_j] > 0:
                    subgraph_adj[i, j] = 1
        
        # 距离
        distances = np.array([visited.get(node, radius) for node in subgraph_nodes])
        
        return subgraph_nodes, subgraph_adj, distances
    
    def compute_subgraph_stats(self, subgraph_adj):
        """
        计算子图统计量
        """
        n = subgraph_adj.shape[0]
        
        # 子图大小
        size = n
        
        # 子图边数
        edges = np.sum(subgraph_adj) / 2
        
        # 子图密度
        max_edges = n * (n - 1) / 2
        density = edges / max_edges if max_edges > 0 else 0
        
        # 子图度统计
        degrees = np.sum(subgraph_adj, axis=1)
        degree_mean = np.mean(degrees)
        degree_std = np.std(degrees)
        
        return np.array([size, edges, density, degree_mean, degree_std])
    
    def forward(self, node_features, adj):
        """前馈"""
        n = node_features.shape[0]
        
        # 节点变换
        h = node_features @ self.W_node
        h = np.maximum(0, h)
        
        # 收集子图信息
        subgraph_features = np.zeros((n, 5))
        
        for node in range(n):
            _, sub_adj, distances = self.extract_subgraph(adj, node, self.subgraph_radius)
            stats = self.compute_subgraph_stats(sub_adj)
            
            # 距离加权
            distance_weight = 1.0 / (distances + 1)
            
            subgraph_features[node] = stats * np.mean(distance_weight)
        
        # 组合节点特征和子图特征
        combined = np.concatenate([h, subgraph_features], axis=1)
        output = np.maximum(0, combined @ self.W_subgraph)
        
        return output


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 60)
    print("图神经网络最新研究进展测试")
    print("=" * 60)
    
    # 创建测试图
    N = 15
    adj = np.zeros((N, N))
    
    for i in range(N):
        for j in range(i + 1, N):
            if np.random.random() < 0.25:
                adj[i, j] = adj[j, i] = 1
    
    # 确保连通
    for i in range(1, N):
        if np.sum(adj[i]) == 0:
            adj[i, i-1] = adj[i-1, i] = 1
    
    node_features = np.random.randn(N, 8)
    
    print(f"\n测试图: {N}节点, {int(np.sum(adj)/2)}边")
    
    # 测试ID-GNN
    print("\n--- 身份识别GNN (ID-GNN) ---")
    id_gnn = IdentityGNNLayer(node_dim=8, hidden_dim=16)
    out_id = id_gnn.forward(node_features, adj)
    
    print(f"输出形状: {out_id.shape}")
    print(f"输出范围: [{out_id.min():.4f}, {out_id.max():.4f}]")
    
    # 检测自环
    cycle_counts = id_gnn.detect_self_loops(adj)
    print(f"自环检测: {cycle_counts[:5]}")
    
    # 测试PH-GNN
    print("\n--- 持续同调GNN (PH-GNN) ---")
    ph_gnn = PersistentHomologyGNN(node_dim=8, hidden_dim=16)
    out_ph = ph_gnn.forward(node_features, adj)
    
    simplices = ph_gnn.compute_simplex_tree(adj)
    betti = ph_gnn.compute_betti_numbers(simplices)
    
    print(f"单纯形: {simplices}")
    print(f"Betti数: {betti}")
    print(f"输出形状: {out_ph.shape}")
    
    # 测试PE-GNN
    print("\n--- 位置编码GNN (PE-GNN) ---")
    pe_gnn = PositionalEncodingGNN(node_dim=8, hidden_dim=16, pe_dim=8)
    
    for pe_type in ['laplacian', 'random_walk', 'svd']:
        pe_gnn.pe_type = pe_type
        pe = pe_gnn.get_positional_encoding(adj)
        out_pe = pe_gnn.forward(node_features, adj)
        print(f"  {pe_type:12s}: PE范围=[{pe.min():.3f}, {pe.max():.3f}], 输出范围=[{out_pe.min():.3f}, {out_pe.max():.3f}]")
    
    # 测试子图感知GNN
    print("\n--- 子图感知GNN ---")
    subgraph_gnn = SubgraphAwareGNN(node_dim=8, hidden_dim=16, subgraph_radius=2)
    out_subgraph = subgraph_gnn.forward(node_features, adj)
    
    print(f"输出形状: {out_subgraph.shape}")
    
    # 提取子图示例
    nodes, sub_adj, dists = subgraph_gnn.extract_subgraph(adj, center_node=0, radius=2)
    print(f"节点0的2-半径子图: {len(nodes)}节点, {int(np.sum(sub_adj)/2)}边")
    print(f"到中心距离: {dists}")
    
    # 综合对比
    print("\n" + "-" * 60)
    print("各新架构输出对比")
    print("-" * 60)
    
    results = {
        'ID-GNN': out_id,
        'PH-GNN': out_ph,
        'PE-GNN (Laplacian)': pe_gnn.compute_laplacian_pe(adj) @ np.eye(8, 16),
        'Subgraph-GNN': out_subgraph,
    }
    
    print(f"{'架构':>20} | {'均值':>10} | {'标准差':>10} | {'非零比例':>12}")
    print("-" * 60)
    
    for name, out in results.items():
        out_mean = np.mean(out)
        out_std = np.std(out)
        nonzero_ratio = np.mean(out != 0)
        print(f"{name:>20} | {out_mean:10.4f} | {out_std:10.4f} | {nonzero_ratio:12.2%}")
    
    # 表达能力分析
    print("\n--- 表达能力分析 ---")
    print("ID-GNN: 区分同构节点")
    print("PH-GNN: 捕获拓扑模式（环、洞）")
    print("PE-GNN: 位置感知，不依赖节点顺序")
    print("Subgraph-GNN: 局部结构感知")
    
    print("\n图神经网络最新研究进展测试完成！")
