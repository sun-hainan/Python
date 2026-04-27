# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / gat_variants



本文件实现 gat_variants 相关的算法功能。

"""



import numpy as np





def leaky_relu(x, alpha=0.2):

    """Leaky ReLU"""

    return np.where(x > 0, x, alpha * x)





def elu(x):

    """ELU激活"""

    return np.where(x > 0, x, np.exp(x) - 1)





def softmax_by_row(x, axis=1):

    """行级Softmax"""

    x_shifted = x - np.max(x, axis=axis, keepdims=True)

    exp_x = np.exp(x_shifted)

    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)





class GATv2Attention:

    """

    GATv2：改进的注意力机制

    

    核心改进：

    - 使用MLP计算注意力，而不是简单的点积

    - 使用ELU激活而非LeakyReLU

    - 注意力计算更灵活

    """

    

    def __init__(self, node_dim, head_dim):

        self.node_dim = node_dim

        self.head_dim = head_dim

        

        # 注意力MLP

        self.W_a = np.random.randn(2 * head_dim, 1) * 0.01

        self.b_a = np.zeros(1)

        

        # 特征变换

        self.W = np.random.randn(node_dim, head_dim) * np.sqrt(2.0 / node_dim)

    

    def forward(self, node_features, adj=None):

        """

        前馈传播

        

        参数:

            node_features: (N, node_dim)

            adj: 邻接矩阵 (N, N)

        返回:

            output: (N, head_dim)

            attention: (N, N) 注意力权重

        """

        N = node_features.shape[0]

        

        # 特征变换

        h = node_features @ self.W  # (N, head_dim)

        

        # 计算注意力系数

        # GATv2: a = MLP([h_i || h_j])

        h_i = h.unsqueeze(1).repeat(1, N, 1)  # (N, N, head_dim)

        h_j = h.unsqueeze(0).repeat(N, 1, 1)  # (N, N, head_dim)

        

        # 拼接

        h_concat = np.concatenate([h_i, h_j], axis=2)  # (N, N, 2*head_dim)

        

        # MLP注意力（使用ELU激活）

        e = elu(h_concat @ self.W_a + self.b_a).squeeze(-1)  # (N, N)

        

        # 掩码

        if adj is not None:

            e = np.where(adj > 0, e, -1e9)

        

        # Softmax

        attention = softmax_by_row(e)  # (N, N)

        

        # 聚合

        output = attention @ h  # (N, head_dim)

        

        return output, attention





class MultiHeadGAT:

    """

    多头GAT

    

    参数:

        node_dim: 输入维度

        num_heads: 头数

        head_dim: 每头维度

    """

    

    def __init__(self, node_dim, num_heads=4, head_dim=16):

        self.node_dim = node_dim

        self.num_heads = num_heads

        self.head_dim = head_dim

        

        # 多头注意力

        self.heads = []

        for _ in range(num_heads):

            self.heads.append(GATv2Attention(node_dim, head_dim))

        

        # 输出权重

        self.W_o = np.random.randn(num_heads * head_dim, num_heads * head_dim) * 0.01

    

    def forward(self, node_features, adj=None):

        """多头前馈"""

        all_outputs = []

        all_attentions = []

        

        for head in self.heads:

            out, att = head.forward(node_features, adj)

            all_outputs.append(out)

            all_attentions.append(att)

        

        # 拼接所有头

        output = np.concatenate(all_outputs, axis=1)

        

        return output, all_attentions





class HighOrderGAT:

    """

    高阶图注意力

    

    考虑k跳邻居的信息

    """

    

    def __init__(self, node_dim, hidden_dim, order=2):

        self.node_dim = node_dim

        self.hidden_dim = hidden_dim

        self.order = order

        

        # 每阶的注意力

        self.attention_per_order = []

        

        for k in range(order):

            self.attention_per_order.append(

                GATv2Attention(node_dim if k == 0 else hidden_dim, hidden_dim)

            )

        

        # 聚合权重

        self.agg_weights = np.random.randn(order) * 0.01

        self.agg_weights = np.exp(self.agg_weights) / np.sum(np.exp(self.agg_weights))

    

    def get_k_hop_neighbors(self, adj, node, k):

        """获取k跳邻居"""

        neighbors = set()

        current = {node}

        

        for _ in range(k):

            next_neighbors = set()

            for n in current:

                for neighbor in np.where(adj[n] > 0)[0]:

                    if neighbor != node:

                        next_neighbors.add(neighbor)

            neighbors.update(next_neighbors)

            current = next_neighbors

        

        return list(neighbors)

    

    def forward(self, node_features, adj):

        """前馈传播"""

        N = node_features.shape[0]

        outputs_per_order = []

        

        for k in range(self.order):

            # 为每个节点聚合k跳邻居的信息

            h_order = np.zeros((N, self.hidden_dim))

            

            for i in range(N):

                k_hop_neighbors = self.get_k_hop_neighbors(adj, i, k + 1)

                

                if len(k_hop_neighbors) > 0:

                    # 聚合邻居特征

                    neighbor_feats = node_features[k_hop_neighbors]

                    h_order[i] = np.mean(neighbor_feats, axis=0)

            

            # 应用注意力

            h_attended, _ = self.attention_per_order[k].forward(h_order, adj)

            outputs_per_order.append(h_attended)

        

        # 加权聚合

        output = np.zeros((N, self.hidden_dim))

        for k, h_k in enumerate(outputs_per_order):

            output += self.agg_weights[k] * h_k

        

        return output





class SpectralGAT:

    """

    频谱图注意力

    

    在频谱域（拉普拉斯特征向量）上计算注意力

    """

    

    def __init__(self, node_dim, hidden_dim, num_eigenvectors=8):

        self.node_dim = node_dim

        self.hidden_dim = hidden_dim

        self.num_eigenvectors = num_eigenvectors

        

        # 特征变换

        self.W = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)

        

        # 频谱注意力权重

        self.W_freq = np.random.randn(num_eigenvectors, 1) * 0.01

        

        # 空域注意力

        self.W_space = np.random.randn(hidden_dim * 2, hidden_dim) * 0.01

    

    def compute_laplacian_eigenvectors(self, adj):

        """计算拉普拉斯特征向量"""

        N = adj.shape[0]

        

        # 添加自环

        adj = adj + np.eye(N)

        

        # 度矩阵

        d = np.sum(adj, axis=1)

        d_inv_sqrt = np.power(d, -0.5)

        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0

        d_mat = np.diag(d_inv_sqrt)

        

        # 归一化拉普拉斯

        L = np.eye(N) - d_mat @ adj @ d_mat

        

        # 特征分解

        eigenvalues, eigenvectors = np.linalg.eigh(L)

        

        # 取最小的k个特征向量

        eigenvectors = eigenvectors[:, :self.num_eigenvectors]

        

        return eigenvectors

    

    def forward(self, node_features, adj):

        """前馈传播"""

        N = node_features.shape[0]

        

        # 频谱嵌入

        eigenvectors = self.compute_laplacian_eigenvectors(adj)

        

        # 频谱注意力

        freq_attention = eigenvectors @ self.W_freq  # (N, 1)

        freq_attention = np.exp(freq_attention) / np.sum(np.exp(freq_attention))

        

        # 空域特征变换

        h = node_features @ self.W  # (N, hidden_dim)

        

        # 计算空域注意力

        h_i = h.unsqueeze(1).repeat(1, N, 1)

        h_j = h.unsqueeze(0).repeat(N, 1, 1)

        h_concat = np.concatenate([h_i, h_j], axis=2)

        

        space_attention = np.tanh(h_concat @ self.W_space).squeeze(-1)  # (N, N)

        space_attention = softmax_by_row(space_attention)

        

        # 结合频谱和空域注意力

        combined_attention = space_attention * freq_attention * freq_attention.T

        combined_attention = softmax_by_row(combined_attention)

        

        # 聚合

        output = combined_attention @ h

        

        return output, combined_attention





class GraphormerAttention:

    """

    Graphormer风格注意力

    

    使用图特定的位置编码和注意力偏置

    """

    

    def __init__(self, node_dim, hidden_dim):

        self.node_dim = node_dim

        self.hidden_dim = hidden_dim

        

        # 特征投影

        self.W_V = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)

        self.W_Q = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)

        self.W_K = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)

        

        # 度编码

        self.degree_embedding = np.random.randn(100, hidden_dim) * 0.01

        

        # 注意力偏置

        self.edge_bias = np.random.randn(hidden_dim) * 0.01

    

    def forward(self, node_features, adj):

        """前馈传播"""

        N = node_features.shape[0]

        

        # QKV

        Q = node_features @ self.W_Q

        K = node_features @ self.W_K

        V = node_features @ self.W_V

        

        # 注意力分数

        attention = Q @ K.T / np.sqrt(self.hidden_dim)  # (N, N)

        

        # 度偏置

        degrees = np.sum(adj > 0, axis=1).astype(int)

        degrees = np.clip(degrees, 0, 99)

        degree_bias = self.degree_embedding[degrees] @ self.degree_embedding[degrees].T / self.hidden_dim

        

        attention = attention + degree_bias

        

        # 边信息偏置

        edge_bias = np.zeros((N, N))

        for i in range(N):

            for j in range(N):

                if adj[i, j] > 0:

                    edge_bias[i, j] = np.sum(self.edge_bias)

        

        attention = attention + edge_bias

        

        # Softmax

        attention = softmax_by_row(attention)

        

        # 聚合

        output = attention @ V

        

        return output, attention





if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 55)

    print("图注意力变体测试")

    print("=" * 55)

    

    # 创建测试图

    N = 8

    adj = np.zeros((N, N))

    

    for i in range(N):

        for j in range(i + 1, N):

            if np.random.random() < 0.3:

                adj[i, j] = adj[j, i] = 1

    

    node_features = np.random.randn(N, 16)

    

    print(f"节点数: {N}")

    print(f"边数: {int(np.sum(adj) / 2)}")

    

    # 测试GATv2

    print("\n--- GATv2注意力 ---")

    gatv2 = GATv2Attention(node_dim=16, head_dim=8)

    output, attn = gatv2.forward(node_features, adj)

    

    print(f"输出形状: {output.shape}")

    print(f"注意力形状: {attn.shape}")

    

    # 多头注意力

    print("\n--- 多头GAT ---")

    multi_gat = MultiHeadGAT(node_dim=16, num_heads=4, head_dim=8)

    output_multi, attentions = multi_gat.forward(node_features, adj)

    

    print(f"多头输出形状: {output_multi.shape}")

    print(f"注意力头数: {len(attentions)}")

    

    # 高阶GAT

    print("\n--- 高阶GAT ---")

    high_order_gat = HighOrderGAT(node_dim=16, hidden_dim=8, order=3)

    output_high = high_order_gat.forward(node_features, adj)

    

    print(f"高阶GAT输出形状: {output_high.shape}")

    

    # 频谱GAT

    print("\n--- 频谱GAT ---")

    spectral_gat = SpectralGAT(node_dim=16, hidden_dim=8, num_eigenvectors=4)

    output_spec, attn_spec = spectral_gat.forward(node_features, adj)

    

    print(f"频谱GAT输出形状: {output_spec.shape}")

    

    # Graphormer风格注意力

    print("\n--- Graphormer风格注意力 ---")

    graphormer = GraphormerAttention(node_dim=16, hidden_dim=8)

    output_graph, attn_graph = graphormer.forward(node_features, adj)

    

    print(f"Graphormer输出形状: {output_graph.shape}")

    print(f"注意力形状: {attn_graph.shape}")

    

    # 各变体对比

    print("\n--- 各变体对比 ---")

    print(f"{'变体':>20} | {'输出范数':>12} | {'注意力稀疏度':>15}")

    print("-" * 52)

    

    variants = {

        'GATv2': output,

        'MultiHead GAT': output_multi,

        'High-Order GAT': output_high,

        'Spectral GAT': output_spec,

        'Graphormer': output_graph,

    }

    

    for name, out in variants.items():

        out_norm = np.linalg.norm(out)

        att = attn if name == 'GATv2' else (attentions[0] if name == 'MultiHead GAT' else None)

        sparsity = 1 - np.sum(att > 0.1) / (N * N) if att is not None else 0

        

        print(f"{name:>20} | {out_norm:12.4f} | {sparsity:15.2%}")

    

    # 注意力可视化

    print("\n--- 注意力权重可视化 ---")

    print("GATv2注意力矩阵（节点0）:")

    print(f"  {attn[0].round(3)}")

    print(f"  节点0最关注: {np.argmax(attn[0])}")

    

    # 不同阶的注意力差异

    print("\n--- 高阶注意力差异 ---")

    for k in range(3):

        neighbors = high_order_gat.get_k_hop_neighbors(adj, 0, k + 1)

        print(f"  {k+1}跳邻居: {neighbors}")

    

    print("\n图注意力变体测试完成！")

