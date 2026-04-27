# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / gin_graph_isomorphism_network

本文件实现 gin_graph_isomorphism_network 相关的算法功能。
"""

import numpy as np


def mlp_forward(x, W, b):
    """MLP前馈"""
    return np.maximum(0, x @ W + b)  # ReLU


class GINLayer:
    """
    GIN层（图同构网络层）
    
    核心公式：h_k^{(v)} = MLP^{(k)}( (1 + ε) * h_{k-1}^{(v)} + Σ_{u∈N(v)} h_{k-1}^{(u)} )
    
    参数:
        input_dim: 输入特征维度
        hidden_dim: 隐藏层维度
        epsilon: 可学习的ε参数（初始为0）
    """
    
    def __init__(self, input_dim, hidden_dim, epsilon=0.0):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.epsilon = epsilon
        
        # MLP参数
        self.W1 = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(hidden_dim)
        
        # 可学习的epsilon
        self.eps = np.array(epsilon)
    
    def forward(self, node_features, adj):
        """
        GIN层前馈传播
        
        参数:
            node_features: 节点特征 (N, input_dim)
            adj: 邻接矩阵 (N, N)
        返回:
            output: 更新后的节点特征 (N, hidden_dim)
        """
        N = node_features.shape[0]
        
        # 聚合邻居特征
        neighbor_sum = adj @ node_features  # Σ h_{k-1}^{(u)}
        
        # 加上自身特征（带epsilon）
        combined = (1 + self.eps) * node_features + neighbor_sum
        
        # 通过MLP
        h = mlp_forward(combined, self.W1, self.b1)
        h = mlp_forward(h, self.W2, self.b2)
        
        return h
    
    def forward_with_edge_features(self, node_features, edge_index, edge_weights=None):
        """
        基于边索引的前馈传播（更高效的稀疏表示）
        
        参数:
            node_features: 节点特征
            edge_index: 边索引 (2, num_edges)
            edge_weights: 边权重 (num_edges,)
        返回:
            output: 更新后的节点特征
        """
        N = node_features.shape[0]
        num_edges = edge_index.shape[1]
        
        # 初始化邻居聚合
        neighbor_agg = np.zeros_like(node_features)
        
        # 聚合邻居特征
        for i in range(num_edges):
            src = edge_index[0, i]
            dst = edge_index[1, i]
            weight = edge_weights[i] if edge_weights is not None else 1.0
            neighbor_agg[dst] += weight * node_features[src]
        
        # 组合
        combined = (1 + self.eps) * node_features + neighbor_agg
        
        # MLP
        h = mlp_forward(combined, self.W1, self.b1)
        h = mlp_forward(h, self.W2, self.b2)
        
        return h


class GIN:
    """
    完整GIN模型
    
    参数:
        input_dim: 输入特征维度
        hidden_dim: 隐藏层维度
        output_dim: 输出维度
        num_layers: GIN层数
        final_mlp: 是否在最后一层使用MLP
    """
    
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers=3, final_mlp=True):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        
        self.layers = []
        
        # 第一层
        self.layers.append(GINLayer(input_dim, hidden_dim))
        
        # 中间层
        for _ in range(num_layers - 2):
            self.layers.append(GINLayer(hidden_dim, hidden_dim))
        
        # 输出层
        if final_mlp:
            self.layers.append(GINLayer(hidden_dim, output_dim))
        else:
            self.layers.append(GINLayer(hidden_dim, output_dim))
        
        self.final_mlp = final_mlp
    
    def forward(self, node_features, adj):
        """
        前馈传播
        
        参数:
            node_features: 节点特征 (N, input_dim)
            adj: 邻接矩阵 (N, N)
        返回:
            output: 节点嵌入 (N, output_dim)
        """
        H = node_features
        
        for i, layer in enumerate(self.layers):
            H = layer.forward(H, adj)
        
        return H
    
    def readout(self, node_features):
        """
        图级别读出操作（将节点特征汇总为图特征）
        
        参数:
            node_features: 节点特征 (N, hidden_dim)
        返回:
            graph_feature: 图级别特征
        """
        # 求和读出（GIN常用）
        return np.sum(node_features, axis=0)
    
    def predict(self, node_features, adj):
        """预测节点类别"""
        logits = self.forward(node_features, adj)
        return np.argmax(logits, axis=1)


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("图同构网络（GIN）测试")
    print("=" * 55)
    
    # 创建测试图
    N = 6
    adj = np.array([
        [0, 1, 1, 0, 0, 0],
        [1, 0, 1, 1, 0, 0],
        [1, 1, 0, 1, 1, 0],
        [0, 1, 1, 0, 1, 1],
        [0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0]
    ], dtype=float)
    
    node_features = np.random.randn(N, 8)
    
    print(f"节点数: {N}")
    print(f"边数: {int(np.sum(adj) / 2)}")
    
    # 测试1：GIN层前馈
    print("\n--- GIN层前馈测试 ---")
    gin_layer = GINLayer(input_dim=8, hidden_dim=16)
    output = gin_layer.forward(node_features, adj)
    
    print(f"输入形状: {node_features.shape}")
    print(f"输出形状: {output.shape}")
    print(f"输出范围: [{output.min():.4f}, {output.max():.4f}]")
    
    # 测试2：epsilon参数
    print("\n--- epsilon参数测试 ---")
    gin_layer_eps = GINLayer(input_dim=8, hidden_dim=16, epsilon=0.5)
    output_eps = gin_layer_eps.forward(node_features, adj)
    
    print(f"epsilon={0.0}: {output[:2, :3].round(3)}")
    print(f"epsilon={0.5}: {output_eps[:2, :3].round(3)}")
    
    # 测试3：完整GIN模型
    print("\n--- 完整GIN模型测试 ---")
    gin = GIN(input_dim=8, hidden_dim=16, output_dim=4, num_layers=3)
    
    embeddings = gin.forward(node_features, adj)
    print(f"节点嵌入形状: {embeddings.shape}")
    
    # 图级别读出
    graph_feature = gin.readout(embeddings)
    print(f"图级别特征形状: {graph_feature.shape}")
    
    # 预测
    predictions = gin.predict(node_features, adj)
    print(f"节点预测: {predictions}")
    
    # 测试4：基于边索引的前馈
    print("\n--- 边索引前馈测试 ---")
    edge_index = np.array([
        [0, 1, 1, 2, 2, 3, 3, 4, 4, 5],
        [1, 0, 2, 1, 3, 2, 4, 3, 5, 4]
    ])
    
    output_sparse = gin_layer.forward_with_edge_features(node_features, edge_index)
    print(f"稀疏前馈输出形状: {output_sparse.shape}")
    
    # 测试5：GIN的1-WL同构测试能力验证
    print("\n--- 1-WL同构测试能力 ---")
    # 创建两个同构的图（三角形-边-三角形）
    adj1 = np.array([
        [0, 1, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [0, 1, 1, 0]
    ], dtype=float)
    
    # GIN应该能区分非同构图
    adj2 = np.array([
        [0, 1, 0, 1],
        [1, 0, 1, 1],
        [0, 1, 0, 1],
        [1, 1, 1, 0]
    ], dtype=float)
    
    # 节点特征
    feat1 = np.ones((4, 4))
    feat2 = np.ones((4, 4))
    
    gin_test = GIN(input_dim=4, hidden_dim=8, output_dim=8, num_layers=2)
    
    emb1 = gin_test.forward(feat1, adj1)
    emb2 = gin_test.forward(feat2, adj2)
    
    print(f"图1嵌入: {emb1.sum(axis=1).round(3)}")
    print(f"图2嵌入: {emb2.sum(axis=1).round(3)}")
    
    # 测试6：多层GIN
    print("\n--- 多层GIN效果 ---")
    for num_layers in [1, 2, 3, 4]:
        gin_multi = GIN(input_dim=8, hidden_dim=16, output_dim=4, num_layers=num_layers)
        emb = gin_multi.forward(node_features, adj)
        print(f"  {num_layers}层: 嵌入范围=[{emb.min():.4f}, {emb.max():.4f}]")
    
    # 测试7：与GCN对比
    print("\n--- GIN vs 其他聚合方式 ---")
    # GIN使用求和聚合，具有更强的表达能力
    # 与GCN的归一化聚合对比
    
    # GCN风格聚合（归一化）
    adj_norm = adj / (np.sum(adj, axis=1, keepdims=True) + 1e-8)
    gcn_style = adj_norm @ node_features @ (np.random.randn(8, 16) * 0.01)
    gcn_style = np.maximum(0, gcn_style)
    
    # GIN风格聚合（求和）
    gin_style = adj @ node_features @ (np.random.randn(8, 16) * 0.01)
    gin_style = np.maximum(0, gin_style)
    
    print(f"归一化聚合后均值: {gcn_style.mean():.4f}")
    print(f"求和聚合后均值: {gin_style.mean():.4f}")
    print("GIN的求和聚合能保留更多信息（度越大的节点聚合越多）")
    
    print("\nGIN测试完成！")
