# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / graph_generation



本文件实现 graph_generation 相关的算法功能。

"""



import numpy as np





# ============================

# GraphRNN

# ============================



class GraphRNN:

    """

    GraphRNN：图递归生成模型

    

    核心思想：

    1. 使用RNN生成图的邻接矩阵

    2. 逐行/逐节点生成图的边

    

    参数:

        node_state_dim: 节点状态维度

        edge_state_dim: 边状态维度

        num_nodes: 最大节点数

    """

    

    def __init__(self, node_state_dim=32, edge_state_dim=32, num_nodes=20):

        self.node_state_dim = node_state_dim

        self.edge_state_dim = edge_state_dim

        self.num_nodes = num_nodes

        

        # 节点RNN：生成新节点时更新状态

        self.node_rnn_W = np.random.randn(node_state_dim, node_state_dim) * 0.1

        self.node_rnn_U = np.random.randn(node_state_dim, node_state_dim) * 0.1

        self.node_rnn_b = np.zeros(node_state_dim)

        

        # 边RNN：为当前节点生成与之前所有节点的边

        self.edge_rnn_W = np.random.randn(edge_state_dim, edge_state_dim) * 0.1

        self.edge_rnn_U = np.random.randn(edge_state_dim, node_state_dim) * 0.1

        self.edge_rnn_b = np.zeros(edge_state_dim)

        

        # 边预测MLP

        self.edge_mlp_W = np.random.randn(edge_state_dim, 1) * 0.1

        self.edge_mlp_b = np.zeros(1)

    

    def sigmoid(self, x):

        """Sigmoid函数"""

        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    

    def node_rnn_step(self, prev_state, node_embedding):

        """节点RNN单步"""

        h = np.tanh(prev_state @ self.node_rnn_W + node_embedding @ self.node_rnn_U + self.node_rnn_b)

        return h

    

    def edge_rnn_step(self, prev_edge_state, node_state):

        """边RNN单步"""

        h = np.tanh(prev_edge_state @ self.edge_rnn_W + node_state @ self.edge_rnn_U + self.edge_rnn_b)

        return h

    

    def predict_edge(self, edge_state):

        """预测边"""

        logit = edge_state @ self.edge_mlp_W + self.edge_mlp_b

        prob = self.sigmoid(logit)

        return prob[0, 0]

    

    def generate(self, max_nodes=None):

        """

        生成图

        

        参数:

            max_nodes: 最大节点数

        返回:

            adj: 生成的邻接矩阵

        """

        if max_nodes is None:

            max_nodes = self.num_nodes

        

        N = max_nodes

        adj = np.zeros((N, N))

        node_states = []

        

        # 初始节点状态

        h_node = np.zeros(self.node_state_dim)

        node_embedding = np.random.randn(self.node_state_dim) * 0.1

        

        # 生成每个节点

        for i in range(N):

            # 决定是否添加节点（简化：总是添加）

            h_node = self.node_rnn_step(h_node, node_embedding)

            node_states.append(h_node)

            

            # 为当前节点生成与之前所有节点的边

            h_edge = np.zeros(self.edge_state_dim)

            

            for j in range(i):

                h_edge = self.edge_rnn_step(h_edge, node_states[j])

                edge_prob = self.predict_edge(h_edge)

                

                # 根据概率决定是否有边

                if np.random.random() < edge_prob:

                    adj[i, j] = adj[j, i] = 1

            

            # 更新节点嵌入

            node_embedding = h_node + np.random.randn(self.node_state_dim) * 0.1

        

        return adj





# ============================

# VAE图生成

# ============================



class GraphVAE:

    """

    图变分自编码器

    

    编码器：图 -> 潜在向量

    解码器：潜在向量 -> 邻接矩阵

    

    参数:

        node_dim: 节点特征维度

        latent_dim: 潜在空间维度

    """

    

    def __init__(self, node_dim=8, hidden_dim=32, latent_dim=16, num_nodes=10):

        self.node_dim = node_dim

        self.hidden_dim = hidden_dim

        self.latent_dim = latent_dim

        self.num_nodes = num_nodes

        

        # 编码器

        self.encoder_W = np.random.randn(node_dim * num_nodes, hidden_dim) * np.sqrt(2.0 / (node_dim * num_nodes))

        self.encoder_b = np.zeros(hidden_dim)

        

        # 潜在变量均值和方差

        self.mu_W = np.random.randn(hidden_dim, latent_dim) * 0.1

        self.mu_b = np.zeros(latent_dim)

        self.logvar_W = np.random.randn(hidden_dim, latent_dim) * 0.1

        self.logvar_b = np.zeros(latent_dim)

        

        # 解码器

        self.decoder_W = np.random.randn(latent_dim, num_nodes * num_nodes) * 0.1

        self.decoder_b = np.zeros(num_nodes * num_nodes)

    

    def encode(self, node_features):

        """

        编码图到潜在空间

        

        参数:

            node_features: 节点特征 (num_nodes, node_dim)

        返回:

            mu: 均值

            logvar: 对数方差

        """

        # 展平节点特征

        x = node_features.flatten()

        

        # 编码

        h = np.maximum(0, x @ self.encoder_W + self.encoder_b)

        

        # 均值和方差

        mu = h @ self.mu_W + self.mu_b

        logvar = h @ self.logvar_W + self.logvar_b

        

        return mu, logvar

    

    def reparameterize(self, mu, logvar):

        """

        重参数化技巧

        

        参数:

            mu: 均值

            logvar: 对数方差

        返回:

            z: 采样潜在向量

        """

        std = np.exp(0.5 * logvar)

        eps = np.random.randn(*mu.shape)

        z = mu + std * eps

        return z

    

    def decode(self, z):

        """

        从潜在向量解码邻接矩阵

        

        参数:

            z: 潜在向量

        返回:

            adj: 预测的邻接矩阵

        """

        # 解码

        logits = z @ self.decoder_W + self.decoder_b

        

        # 重塑为邻接矩阵

        adj_flat = 1 / (1 + np.exp(-logits))  # Sigmoid

        adj = adj_flat.reshape(self.num_nodes, self.num_nodes)

        

        # 对称化（无向图）

        adj = (adj + adj.T) / 2

        

        return adj

    

    def forward(self, node_features):

        """

        前馈传播

        

        参数:

            node_features: 节点特征

        返回:

            adj_recon: 重构的邻接矩阵

            mu: 潜在均值

            logvar: 潜在对数方差

        """

        mu, logvar = self.encode(node_features)

        z = self.reparameterize(mu, logvar)

        adj_recon = self.decode(z)

        

        return adj_recon, mu, logvar

    

    def generate(self, node_features):

        """生成图（简化版）"""

        mu, logvar = self.encode(node_features)

        z = self.reparameterize(mu, logvar)

        return self.decode(z)





def graph_statistics(adj):

    """

    计算图的统计信息

    

    参数:

        adj: 邻接矩阵

    返回:

        stats: 统计信息字典

    """

    N = adj.shape[0]

    

    # 节点数

    num_nodes = N

    

    # 边数

    num_edges = int(np.sum(adj) / 2)

    

    # 平均度

    degrees = np.sum(adj, axis=1)

    avg_degree = np.mean(degrees)

    

    # 度分布标准差

    degree_std = np.std(degrees)

    

    # 密度

    density = num_edges / (N * (N - 1) / 2) if N > 1 else 0

    

    # 连通分量数（简化：使用BFS）

    visited = set()

    num_components = 0

    

    for start in range(N):

        if start not in visited:

            num_components += 1

            queue = [start]

            while queue:

                node = queue.pop(0)

                if node not in visited:

                    visited.add(node)

                    for neighbor in np.where(adj[node] > 0)[0]:

                        if neighbor not in visited:

                            queue.append(neighbor)

    

    return {

        'num_nodes': num_nodes,

        'num_edges': num_edges,

        'avg_degree': avg_degree,

        'degree_std': degree_std,

        'density': density,

        'num_components': num_components

    }





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 55)

    print("图生成模型测试")

    print("=" * 55)

    

    # 测试1：GraphRNN生成

    print("\n--- GraphRNN生成测试 ---")

    graphrnn = GraphRNN(node_state_dim=32, edge_state_dim=32, num_nodes=10)

    

    generated_adj = graphrnn.generate(max_nodes=10)

    

    print(f"生成的邻接矩阵形状: {generated_adj.shape}")

    print(f"生成边数: {int(np.sum(generated_adj) / 2)}")

    print(f"图密度: {np.sum(generated_adj) / (10 * 9):.4f}")

    

    stats = graph_statistics(generated_adj)

    print(f"\n生成图统计:")

    for k, v in stats.items():

        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

    

    # 测试2：生成多个图

    print("\n--- 批量图生成 ---")

    num_graphs = 5

    graphs = []

    

    for i in range(num_graphs):

        adj = graphrnn.generate(max_nodes=8)

        graphs.append(adj)

    

    # 统计生成图的边数分布

    edge_counts = [int(np.sum(g) / 2) for g in graphs]

    print(f"生成{num_graphs}个图的边数: {edge_counts}")

    print(f"平均边数: {np.mean(edge_counts):.2f}")

    print(f"边数标准差: {np.std(edge_counts):.2f}")

    

    # 测试3：GraphVAE

    print("\n--- GraphVAE测试 ---")

    graphvae = GraphVAE(node_dim=8, hidden_dim=16, latent_dim=8, num_nodes=8)

    

    # 创建节点特征

    node_features = np.random.randn(8, 8)

    

    # 前馈

    adj_recon, mu, logvar = graphvae.forward(node_features)

    

    print(f"输入特征形状: {node_features.shape}")

    print(f"潜在均值形状: {mu.shape}")

    print(f"重构邻接矩阵形状: {adj_recon.shape}")

    print(f"重构邻接矩阵范围: [{adj_recon.min():.4f}, {adj_recon.max():.4f}]")

    

    # 测试4：VAE生成新图

    print("\n--- VAE生成新图 ---")

    np.random.seed(123)  # 不同的随机种子

    new_node_features = np.random.randn(8, 8)

    generated_adj_vae = graphvae.generate(new_node_features)

    

    print(f"VAE生成图统计:")

    gen_stats = graph_statistics(generated_adj_vae > 0.3)  # 阈值化

    for k, v in gen_stats.items():

        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

    

    # 测试5：比较生成图和真实图

    print("\n--- 生成图质量评估 ---")

    

    # 创建一些真实图的统计

    real_graphs = []

    for _ in range(5):

        # Erdős-Rényi随机图

        n = 10

        p = 0.3

        adj = np.random.binomial(1, p, (n, n)).astype(float)

        adj = (adj + adj.T) / 2

        np.fill_diagonal(adj, 0)

        real_graphs.append(adj)

    

    # 真实图统计

    real_stats = [graph_statistics(g) for g in real_graphs]

    real_avg_degree = np.mean([s['avg_degree'] for s in real_stats])

    real_density = np.mean([s['density'] for s in real_stats])

    

    # 生成图统计

    gen_graphs = [graphrnn.generate(max_nodes=10) for _ in range(5)]

    gen_stats_list = [graph_statistics(g) for g in gen_graphs]

    gen_avg_degree = np.mean([s['avg_degree'] for s in gen_stats_list])

    gen_density = np.mean([s['density'] for s in gen_stats_list])

    

    print(f"真实图平均度: {real_avg_degree:.2f}")

    print(f"生成图平均度: {gen_avg_degree:.2f}")

    print(f"真实图密度: {real_density:.4f}")

    print(f"生成图密度: {gen_density:.4f}")

    

    # 测试6：潜在空间插值

    print("\n--- 潜在空间插值 ---")

    graphvae2 = GraphVAE(node_dim=4, hidden_dim=16, latent_dim=4, num_nodes=5)

    

    # 两个不同的输入

    features1 = np.random.randn(5, 4)

    features2 = np.random.randn(5, 4)

    

    mu1, _ = graphvae2.encode(features1)

    mu2, _ = graphvae2.encode(features2)

    

    # 线性插值

    alphas = [0.0, 0.25, 0.5, 0.75, 1.0]

    print("潜在空间插值:")

    for alpha in alphas:

        z_interp = (1 - alpha) * mu1 + alpha * mu2

        adj_interp = graphvae2.decode(z_interp)

        edge_count = np.sum(adj_interp > 0.3) // 2

        print(f"  alpha={alpha:.2f}: 边数估计={edge_count:.1f}")

    

    # 测试7：GraphRNN边生成顺序分析

    print("\n--- 边生成顺序分析 ---")

    np.random.seed(42)

    adj = graphrnn.generate(max_nodes=6)

    

    print("生成的邻接矩阵:")

    print(adj.astype(int))

    

    # 分析每行生成边的情况

    print("\n每行边分布:")

    for i in range(6):

        row_edges = np.sum(adj[i, :i+1])

        print(f"  节点{i}: {int(row_edges)}条边（与前{i}个节点）")

    

    print("\n图生成模型测试完成！")

