# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / gcn_graph_convolutional_network

本文件实现 gcn_graph_convolutional_network 相关的算法功能。
"""

import numpy as np


def normalize_adjacency(adj):
    """
    归一化邻接矩阵（对称归一化）
    
    A_norm = D^(-1/2) * A * D^(-1/2)
    
    参数:
        adj: 邻接矩阵 (N, N)
    返回:
        归一化后的邻接矩阵
    """
    # 添加自环
    adj = adj + np.eye(adj.shape[0])
    
    # 计算度矩阵
    degrees = np.sum(adj, axis=1)
    
    # D^(-1/2)
    d_inv_sqrt = np.power(degrees, -0.5)
    d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
    
    # D^(-1/2) * A * D^(-1/2)
    d_mat_inv_sqrt = np.diag(d_inv_sqrt)
    normalized_adj = d_mat_inv_sqrt @ adj @ d_mat_inv_sqrt
    
    return normalized_adj


def compute_laplacian(adj):
    """
    计算归一化拉普拉斯矩阵
    
    L = I - D^(-1/2) * A * D^(-1/2)
    
    参数:
        adj: 邻接矩阵
    返回:
        L: 归一化拉普拉斯矩阵
    """
    # 归一化邻接矩阵
    adj_norm = normalize_adjacency(adj)
    
    # 拉普拉斯矩阵
    L = np.eye(adj.shape[0]) - adj_norm
    
    return L


def spectral_decomposition(L):
    """
    拉普拉斯矩阵的谱分解
    
    L = V * Λ * V^T
    
    参数:
        L: 拉普拉斯矩阵
    返回:
        eigenvalues: 特征值
        eigenvectors: 特征向量矩阵
    """
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    
    return eigenvalues, eigenvectors


def gcn_convolution(node_features, adj, num_layers=1, hidden_dim=16):
    """
    GCN卷积操作（简化版，直接使用邻接矩阵）
    
    H' = ReLU(A_norm * H * W)
    
    参数:
        node_features: 节点特征矩阵 (N, input_dim)
        adj: 邻接矩阵 (N, N)
        num_layers: 卷积层数
        hidden_dim: 隐藏层维度
    返回:
        output: 输出节点特征 (N, hidden_dim)
    """
    N, input_dim = node_features.shape
    
    # 归一化邻接矩阵
    adj_norm = normalize_adjacency(adj)
    
    # 初始化权重
    W1 = np.random.randn(input_dim, hidden_dim) * 0.01
    
    # 第一层图卷积
    H = node_features @ W1
    H = adj_norm @ H
    H = np.maximum(0, H)  # ReLU激活
    
    return H


class GCNLayer:
    """
    GCN层：单层图卷积网络
    
    前馈: H' = σ(A_norm * H * W + b)
    
    参数:
        in_features: 输入特征维度
        out_features: 输出特征维度
    """
    
    def __init__(self, in_features, out_features):
        self.in_features = in_features
        self.out_features = out_features
        
        # Xavier初始化权重
        self.W = np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features)
        self.bias = np.zeros(out_features)
        
        # 反向传播缓存
        self.H = None
        self.adj_norm = None
    
    def forward(self, node_features, adj):
        """
        前馈传播
        
        参数:
            node_features: 节点特征 (N, in_features)
            adj: 邻接矩阵 (N, N)
        返回:
            output: 输出特征 (N, out_features)
        """
        # 归一化邻接矩阵
        self.adj_norm = normalize_adjacency(adj)
        
        # 保存输入用于反向传播
        self.H = node_features
        
        # 图卷积操作
        output = self.adj_norm @ node_features @ self.W + self.bias
        
        # ReLU激活
        output = np.maximum(0, output)
        
        return output
    
    def backward(self, grad_output):
        """
        反向传播
        
        参数:
            grad_output: 损失对输出的梯度 (N, out_features)
        返回:
            grad_input: 损失对输入的梯度 (N, in_features)
        """
        # ReLU梯度
        grad_relu = grad_output * (self.H @ self.W + self.bias > 0).astype(float)
        
        # 对权重的梯度
        grad_W = (self.adj_norm @ self.H).T @ grad_output
        
        # 对输入的梯度（用于继续反向传播）
        grad_input = grad_output @ self.W.T
        grad_input = self.adj_norm.T @ grad_input
        
        # 更新权重（简化：直接应用梯度）
        self.W -= 0.01 * grad_W
        self.bias -= 0.01 * np.sum(grad_output, axis=0)
        
        return grad_input


class GCN:
    """
    完整GCN模型
    
    参数:
        input_dim: 输入特征维度
        hidden_dim: 隐藏层维度
        output_dim: 输出维度
        num_layers: GCN层数
    """
    
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers=2):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        
        # 构建层
        self.layers = []
        
        if num_layers == 1:
            self.layers.append(GCNLayer(input_dim, output_dim))
        else:
            # 第一层
            self.layers.append(GCNLayer(input_dim, hidden_dim))
            # 中间层
            for _ in range(num_layers - 2):
                self.layers.append(GCNLayer(hidden_dim, hidden_dim))
            # 输出层
            self.layers.append(GCNLayer(hidden_dim, output_dim))
    
    def forward(self, node_features, adj):
        """
        前馈传播
        
        参数:
            node_features: 节点特征 (N, input_dim)
            adj: 邻接矩阵 (N, N)
        返回:
            output: 输出 (N, output_dim)
        """
        H = node_features
        
        for i, layer in enumerate(self.layers):
            H = layer.forward(H, adj)
            
            # 最后一层不应用激活（通常用于分类）
            if i < len(self.layers) - 1:
                pass  # 激活已在层内应用
        
        return H
    
    def predict(self, node_features, adj):
        """预测：返回每个节点的类别"""
        logits = self.forward(node_features, adj)
        return np.argmax(logits, axis=1)


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("图卷积网络（GCN）测试")
    print("=" * 55)
    
    # 创建一个简单的图：7个节点，类似于Cora数据集的子图
    N = 7  # 节点数
    
    # 邻接矩阵（手动创建）
    adj = np.array([
        [0, 1, 1, 0, 0, 0, 0],
        [1, 0, 1, 1, 0, 0, 0],
        [1, 1, 0, 1, 1, 0, 0],
        [0, 1, 1, 0, 1, 1, 0],
        [0, 0, 1, 1, 0, 1, 1],
        [0, 0, 0, 1, 1, 0, 1],
        [0, 0, 0, 0, 1, 1, 0]
    ], dtype=float)
    
    print(f"节点数: {N}")
    print(f"边数: {int(np.sum(adj) / 2)}")
    
    # 节点特征（简化：每个节点用一个7维one-hot向量）
    node_features = np.eye(N)
    
    # 测试1：GCN卷积
    print("\n--- GCN卷积测试 ---")
    output = gcn_convolution(node_features, adj, hidden_dim=16)
    print(f"输入形状: {node_features.shape}")
    print(f"输出形状: {output.shape}")
    print(f"输出范围: [{output.min():.4f}, {output.max():.4f}]")
    
    # 测试2：GCN层前馈和反向传播
    print("\n--- GCN层前馈/反向传播 ---")
    gcn_layer = GCNLayer(in_features=7, out_features=16)
    output = gcn_layer.forward(node_features, adj)
    print(f"前馈输出形状: {output.shape}")
    
    grad = np.random.randn(N, 16)
    grad_input = gcn_layer.backward(grad)
    print(f"反向传播输入梯度形状: {grad_input.shape}")
    
    # 测试3：完整GCN模型
    print("\n--- 完整GCN模型测试 ---")
    gcn = GCN(input_dim=N, hidden_dim=16, output_dim=3, num_layers=2)
    
    logits = gcn.forward(node_features, adj)
    print(f"输入形状: {node_features.shape}")
    print(f"输出形状（logits）: {logits.shape}")
    
    predictions = gcn.predict(node_features, adj)
    print(f"预测类别: {predictions}")
    
    # 测试4：邻接矩阵归一化效果
    print("\n--- 邻接矩阵归一化效果 ---")
    adj_norm = normalize_adjacency(adj)
    
    print(f"原始邻接矩阵（非归一化）:")
    print(adj[:4, :4])
    print(f"\n归一化邻接矩阵:")
    print(adj_norm[:4, :4].round(3))
    
    # 测试5：拉普拉斯矩阵
    print("\n--- 拉普拉斯矩阵特征值 ---")
    L = compute_laplacian(adj)
    eigenvalues, _ = spectral_decomposition(L)
    
    print(f"特征值（最小的5个）: {eigenvalues[:5].round(3)}")
    print(f"最大特征值: {eigenvalues.max():.3f}")
    print(f"最小特征值: {eigenvalues.min():.3f}")
    
    # 测试6：模拟半监督节点分类
    print("\n--- 半监督节点分类模拟 ---")
    # 假设节点0和节点3有标签
    labeled_nodes = [0, 3]
    labels = [0, 2]  # 节点0是类别0，节点3是类别2
    
    # 训练（简化）
    for epoch in range(100):
        logits = gcn.forward(node_features, adj)
        # 简化损失：只考虑有标签的节点
        loss = 0.0
        for node, label in zip(labeled_nodes, labels):
            loss -= np.log(logits[node, label] + 1e-8)
        
        if (epoch + 1) % 20 == 0:
            preds = gcn.predict(node_features, adj)
            print(f"Epoch {epoch+1}: Loss={loss:.4f}, Predictions={preds}")
    
    print("\nGCN测试完成！")
