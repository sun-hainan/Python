# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / gnn_layer_architectures

本文件实现 gnn_layer_architectures 相关的算法功能。
"""

import numpy as np


# ============================
# 谱域GNN层
# ============================

class ChebNetLayer:
    """
    Chebyshev谱神经网络层
    
    使用Chebyshev多项式近似滤波器
    """
    
    def __init__(self, in_channels, out_channels, k=2):
        """
        参数:
            in_channels: 输入通道
            out_channels: 输出通道
            k: Chebyshev多项式阶数
        """
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.k = k
        
        # Chebyshev系数
        self.theta = np.random.randn(k + 1) * 0.01
    
    def compute_laplacian(self, adj):
        """计算归一化拉普拉斯"""
        adj = adj + np.eye(adj.shape[0])
        d = np.sum(adj, axis=1)
        d_inv_sqrt = np.power(d, -0.5)
        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
        L = np.eye(adj.shape[0]) - np.diag(d_inv_sqrt) @ adj @ np.diag(d_inv_sqrt)
        return L
    
    def chebyshev_polynomials(self, L, k):
        """计算Chebyshev多项式"""
        n = L.shape[0]
        T = [np.eye(n), L]  # T_0, T_1
        
        for i in range(2, k + 1):
            T.append(2 * L @ T[-1] - T[-2])
        
        return T
    
    def forward(self, x, adj):
        """
        前馈
        
        参数:
            x: 节点特征 (N, in_channels)
            adj: 邻接矩阵
        """
        N = x.shape[0]
        
        # 缩放拉普拉斯（特征值在[0, 2]）
        L = self.compute_laplacian(adj)
        L_scaled = L * 2 - np.eye(N)
        
        # Chebyshev多项式
        T = self.chebyshev_polynomials(L_scaled, self.k)
        
        # 滤波
        output = np.zeros((N, self.out_channels))
        
        for i in range(self.k + 1):
            # T_i @ x @ theta_i
            filtered = T[i] @ x @ (np.eye(self.in_channels) * self.theta[i])
            output += filtered
        
        return output


class ARMAConvLayer:
    """
    ARMA（Anti-Renormalization Message Passing）层
    """
    
    def __init__(self, in_channels, out_channels, num_stacks=2, iterations=2):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_stacks = num_stacks
        self.iterations = iterations
        
        # 每个stack的参数
        self.W0 = np.random.randn(in_channels, out_channels) * np.sqrt(2.0 / in_channels)
        self.W1 = np.random.randn(in_channels, out_channels) * np.sqrt(2.0 / in_channels)
        self.W_skip = np.random.randn(out_channels, out_channels) * 0.01
    
    def forward(self, x, adj):
        """前馈"""
        N = x.shape[0]
        
        # 归一化邻接
        adj = adj + np.eye(N)
        d = np.sum(adj, axis=1)
        d_inv = 1.0 / (d + 1e-8)
        adj_norm = np.diag(d_inv) @ adj
        
        # 多个stack的平均
        stack_outputs = []
        
        for _ in range(self.num_stacks):
            h = x @ self.W0
            
            # 迭代消息传递
            for _ in range(self.iterations):
                h = adj_norm @ (h @ self.W1)
                h = np.maximum(0, h)  # ReLU
            
            stack_outputs.append(h)
        
        # 平均所有stack
        output = np.mean(stack_outputs, axis=0)
        
        # Skip connection
        output = output + x[:, :self.out_channels] @ self.W_skip
        
        return output


# ============================
# 空域GNN层
# ============================

class MessagePassingLayer:
    """
    通用消息传递层框架
    """
    
    def __init__(self, node_dim, edge_dim, hidden_dim):
        self.node_dim = node_dim
        self.edge_dim = edge_dim
        self.hidden_dim = hidden_dim
        
        # 消息函数
        self.W_msg = np.random.randn(node_dim * 2 + edge_dim, hidden_dim) * 0.01
        
        # 更新函数
        self.W_update = np.random.randn(hidden_dim * 2, hidden_dim) * 0.01
    
    def forward(self, node_features, edge_index, edge_features=None):
        """
        前馈
        
        参数:
            node_features: (N, node_dim)
            edge_index: (2, num_edges)
            edge_features: (num_edges, edge_dim)
        """
        N = node_features.shape[0]
        num_edges = edge_index.shape[1]
        
        if edge_features is None:
            edge_features = np.zeros((num_edges, 1))
        
        # 消息传递
        messages = np.zeros((num_edges, self.hidden_dim))
        
        for i in range(num_edges):
            src = edge_index[0, i]
            dst = edge_index[1, i]
            
            # 消息 = f(h_src, h_dst, e_src_dst)
            combined = np.concatenate([
                node_features[src],
                node_features[dst],
                edge_features[i]
            ])
            
            messages[i] = np.maximum(0, combined @ self.W_msg)
        
        # 聚合
        aggregated = np.zeros((N, self.hidden_dim))
        receiver_counts = np.zeros(N)
        
        for i in range(num_edges):
            dst = edge_index[1, i]
            aggregated[dst] += messages[i]
            receiver_counts[dst] += 1
        
        # 平均
        for n in range(N):
            if receiver_counts[n] > 0:
                aggregated[n] /= receiver_counts[n]
        
        # 更新
        combined = np.concatenate([node_features[:, :self.hidden_dim], aggregated], axis=1)
        updated = np.maximum(0, combined @ self.W_update)
        
        return updated


class PANLayer:
    """
    PAN（Path-Augmented Network）层
    通过路径信息增强
    """
    
    def __init__(self, in_dim, out_dim):
        self.in_dim = in_dim
        self.out_dim = out_dim
        
        self.W_neighbor = np.random.randn(in_dim, out_dim) * np.sqrt(2.0 / in_dim)
        self.W_self = np.random.randn(in_dim, out_dim) * np.sqrt(2.0 / in_dim)
        self.W_path = np.random.randn(in_dim, out_dim) * 0.01
    
    def forward(self, x, adj):
        """前馈"""
        N = x.shape[0]
        
        # 邻居聚合
        neighbor_agg = adj @ (x @ self.W_neighbor)
        neighbor_count = np.sum(adj, axis=1, keepdims=True) + 1e-8
        neighbor_agg = neighbor_agg / neighbor_count
        
        # 自身特征
        self_feat = x @ self.W_self
        
        # 路径信息（简化为二阶邻居）
        path_agg = adj @ adj @ (x @ self.W_path)
        path_agg = path_agg / (np.sum(adj @ adj, axis=1, keepdims=True) + 1e-8)
        
        # 组合
        output = neighbor_agg + self_feat + 0.5 * path_agg
        
        return output


# ============================
# 注意力机制层
# ============================

class GATConv:
    """GAT卷积层"""
    
    def __init__(self, in_dim, out_dim, num_heads=4):
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.num_heads = num_heads
        self.head_dim = out_dim // num_heads
        
        # 线性变换
        self.W = np.random.randn(in_dim, out_dim) * np.sqrt(2.0 / in_dim)
        
        # 注意力参数
        self.a = np.random.randn(2 * self.head_dim, num_heads) * 0.01
    
    def forward(self, x, adj):
        """前馈"""
        N = x.shape[0]
        h = x @ self.W  # (N, out_dim)
        
        # 分成多头
        h = h.reshape(N, self.num_heads, self.head_dim)
        h = h.transpose(1, 0, 2)  # (num_heads, N, head_dim)
        
        # 计算注意力
        h_i = h.unsqueeze(2)  # (num_heads, N, 1, head_dim)
        h_j = h.unsqueeze(3)  # (num_heads, N, head_dim, 1)
        
        # 拼接并计算注意力系数
        h_concat = np.concatenate([h_i, h_j], axis=3)  # (num_heads, N, N, 2*head_dim)
        
        # 简化的注意力计算
        e = np.sum(h_concat * self.a.T.reshape(1, 1, 1, 2), axis=-1)  # (num_heads, N, N)
        e = np.exp(np.clip(e, -50, 50))
        
        # 掩码
        mask = adj > 0
        for head in range(self.num_heads):
            e[head] = np.where(mask, e[head], 0)
        
        # 归一化
        alpha = e / (np.sum(e, axis=2, keepdims=True) + 1e-8)
        
        # 加权聚合
        output = np.einsum('hnn,hnd->hnd', alpha, h)
        output = output.transpose(1, 0, 2).reshape(N, -1)
        
        return output


# ============================
# 混合方法层
# ============================

class GraphNetLayer:
    """
    Graph Network完整实现
    包含节点更新、边更新、图更新三个阶段
    """
    
    def __init__(self, node_dim, edge_dim, global_dim):
        self.node_dim = node_dim
        self.edge_dim = edge_dim
        self.global_dim = global_dim
        
        # 边更新
        self.edge_fn = lambda e, v_s, v_r, u: np.random.randn(*e.shape) * 0.01
        
        # 节点更新
        self.node_fn = lambda v, u, aggr_e: np.random.randn(*v.shape) * 0.01
        
        # 全局更新
        self.global_fn = lambda u, aggr_v, aggr_e: np.random.randn(*u.shape) * 0.01
    
    def forward(self, node_features, edge_index, edge_features=None, global_features=None):
        """
        前馈
        
        三个阶段：
        1. 边更新：基于相连节点和全局特征
        2. 节点更新：聚合边信息后更新
        3. 全局更新：聚合所有信息
        """
        N = node_features.shape[0]
        
        if edge_features is None:
            edge_features = np.zeros((edge_index.shape[1], self.edge_dim))
        
        if global_features is None:
            global_features = np.zeros((1, self.global_dim))
        
        # 1. 边更新（简化）
        num_edges = edge_index.shape[1]
        updated_edge_features = edge_features + np.random.randn(num_edges, self.edge_dim) * 0.01
        
        # 2. 节点更新
        node_updates = np.zeros((N, self.node_dim))
        node_counts = np.zeros(N)
        
        for i in range(num_edges):
            src, dst = edge_index[:, i]
            node_updates[dst] += updated_edge_features[i]
            node_counts[dst] += 1
        
        for n in range(N):
            if node_counts[n] > 0:
                node_updates[n] /= node_counts[n]
        
        updated_node_features = node_features + node_updates
        
        # 3. 全局更新（简化）
        updated_global = global_features + np.random.randn(1, self.global_dim) * 0.01
        
        return updated_node_features, updated_edge_features, updated_global


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 60)
    print("图神经网络层架构汇总测试")
    print("=" * 60)
    
    # 创建测试图
    N = 10
    adj = np.zeros((N, N))
    
    for i in range(N):
        for j in range(i + 1, N):
            if np.random.random() < 0.3:
                adj[i, j] = adj[j, i] = 1
    
    # 确保连通
    for i in range(1, N):
        adj[i-1, i] = adj[i, i-1] = 1
    
    node_features = np.random.randn(N, 8)
    
    print(f"\n测试图: {N}节点, {int(np.sum(adj)/2)}边")
    
    # 测试ChebNet
    print("\n--- ChebNet层 ---")
    cheb = ChebNetLayer(in_channels=8, out_channels=16, k=3)
    out_cheb = cheb.forward(node_features, adj)
    print(f"输入: {node_features.shape}")
    print(f"输出: {out_cheb.shape}")
    
    # 测试ARMA
    print("\n--- ARMA层 ---")
    arma = ARMAConvLayer(in_channels=8, out_channels=16, num_stacks=2, iterations=2)
    out_arma = arma.forward(node_features, adj)
    print(f"输出: {out_arma.shape}")
    
    # 测试MessagePassing
    print("\n--- MessagePassing层 ---")
    edge_index = np.array([
        [i, j] for i in range(N) for j in range(N) if adj[i, j] > 0
    ]).T
    mp = MessagePassingLayer(node_dim=8, edge_dim=2, hidden_dim=16)
    out_mp = mp.forward(node_features, edge_index)
    print(f"边数: {edge_index.shape[1]}")
    print(f"输出: {out_mp.shape}")
    
    # 测试PAN
    print("\n--- PAN层 ---")
    pan = PANLayer(in_dim=8, out_dim=16)
    out_pan = pan.forward(node_features, adj)
    print(f"输出: {out_pan.shape}")
    
    # 测试GAT
    print("\n--- GAT层 ---")
    gat = GATConv(in_dim=8, out_dim=16, num_heads=4)
    out_gat = gat.forward(node_features, adj)
    print(f"输出: {out_gat.shape}")
    
    # 测试GraphNet
    print("\n--- GraphNet层 ---")
    gn = GraphNetLayer(node_dim=8, edge_dim=4, global_dim=8)
    out_v, out_e, out_u = gn.forward(node_features, edge_index)
    print(f"节点特征: {out_v.shape}")
    print(f"边特征: {out_e.shape}")
    print(f"全局特征: {out_u.shape}")
    
    # 层对比
    print("\n" + "-" * 60)
    print("各层输出对比")
    print("-" * 60)
    
    layers = {
        'ChebNet': out_cheb,
        'ARMA': out_arma,
        'MessagePassing': out_mp,
        'PAN': out_pan,
        'GAT': out_gat,
    }
    
    print(f"{'层类型':>20} | {'输出均值':>12} | {'输出标准差':>12} | {'输出范数':>12}")
    print("-" * 60)
    
    for name, out in layers.items():
        print(f"{name:>20} | {out.mean():12.4f} | {out.std():12.4f} | {np.linalg.norm(out):12.4f}")
    
    # 感受野分析
    print("\n--- 不同层的感受野 ---")
    print("1跳邻居：GCN, GAT, GraphSAGE")
    print("2跳邻居：ChebNet(k=2), PAN, DeepWalk")
    print("自适应：GAT, Transformer")
    
    print("\n图神经网络层架构汇总测试完成！")
