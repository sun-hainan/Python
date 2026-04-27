# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / graph_transformer

本文件实现 graph_transformer 相关的算法功能。
"""

import numpy as np


# ============================
# 位置编码
# ============================

def laplacian_positional_encoding(adj, num_encodings=16):
    """
    拉普拉斯位置编码（Laplacian PE）
    
    基于归一化拉普拉斯矩阵的特征向量作为位置编码。
    类似于Transformer中的正弦/余弦位置编码，但利用图结构。
    
    参数:
        adj: 邻接矩阵 (N, N)
        num_encodings: 编码维度
    返回:
        pos_encoding: 位置编码 (N, num_encodings)
    """
    N = adj.shape[0]
    
    # 添加自环
    adj = adj + np.eye(N)
    
    # 度矩阵
    degrees = np.sum(adj, axis=1)
    d_inv_sqrt = np.power(degrees, -0.5)
    d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0
    d_mat_inv_sqrt = np.diag(d_inv_sqrt)
    
    # 归一化拉普拉斯矩阵
    L_norm = np.eye(N) - d_mat_inv_sqrt @ adj @ d_mat_inv_sqrt
    
    # 特征分解
    eigenvalues, eigenvectors = np.linalg.eigh(L_norm)
    
    # 取最小的特征向量作为位置编码
    # 跳过第一个特征向量（对应特征值0）
    pos_encoding = eigenvectors[:, 1:num_encodings+1]
    
    # 如果编码维度大于N-1，用零填充
    if pos_encoding.shape[1] < num_encodings:
        padding = np.zeros((N, num_encodings - pos_encoding.shape[1]))
        pos_encoding = np.concatenate([pos_encoding, padding], axis=1)
    
    return pos_encoding


def random_walk_positional_encoding(adj, walk_length=10, num_walks=10):
    """
    随机游走位置编码
    通过从每个节点出发的随机游走，统计访问各节点的频率作为编码。
    
    参数:
        adj: 邻接矩阵
        walk_length: 游走长度
        num_walks: 每个节点的游走次数
    返回:
        rwpe: 随机游走位置编码 (N, N)
    """
    N = adj.shape[0]
    
    # 构建邻接表
    adj_list = {}
    for i in range(N):
        neighbors = np.where(adj[i] > 0)[0]
        if len(neighbors) > 0:
            adj_list[i] = neighbors
        else:
            adj_list[i] = np.array([i])
    
    # 初始化访问计数
    rwpe = np.zeros((N, N))
    
    for start_node in range(N):
        for _ in range(num_walks):
            current = start_node
            for step in range(walk_length):
                rwpe[start_node, current] += 1
                
                # 随机游走到邻居
                neighbors = adj_list.get(current, np.array([current]))
                current = np.random.choice(neighbors)
    
    # 归一化
    rwpe = rwpe / (rwpe.sum(axis=1, keepdims=True) + 1e-8)
    
    return rwpe


def signals_on_graph(pos_encoding, signals):
    """
    在图上传播信号得到节点表示（用于位置编码的增强）
    
    参数:
        pos_encoding: 位置编码
        signals: 初始信号
    返回:
        enhanced: 增强后的表示
    """
    # 简化版：直接拼接
    return np.concatenate([signals, pos_encoding], axis=1)


# ============================
# 图注意力机制
# ============================

def masked_attention(query, key, value, mask=None, scale=True):
    """
    带掩码的注意力机制
    
    参数:
        query: 查询向量 (num_heads, N, head_dim)
        key: 键向量
        value: 值向量
        mask: 注意力掩码 (N, N)
        scale: 是否缩放
    返回:
        output: 注意力输出
        attention_weights: 注意力权重
    """
    if scale:
        d_k = query.shape[-1]
        scores = np.dot(query, key.transpose(0, 2, 1)) / np.sqrt(d_k)
    else:
        scores = np.dot(query, key.transpose(0, 2, 1))
    
    # 应用掩码
    if mask is not None:
        scores = np.where(mask > 0, scores, -1e9)
    
    # Softmax
    exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
    attention_weights = exp_scores / (np.sum(exp_scores, axis=-1, keepdims=True) + 1e-8)
    
    # 加权求和
    output = np.dot(attention_weights, value)
    
    return output, attention_weights


# ============================
# 图Transformer层
# ============================

class GraphTransformerLayer:
    """
    图Transformer层
    
    参数:
        node_dim: 节点特征维度
        num_heads: 注意力头数
        dim_feedforward: 前馈网络维度
        dropout: Dropout率
    """
    
    def __init__(self, node_dim, num_heads=4, dim_feedforward=64, dropout=0.0):
        self.node_dim = node_dim
        self.num_heads = num_heads
        self.head_dim = node_dim // num_heads
        self.dim_feedforward = dim_feedforward
        
        assert node_dim % num_heads == 0, "node_dim must be divisible by num_heads"
        
        # QKV变换
        self.W_q = np.random.randn(node_dim, node_dim) * np.sqrt(2.0 / node_dim)
        self.W_k = np.random.randn(node_dim, node_dim) * np.sqrt(2.0 / node_dim)
        self.W_v = np.random.randn(node_dim, node_dim) * np.sqrt(2.0 / node_dim)
        
        # 输出变换
        self.W_o = np.random.randn(node_dim, node_dim) * np.sqrt(2.0 / node_dim)
        
        # 前馈网络
        self.W_ff1 = np.random.randn(node_dim, dim_feedforward) * np.sqrt(2.0 / node_dim)
        self.W_ff2 = np.random.randn(dim_feedforward, node_dim) * np.sqrt(2.0 / dim_feedforward)
        
        self.dropout = dropout
        self.training = True
    
    def forward(self, node_features, adj, pos_encoding=None):
        """
        前馈传播
        
        参数:
            node_features: 节点特征 (N, node_dim)
            adj: 邻接矩阵 (N, N)
            pos_encoding: 位置编码 (N, pe_dim)，可选
        返回:
            output: 输出特征 (N, node_dim)
            attention_weights: 注意力权重
        """
        N = node_features.shape[0]
        
        # 如果有位置编码，拼接到节点特征
        if pos_encoding is not None:
            node_features = np.concatenate([node_features, pos_encoding], axis=1)
            # 调整QKV维度（简化处理：截断或填充）
            actual_dim = node_features.shape[1]
            if actual_dim > self.node_dim:
                node_features = node_features[:, :self.node_dim]
            elif actual_dim < self.node_dim:
                padding = np.zeros((N, self.node_dim - actual_dim))
                node_features = np.concatenate([node_features, padding], axis=1)
        
        # QKV计算
        Q = node_features @ self.W_q
        K = node_features @ self.W_k
        V = node_features @ self.W_v
        
        # 重塑为多头形式 (num_heads, N, head_dim)
        Q = Q.reshape(N, self.num_heads, self.head_dim).transpose(1, 0, 2)
        K = K.reshape(N, self.num_heads, self.head_dim).transpose(1, 0, 2)
        V = V.reshape(N, self.num_heads, self.head_dim).transpose(1, 0, 2)
        
        # 构建注意力掩码（只允许相邻节点之间注意）
        if adj is not None:
            # adj_mask[i,j] = 1 表示 i可以关注j
            adj_mask = (adj > 0).astype(float)
            # 添加自环
            adj_mask = adj_mask + np.eye(N)
        else:
            adj_mask = np.ones((N, N))
        
        # 缩放点积注意力
        d_k = self.head_dim
        scores = np.dot(Q, K.transpose(0, 2, 1)) / np.sqrt(d_k)
        
        # 应用掩码
        scores = np.where(adj_mask > 0, scores, -1e9)
        
        # Softmax
        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attention_weights = exp_scores / (np.sum(exp_scores, axis=-1, keepdims=True) + 1e-8)
        
        # 注意力加权
        attended = np.dot(attention_weights, V)  # (num_heads, N, head_dim)
        
        # 合并多头
        attended = attended.transpose(1, 0, 2).reshape(N, -1)  # (N, node_dim)
        
        # 输出投影
        output = attended @ self.W_o
        
        # 前馈网络
        ff_output = np.maximum(0, output @ self.W_ff1)  # ReLU
        ff_output = ff_output @ self.W_ff2
        
        # 残差连接和层归一化（简化版）
        output = output + ff_output
        
        return output, attention_weights


class GraphTransformer:
    """
    完整GraphTransformer模型
    
    参数:
        input_dim: 输入维度
        hidden_dim: 隐藏维度
        output_dim: 输出维度
        num_heads: 注意力头数
        num_layers: 层数
        pe_type: 位置编码类型 ('laplacian', 'random_walk', None)
    """
    
    def __init__(self, input_dim, hidden_dim, output_dim, num_heads=4,
                 num_layers=2, pe_type='laplacian'):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.pe_type = pe_type
        
        self.layers = []
        
        # 输入投影
        self.input_proj = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / input_dim)
        
        # 多层Transformer
        for _ in range(num_layers):
            self.layers.append(GraphTransformerLayer(
                hidden_dim, num_heads, hidden_dim * 2
            ))
        
        # 输出投影
        self.output_proj = np.random.randn(hidden_dim, output_dim) * np.sqrt(2.0 / hidden_dim)
    
    def forward(self, node_features, adj):
        """
        前馈传播
        
        参数:
            node_features: 节点特征 (N, input_dim)
            adj: 邻接矩阵 (N, N)
        返回:
            output: 输出 (N, output_dim)
        """
        # 输入投影
        H = node_features @ self.input_proj
        
        # 位置编码
        if self.pe_type == 'laplacian':
            pos_enc = laplacian_positional_encoding(adj, num_encodings=self.hidden_dim)
        elif self.pe_type == 'random_walk':
            pos_enc = random_walk_positional_encoding(adj)[:, :self.hidden_dim]
        else:
            pos_enc = None
        
        # 多层Transformer
        for layer in self.layers:
            H, _ = layer.forward(H, adj, pos_enc)
        
        # 输出投影
        output = H @ self.output_proj
        
        return output


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("图Transformer测试")
    print("=" * 55)
    
    # 创建测试图
    N = 8
    adj = np.zeros((N, N))
    
    # 创建一个简单的环形图
    for i in range(N):
        adj[i, (i + 1) % N] = 1
        adj[i, (i - 1) % N] = 1
    
    node_features = np.random.randn(N, 16)
    
    print(f"节点数: {N}")
    print(f"边数: {int(np.sum(adj) / 2)}")
    
    # 测试1：拉普拉斯位置编码
    print("\n--- 拉普拉斯位置编码 ---")
    lap_pe = laplacian_positional_encoding(adj, num_encodings=8)
    
    print(f"位置编码形状: {lap_pe.shape}")
    print(f"节点0编码: {lap_pe[0].round(3)}")
    print(f"节点4编码（对节点0对称）: {lap_pe[4].round(3)}")
    
    # 测试2：随机游走位置编码
    print("\n--- 随机游走位置编码 ---")
    rw_pe = random_walk_positional_encoding(adj, walk_length=20, num_walks=5)
    
    print(f"随机游走PE形状: {rw_pe.shape}")
    print(f"节点0的邻居访问频率: {rw_pe[0, np.where(adj[0] > 0)[0]].round(3)}")
    
    # 测试3：注意力掩码效果
    print("\n--- 注意力掩码效果 ---")
    adj_mask = (adj > 0).astype(float) + np.eye(N)
    
    print("邻接掩码（节点0）:")
    print(f"  {adj_mask[0]}")
    print("节点0只能关注自己、相邻节点1和节点7")
    
    # 测试4：GraphTransformer层
    print("\n--- GraphTransformer层测试 ---")
    gt_layer = GraphTransformerLayer(node_dim=16, num_heads=4)
    
    output, attn = gt_layer.forward(node_features, adj, pos_encoding=lap_pe)
    
    print(f"输入形状: {node_features.shape}")
    print(f"输出形状: {output.shape}")
    print(f"注意力权重形状: {attn.shape}")
    
    # 查看注意力权重
    print(f"\n节点0的注意力权重（多头平均）:")
    avg_attn = np.mean(attn, axis=0)
    print(f"  {avg_attn[0].round(3)}")
    print(f"  节点0最关注: 节点{np.argmax(avg_attn[0])}")
    
    # 测试5：完整GraphTransformer
    print("\n--- 完整GraphTransformer测试 ---")
    gt = GraphTransformer(
        input_dim=16,
        hidden_dim=16,
        output_dim=8,
        num_heads=4,
        num_layers=2,
        pe_type='laplacian'
    )
    
    logits = gt.forward(node_features, adj)
    
    print(f"输入形状: {node_features.shape}")
    print(f"输出形状: {logits.shape}")
    
    # 测试6：位置编码的效果
    print("\n--- 位置编码的效果 ---")
    gt_no_pe = GraphTransformer(
        input_dim=16, hidden_dim=16, output_dim=8,
        num_heads=4, num_layers=2, pe_type=None
    )
    
    gt_with_pe = GraphTransformer(
        input_dim=16, hidden_dim=16, output_dim=8,
        num_heads=4, num_layers=2, pe_type='laplacian'
    )
    
    out_no_pe = gt_no_pe.forward(node_features, adj)
    out_with_pe = gt_with_pe.forward(node_features, adj)
    
    print(f"无PE输出范围: [{out_no_pe.min():.4f}, {out_no_pe.max():.4f}]")
    print(f"有PE输出范围: [{out_with_pe.min():.4f}, {out_with_pe.max():.4f}]")
    print(f"PE带来的变化: {np.linalg.norm(out_with_pe - out_no_pe):.4f}")
    
    # 测试7：多头注意力的差异
    print("\n--- 多头注意力分析 ---")
    gt_layer_multi = GraphTransformerLayer(node_dim=16, num_heads=4)
    _, attn_multi = gt_layer_multi.forward(node_features, adj)
    
    print(f"注意力权重形状: {attn_multi.shape}")
    
    for h in range(4):
        attn_head = attn_multi[h]
        print(f"  头{h}: 对角线注意力均值={np.diag(attn_head).mean():.4f}")
    
    print("\n图Transformer测试完成！")
