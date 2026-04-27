# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / graphsage

本文件实现 graphsage 相关的算法功能。
"""

import numpy as np
import random


def uniform_sample(neighbors, num_samples):
    """
    均匀采样邻居
    
    参数:
        neighbors: 邻居节点列表
        num_samples: 采样数量
    返回:
        sampled: 采样后的邻居
    """
    if len(neighbors) <= num_samples:
        return neighbors
    return random.sample(neighbors, num_samples)


def get_neighbors(adj, node, num_samples=None):
    """
    获取节点的邻居
    
    参数:
        adj: 邻接矩阵
        node: 节点索引
        num_samples: 采样数量（可选）
    返回:
        neighbors: 邻居节点列表
    """
    neighbors = np.where(adj[node] > 0)[0].tolist()
    
    if num_samples is not None and len(neighbors) > num_samples:
        neighbors = uniform_sample(neighbors, num_samples)
    
    return neighbors


# ============================
# 聚合函数
# ============================

class MeanAggregator:
    """
    均值聚合器：简单地将邻居节点的特征取平均
    
    h_agg = MEAN({h_j for j in neighbors})
    """
    
    def __init__(self, input_dim, output_dim):
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # 线性变换权重（可选，用于维度变换）
        self.linear = np.random.randn(input_dim, output_dim) * np.sqrt(2.0 / input_dim)
        self.bias = np.zeros(output_dim)
    
    def aggregate(self, node_features, neighbors):
        """
        聚合邻居特征
        
        参数:
            node_features: 所有节点的特征 (N, input_dim)
            neighbors: 某个节点的邻居列表
        返回:
            aggregated: 聚合后的特征 (output_dim,)
        """
        if len(neighbors) == 0:
            return np.zeros(self.output_dim)
        
        # 获取邻居特征并求平均
        neighbor_features = node_features[neighbors]
        mean_features = np.mean(neighbor_features, axis=0)
        
        # 线性变换
        output = mean_features @ self.linear + self.bias
        
        return output
    
    def forward(self, node_features, neighbor_lists):
        """
        对所有节点执行聚合
        
        参数:
            node_features: 所有节点特征 (N, input_dim)
            neighbor_lists: 每个节点的邻居列表字典 {node: [neighbors]}
        返回:
            outputs: 聚合结果 (N, output_dim)
        """
        N = node_features.shape[0]
        outputs = np.zeros((N, self.output_dim))
        
        for node in range(N):
            neighbors = neighbor_lists.get(node, [])
            outputs[node] = self.aggregate(node_features, neighbors)
        
        return outputs


class LSTMAggregator:
    """
    LSTM聚合器：使用LSTM对邻居节点序列进行编码
    
    参数:
        input_dim: 输入特征维度
        output_dim: 输出维度
    """
    
    def __init__(self, input_dim, output_dim):
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # 简化的LSTM参数（实际应使用完整LSTM）
        self.W = np.random.randn(input_dim, output_dim) * 0.01
        self.U = np.random.randn(output_dim, output_dim) * 0.01
        self.b = np.zeros(output_dim)
        
        # 隐藏状态
        self.h = None
        self.c = None
    
    def lstm_step(self, x, h, c):
        """单步LSTM"""
        # 简化版：只实现核心的遗忘门和输入门
        f = sigmoid(np.dot(x, self.W) + np.dot(h, self.U) + self.b)
        i = sigmoid(np.dot(x, self.W) + np.dot(h, self.U) + self.b)
        
        c_new = f * c + i * np.tanh(np.dot(x, self.W) + np.dot(h, self.U) + self.b)
        h_new = np.tanh(c_new) * sigmoid(np.dot(x, self.W) + np.dot(h, self.U) + self.b)
        
        return h_new, c_new
    
    def aggregate(self, node_features, neighbors):
        """LSTM聚合"""
        if len(neighbors) == 0:
            return np.zeros(self.output_dim)
        
        # 初始化隐藏状态
        h = np.zeros(self.output_dim)
        c = np.zeros(self.output_dim)
        
        # 随机打乱邻居顺序（关键：LSTM聚合需要无序输入）
        random.shuffle(neighbors)
        
        # 依次处理每个邻居
        for neighbor in neighbors:
            neighbor_feat = node_features[neighbor]
            h, c = self.lstm_step(neighbor_feat, h, c)
        
        return h
    
    def forward(self, node_features, neighbor_lists):
        """对所有节点执行LSTM聚合"""
        N = node_features.shape[0]
        outputs = np.zeros((N, self.output_dim))
        
        for node in range(N):
            neighbors = neighbor_lists.get(node, [])
            outputs[node] = self.aggregate(node_features, neighbors)
        
        return outputs


class PoolingAggregator:
    """
    池化聚合器：先对邻居特征做MLP，再用池化
    
    h_agg = MAX({MLP(h_j) for j in neighbors})
    """
    
    def __init__(self, input_dim, output_dim):
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        # MLP参数
        self.W = np.random.randn(input_dim, output_dim) * np.sqrt(2.0 / input_dim)
        self.b = np.zeros(output_dim)
    
    def aggregate(self, node_features, neighbors):
        """池化聚合"""
        if len(neighbors) == 0:
            return np.zeros(self.output_dim)
        
        # 获取邻居特征
        neighbor_features = node_features[neighbors]
        
        # MLP + ReLU
        h = neighbor_features @ self.W + self.b
        h = np.maximum(0, h)  # ReLU
        
        # Max pooling
        pooled = np.max(h, axis=0)
        
        return pooled
    
    def forward(self, node_features, neighbor_lists):
        """对所有节点执行池化聚合"""
        N = node_features.shape[0]
        outputs = np.zeros((N, self.output_dim))
        
        for node in range(N):
            neighbors = neighbor_lists.get(node, [])
            outputs[node] = self.aggregate(node_features, neighbors)
        
        return outputs


def sigmoid(x):
    """Sigmoid"""
    x = np.clip(x, -500, 500)
    return 1 / (1 + np.exp(-x))


# ============================
# GraphSAGE层
# ============================

class GraphSAGELayer:
    """
    GraphSAGE层
    
    参数:
        input_dim: 输入特征维度
        output_dim: 输出特征维度
        aggregator_type: 聚合器类型 ('mean', 'lstm', 'pooling')
    """
    
    def __init__(self, input_dim, output_dim, aggregator_type='mean'):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.aggregator_type = aggregator_type
        
        # 创建聚合器
        if aggregator_type == 'mean':
            self.aggregator = MeanAggregator(input_dim, output_dim)
        elif aggregator_type == 'lstm':
            self.aggregator = LSTMAggregator(input_dim, output_dim)
        elif aggregator_type == 'pooling':
            self.aggregator = PoolingAggregator(input_dim, output_dim)
        else:
            raise ValueError(f"Unknown aggregator: {aggregator_type}")
        
        # 自身特征的变换权重（用于拼接）
        self.self_transform = np.random.randn(input_dim, output_dim) * np.sqrt(2.0 / input_dim)
    
    def forward(self, node_features, adj, neighbor_lists=None):
        """
        GraphSAGE前馈传播
        
        参数:
            node_features: 节点特征 (N, input_dim)
            adj: 邻接矩阵 (N, N)
            neighbor_lists: 邻居列表（可选，不提供则自动计算）
        返回:
            output: 更新后的节点特征 (N, output_dim)
        """
        N = node_features.shape[0]
        
        # 如果没有提供邻居列表，从邻接矩阵构建
        if neighbor_lists is None:
            neighbor_lists = {i: np.where(adj[i] > 0)[0].tolist() for i in range(N)}
        
        # 聚合邻居特征
        neighbor_agg = self.aggregator.forward(node_features, neighbor_lists)
        
        # 自身特征变换
        self_feat = node_features @ self.self_transform
        
        # 拼接并激活
        combined = np.concatenate([self_feat, neighbor_agg], axis=1)
        
        # 最终变换（压缩到output_dim）
        output = combined @ (np.random.randn(2 * self.output_dim, self.output_dim) * 0.01)
        
        return output


class GraphSAGE:
    """
    完整GraphSAGE模型
    
    参数:
        input_dim: 输入特征维度
        hidden_dim: 隐藏层维度
        output_dim: 输出维度
        num_layers: SAGE层数
        aggregator: 聚合器类型
    """
    
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers=2, aggregator='mean'):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        
        self.layers = []
        
        if num_layers == 1:
            self.layers.append(GraphSAGELayer(input_dim, output_dim, aggregator))
        else:
            self.layers.append(GraphSAGELayer(input_dim, hidden_dim, aggregator))
            for _ in range(num_layers - 2):
                self.layers.append(GraphSAGELayer(hidden_dim, hidden_dim, aggregator))
            self.layers.append(GraphSAGELayer(hidden_dim, output_dim, aggregator))
    
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
        
        # 构建邻居列表
        N = node_features.shape[0]
        neighbor_lists = {i: np.where(adj[i] > 0)[0].tolist() for i in range(N)}
        
        for layer in self.layers:
            H = layer.forward(H, adj, neighbor_lists)
        
        return H


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    random.seed(42)
    
    print("=" * 55)
    print("GraphSAGE测试")
    print("=" * 55)
    
    # 创建测试图
    N = 8
    adj = np.array([
        [0, 1, 1, 1, 0, 0, 0, 0],
        [1, 0, 1, 0, 1, 1, 0, 0],
        [1, 1, 0, 1, 1, 0, 1, 0],
        [1, 0, 1, 0, 0, 1, 1, 0],
        [0, 1, 1, 0, 0, 1, 0, 1],
        [0, 1, 0, 1, 1, 0, 1, 1],
        [0, 0, 1, 1, 0, 1, 0, 1],
        [0, 0, 0, 0, 1, 1, 1, 0]
    ], dtype=float)
    
    node_features = np.random.randn(N, 16)
    
    print(f"节点数: {N}")
    print(f"边数: {int(np.sum(adj) / 2)}")
    
    # 构建邻居列表
    neighbor_lists = {i: np.where(adj[i] > 0)[0].tolist() for i in range(N)}
    print(f"\n邻居表示例（节点0）: {neighbor_lists[0]}")
    
    # 测试1：Mean聚合器
    print("\n--- Mean聚合器测试 ---")
    mean_agg = MeanAggregator(input_dim=16, output_dim=32)
    output = mean_agg.forward(node_features, neighbor_lists)
    print(f"输入形状: {node_features.shape}")
    print(f"输出形状: {output.shape}")
    
    # 测试2：LSTM聚合器
    print("\n--- LSTM聚合器测试 ---")
    lstm_agg = LSTMAggregator(input_dim=16, output_dim=32)
    output_lstm = lstm_agg.forward(node_features, neighbor_lists)
    print(f"LSTM输出形状: {output_lstm.shape}")
    
    # 测试3：Pooling聚合器
    print("\n--- Pooling聚合器测试 ---")
    pool_agg = PoolingAggregator(input_dim=16, output_dim=32)
    output_pool = pool_agg.forward(node_features, neighbor_lists)
    print(f"Pooling输出形状: {output_pool.shape}")
    
    # 测试4：不同聚合器对比
    print("\n--- 不同聚合器输出对比 ---")
    print(f"Mean输出均值: {output.mean():.4f}, 标准差: {output.std():.4f}")
    print(f"LSTM输出均值: {output_lstm.mean():.4f}, 标准差: {output_lstm.std():.4f}")
    print(f"Pool输出均值: {output_pool.mean():.4f}, 标准差: {output_pool.std():.4f}")
    
    # 测试5：GraphSAGE层
    print("\n--- GraphSAGE层测试 ---")
    sage_layer = GraphSAGELayer(input_dim=16, output_dim=32, aggregator_type='mean')
    output_sage = sage_layer.forward(node_features, adj, neighbor_lists)
    print(f"GraphSAGE层输出形状: {output_sage.shape}")
    
    # 测试6：完整GraphSAGE模型
    print("\n--- 完整GraphSAGE模型测试 ---")
    sage = GraphSAGE(input_dim=16, hidden_dim=32, output_dim=8, num_layers=2, aggregator='mean')
    embeddings = sage.forward(node_features, adj)
    print(f"GraphSAGE嵌入形状: {embeddings.shape}")
    print(f"嵌入范围: [{embeddings.min():.4f}, {embeddings.max():.4f}]")
    
    # 测试7：邻居采样效果
    print("\n--- 邻居采样测试 ---")
    original_neighbors = neighbor_lists[0]
    print(f"节点0原始邻居: {original_neighbors}")
    
    sampled_neighbors = uniform_sample(original_neighbors, num_samples=2)
    print(f"采样2个邻居: {sampled_neighbors}")
    
    # 测试8：聚合器类型对结果的影响
    print("\n--- 聚合器类型对节点0嵌入的影响 ---")
    for agg_type in ['mean', 'lstm', 'pooling']:
        agg = MeanAggregator(16, 32) if agg_type == 'mean' else \
              LSTMAggregator(16, 32) if agg_type == 'lstm' else \
              PoolingAggregator(16, 32)
        
        output = agg.aggregate(node_features, original_neighbors)
        print(f"  {agg_type:6s}: {output[:5].round(3)}")
    
    # 测试9：多跳邻居聚合
    print("\n--- 多跳邻居信息 ---")
    def get_k_hop_neighbors(adj, node, k):
        """获取k跳邻居"""
        neighbors = {0: [node]}
        current = {node}
        
        for hop in range(1, k + 1):
            hop_neighbors = set()
            for n in current:
                hop_neighbors.update(np.where(adj[n] > 0)[0])
            hop_neighbors -= set(neighbors[0])
            neighbors[hop] = list(hop_neighbors)
            current = hop_neighbors
        
        return neighbors
    
    multi_hop = get_k_hop_neighbors(adj, 0, k=2)
    for hop, neighs in multi_hop.items():
        print(f"  {hop}跳邻居: {neighs}")
    
    print("\nGraphSAGE测试完成！")
