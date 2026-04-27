# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / gat_graph_attention_network

本文件实现 gat_graph_attention_network 相关的算法功能。
"""

import numpy as np


def leaky_relu(x, alpha=0.2):
    """Leaky ReLU"""
    return np.where(x > 0, x, alpha * x)


def softmax_by_row(x, axis=1):
    """按行softmax"""
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x_shifted)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


class AttentionLayer:
    """
    单头注意力层
    
    参数:
        in_features: 输入特征维度
        out_features: 输出特征维度
        alpha: LeakyReLU的负斜率
    """
    
    def __init__(self, in_features, out_features, alpha=0.2):
        self.in_features = in_features
        self.out_features = out_features
        self.alpha = alpha
        
        # 线性变换权重
        self.W = np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features)
        
        # 注意力向量
        self.a = np.random.randn(2 * out_features, 1) * 0.01
        
        # 缓存
        self.wh = None  # 变换后的特征
        self.e = None   # 注意力系数
        self.alpha_coef = None  # 最终注意力系数
    
    def forward(self, node_features, adj=None):
        """
        前馈传播
        
        参数:
            node_features: 节点特征 (N, in_features)
            adj: 邻接矩阵 (N, N)，可选
        返回:
            output: 聚合后的特征 (N, out_features)
            attention_weights: 注意力权重
        """
        N = node_features.shape[0]
        
        # 线性变换
        self.wh = node_features @ self.W  # (N, out_features)
        
        # 计算注意力系数 e_ij = LeakyReLU(a^T [Wh_i || Wh_j])
        # 拼接方式计算
        wh_i = self.wh.unsqueeze(1).repeat(1, N, 1)  # (N, N, out_features)
        wh_j = self.wh.unsqueeze(0).repeat(N, 1, 1)  # (N, N, out_features)
        
        # 拼接
        wh_concat = np.concatenate([wh_i, wh_j], axis=2)  # (N, N, 2*out_features)
        
        # 计算e
        e = (wh_concat @ self.a).squeeze(-1)  # (N, N)
        e = leaky_relu(e, self.alpha)
        
        # 掩码：对于没有边的节点，将e设为很小的值
        if adj is not None:
            self.e = np.where(adj > 0, e, -1e9)
        else:
            self.e = e
        
        # Softmax得到注意力系数
        self.alpha_coef = softmax_by_row(self.e, axis=1)  # (N, N)
        
        # 掩蔽自环（如果邻接矩阵包含自环，需要处理）
        if adj is not None:
            mask = adj + np.eye(N)
            self.alpha_coef = self.alpha_coef * (mask > 0)
            self.alpha_coef = self.alpha_coef / (np.sum(self.alpha_coef, axis=1, keepdims=True) + 1e-8)
        
        # 特征聚合
        output = self.alpha_coef @ self.wh  # (N, out_features)
        
        return output, self.alpha_coef


class MultiHeadAttention:
    """
    多头注意力机制
    
    参数:
        in_features: 输入特征维度
        out_features: 输出特征维度
        num_heads: 注意力头数
        alpha: LeakyReLU负斜率
        concat: 是否拼接多头输出（False则平均）
    """
    
    def __init__(self, in_features, out_features, num_heads=4, alpha=0.2, concat=True):
        self.num_heads = num_heads
        self.out_features = out_features
        self.concat = concat
        self.head_dim = out_features // num_heads
        
        assert out_features % num_heads == 0, "out_features must be divisible by num_heads"
        
        # 创建多个注意力头
        self.heads = []
        for _ in range(num_heads):
            head = AttentionLayer(in_features, self.head_dim, alpha)
            self.heads.append(head)
    
    def forward(self, node_features, adj=None):
        """
        多头注意力前馈传播
        
        参数:
            node_features: 节点特征 (N, in_features)
            adj: 邻接矩阵 (N, N)
        返回:
            output: 输出特征
            all_attentions: 所有头的注意力权重
        """
        all_outputs = []
        all_attentions = []
        
        for head in self.heads:
            head_out, head_att = head.forward(node_features, adj)
            all_outputs.append(head_out)
            all_attentions.append(head_att)
        
        # 拼接或平均
        if self.concat:
            output = np.concatenate(all_outputs, axis=1)  # (N, out_features)
        else:
            output = np.mean(all_outputs, axis=0)  # (N, out_features)
        
        return output, all_attentions


class GATLayer:
    """
    GAT层（封装多头注意力）
    
    参数:
        in_features: 输入特征维度
        out_features: 输出特征维度
        num_heads: 注意力头数
        alpha: LeakyReLU负斜率
        dropout: Dropout率（训练时）
    """
    
    def __init__(self, in_features, out_features, num_heads=4, alpha=0.2, dropout=0.0):
        self.in_features = in_features
        self.out_features = out_features
        self.num_heads = num_heads
        self.dropout = dropout
        self.training = True
        
        # 多头注意力
        self.attention = MultiHeadAttention(
            in_features, out_features, num_heads, alpha, concat=True
        )
        
        # 激活函数（ELU或LeakyReLU）
        self.activation = lambda x: leaky_relu(x, alpha)
    
    def forward(self, node_features, adj=None):
        """前馈传播"""
        output, attention_weights = self.attention.forward(node_features, adj)
        
        # 激活
        output = self.activation(output)
        
        return output, attention_weights
    
    def eval(self):
        """推理模式"""
        self.training = False
    
    def train(self):
        """训练模式"""
        self.training = True


class GAT:
    """
    完整GAT模型
    
    参数:
        input_dim: 输入特征维度
        hidden_dim: 隐藏层维度
        output_dim: 输出维度
        num_heads: 注意力头数
        num_layers: GAT层数
    """
    
    def __init__(self, input_dim, hidden_dim, output_dim, num_heads=4, num_layers=2):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        
        self.layers = []
        
        if num_layers == 1:
            self.layers.append(GATLayer(input_dim, output_dim, num_heads=1))
        else:
            # 第一层
            self.layers.append(GATLayer(input_dim, hidden_dim, num_heads))
            # 中间层
            for _ in range(num_layers - 2):
                self.layers.append(GATLayer(hidden_dim * num_heads, hidden_dim, num_heads))
            # 输出层
            self.layers.append(GATLayer(hidden_dim * num_heads, output_dim, num_heads=1))
    
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
            H, _ = layer.forward(H, adj)
        
        return H
    
    def predict(self, node_features, adj):
        """预测"""
        logits = self.forward(node_features, adj)
        return np.argmax(logits, axis=1)


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("图注意力网络（GAT）测试")
    print("=" * 55)
    
    # 创建测试图
    N = 6  # 节点数
    adj = np.array([
        [0, 1, 1, 0, 0, 0],
        [1, 0, 1, 1, 0, 0],
        [1, 1, 0, 1, 1, 0],
        [0, 1, 1, 0, 1, 1],
        [0, 0, 1, 1, 0, 1],
        [0, 0, 0, 1, 1, 0]
    ], dtype=float)
    
    # 节点特征
    node_features = np.random.randn(N, 8)
    
    print(f"节点数: {N}")
    print(f"边数: {int(np.sum(adj) / 2)}")
    
    # 测试1：单头注意力
    print("\n--- 单头注意力测试 ---")
    att_layer = AttentionLayer(in_features=8, out_features=4)
    output, attention = att_layer.forward(node_features, adj)
    
    print(f"输入形状: {node_features.shape}")
    print(f"输出形状: {output.shape}")
    print(f"注意力权重形状: {attention.shape}")
    
    # 查看注意力权重
    print(f"\n节点0的注意力权重: {attention[0].round(3)}")
    print(f"节点0最关注的邻居: 节点{np.argmax(attention[0])}")
    
    # 测试2：多头注意力
    print("\n--- 多头注意力测试 ---")
    multi_head = MultiHeadAttention(in_features=8, out_features=16, num_heads=4)
    output, attentions = multi_head.forward(node_features, adj)
    
    print(f"多头输出形状: {output.shape}")
    print(f"注意力头数: {len(attentions)}")
    print(f"每个头的注意力权重形状: {attentions[0].shape}")
    
    # 测试3：GAT层
    print("\n--- GAT层测试 ---")
    gat_layer = GATLayer(in_features=8, out_features=16, num_heads=4)
    output, _ = gat_layer.forward(node_features, adj)
    
    print(f"GAT层输出形状: {output.shape}")
    
    # 测试4：完整GAT模型
    print("\n--- 完整GAT模型测试 ---")
    gat = GAT(input_dim=8, hidden_dim=16, output_dim=3, num_heads=4, num_layers=2)
    
    logits = gat.forward(node_features, adj)
    print(f"GAT输出形状: {logits.shape}")
    
    predictions = gat.predict(node_features, adj)
    print(f"节点预测类别: {predictions}")
    
    # 测试5：注意力可视化分析
    print("\n--- 注意力权重分析 ---")
    gat_layer = GATLayer(in_features=8, out_features=16, num_heads=4)
    _, attentions = gat_layer.forward(node_features, adj)
    
    # 所有头的平均注意力
    avg_attention = np.mean(attentions[0], axis=0) if len(attentions) > 0 else attentions[0]
    
    print("节点间的平均注意力权重:")
    print(f"{'节点':>6} | {'最关注':>8} | {'注意力值':>10}")
    print("-" * 30)
    for i in range(N):
        neighbors = np.where(adj[i] > 0)[0]
        if len(neighbors) > 0:
            att_values = avg_attention[i, neighbors]
            most_attentive = neighbors[np.argmax(att_values)]
            print(f"{i:6d} | {most_attentive:8d} | {avg_attention[i, most_attentive]:10.4f}")
    
    # 测试6：多头注意力的差异
    print("\n--- 多头注意力的差异分析 ---")
    gat_layer2 = GATLayer(in_features=8, out_features=16, num_heads=4)
    _, attentions2 = gat_layer2.forward(node_features, adj)
    
    # 计算不同头之间的注意力差异
    att_diff = []
    for h1 in range(len(attentions2)):
        for h2 in range(h1 + 1, len(attentions2)):
            diff = np.abs(attentions2[h1] - attentions2[h2]).mean()
            att_diff.append(diff)
    
    print(f"不同头之间注意力权重的平均差异: {np.mean(att_diff):.4f}")
    
    # 测试7：对比GCN和GAT
    print("\n--- GCN vs GAT 对比 ---")
    # GCN权重
    W_gcn = np.random.randn(8, 16) * 0.01
    adj_norm = adj / (np.sum(adj, axis=1, keepdims=True) + 1e-8)
    h_gcn = adj_norm @ node_features @ W_gcn
    h_gcn = np.maximum(0, h_gcn)  # ReLU
    
    # GAT输出
    gat_layer3 = GATLayer(in_features=8, out_features=16, num_heads=4)
    h_gat, _ = gat_layer3.forward(node_features, adj)
    
    print(f"GCN输出范围: [{h_gcn.min():.4f}, {h_gcn.max():.4f}]")
    print(f"GAT输出范围: [{h_gat.min():.4f}, {h_gat.max():.4f}]")
    print(f"GCN和GAT输出的相关性: {np.corrcoef(h_gcn.flatten(), h_gat.flatten())[0,1]:.4f}")
    
    print("\nGAT测试完成！")
