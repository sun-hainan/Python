# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / gnn_comparison



本文件实现 gnn_comparison 相关的算法功能。

"""



import numpy as np





# ============================

# 简化版GNN模型

# ============================



class SimpleGCN:

    """简化GCN"""

    def __init__(self, input_dim, output_dim):

        self.W = np.random.randn(input_dim, output_dim) * 0.01

    

    def forward(self, features, adj):

        # 归一化邻接矩阵

        adj = adj + np.eye(adj.shape[0])

        d = np.sum(adj, axis=1)

        d_inv = 1.0 / (d + 1e-8)

        d_inv_sqrt = np.power(d_inv, 0.5)

        d_mat = np.diag(d_inv_sqrt)

        adj_norm = d_mat @ adj @ d_mat

        

        # 图卷积

        return np.maximum(0, adj_norm @ features @ self.W)





class SimpleGAT:

    """简化GAT"""

    def __init__(self, input_dim, output_dim, num_heads=2):

        self.W = np.random.randn(input_dim, output_dim) * 0.01

        self.num_heads = num_heads

    

    def forward(self, features, adj):

        N = features.shape[0]

        

        # 计算注意力

        scores = features @ features.T / np.sqrt(features.shape[1])

        scores = np.where(adj > 0, scores, -1e9)

        att = np.exp(scores) / (np.sum(np.exp(scores), axis=1, keepdims=True) + 1e-8)

        

        # 加权聚合

        h = att @ features @ self.W

        return np.maximum(0, h)





class SimpleGraphSAGE:

    """简化GraphSAGE（Mean聚合）"""

    def __init__(self, input_dim, output_dim):

        self.W = np.random.randn(input_dim, output_dim) * 0.01

    

    def forward(self, features, adj):

        N = features.shape[0]

        

        # 邻居聚合

        neighbor_sum = adj @ features

        neighbor_count = np.sum(adj, axis=1, keepdims=True) + 1e-8

        neighbor_mean = neighbor_sum / neighbor_count

        

        # 拼接自身和邻居

        combined = np.concatenate([features, neighbor_mean], axis=1)

        

        return np.maximum(0, combined @ self.W[:combined.shape[1], :])





class SimpleGIN:

    """简化GIN"""

    def __init__(self, input_dim, output_dim):

        self.W1 = np.random.randn(input_dim, output_dim) * 0.01

        self.b1 = np.zeros(output_dim)

    

    def forward(self, features, adj):

        # 邻居求和 + 自身

        neighbor_sum = adj @ features

        combined = features + neighbor_sum

        

        # MLP

        h = combined @ self.W1 + self.b1

        return np.maximum(0, h)





class SimpleMPNN:

    """简化MPNN（消息传递神经网络）"""

    def __init__(self, input_dim, output_dim):

        self.W_msg = np.random.randn(input_dim, output_dim) * 0.01

        self.W_update = np.random.randn(output_dim * 2, output_dim) * 0.01

    

    def forward(self, features, adj):

        N = features.shape[0]

        

        # 消息传递：聚合邻居

        neighbor_agg = adj @ features

        

        # 更新

        combined = np.concatenate([features, neighbor_agg], axis=1)

        h = combined @ self.W_update

        

        return np.maximum(0, h)





# ============================

# 图统计计算

# ============================



def compute_graph_stats(adj):

    """计算图统计"""

    N = adj.shape[0]

    num_edges = int(np.sum(adj) / 2)

    avg_degree = np.mean(np.sum(adj, axis=1))

    density = num_edges / (N * (N - 1) / 2) if N > 1 else 0

    

    return {

        'nodes': N,

        'edges': num_edges,

        'avg_degree': avg_degree,

        'density': density

    }





def node_degree_distribution(adj):

    """计算度分布"""

    degrees = np.sum(adj, axis=1)

    return degrees





def clustering_coefficient(adj):

    """计算聚类系数"""

    N = adj.shape[0]

    coeffs = []

    

    for i in range(N):

        neighbors = np.where(adj[i] > 0)[0]

        k = len(neighbors)

        

        if k < 2:

            coeffs.append(0.0)

            continue

        

        # 计算邻居之间的边

        edges_between = 0

        for ni in neighbors:

            for nj in neighbors:

                if ni < nj and adj[ni, nj] > 0:

                    edges_between += 1

        

        max_edges = k * (k - 1) / 2

        coeffs.append(edges_between / max_edges if max_edges > 0 else 0)

    

    return np.mean(coeffs)





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 60)

    print("图神经网络综合对比测试")

    print("=" * 60)

    

    # 创建测试图

    N = 12

    node_dim = 8

    output_dim = 4

    

    # 创建随机图

    adj = np.zeros((N, N))

    for i in range(N):

        for j in range(i + 1, N):

            if np.random.random() < 0.3:

                adj[i, j] = adj[j, i] = 1

    

    # 确保连通

    for i in range(1, N):

        adj[i-1, i] = adj[i, i-1] = 1

    

    # 节点特征

    features = np.random.randn(N, node_dim)

    

    print(f"\n测试图: {N}节点, {int(np.sum(adj)/2)}边")

    stats = compute_graph_stats(adj)

    print(f"平均度: {stats['avg_degree']:.2f}, 密度: {stats['density']:.4f}")

    print(f"聚类系数: {clustering_coefficient(adj):.4f}")

    

    # 初始化模型

    models = {

        'GCN': SimpleGCN(node_dim, output_dim),

        'GAT': SimpleGAT(node_dim, output_dim, num_heads=2),

        'GraphSAGE': SimpleGraphSAGE(node_dim, output_dim),

        'GIN': SimpleGIN(node_dim, output_dim),

        'MPNN': SimpleMPNN(node_dim, output_dim),

    }

    

    # 测试各模型

    print("\n" + "-" * 60)

    print("各模型输出对比")

    print("-" * 60)

    

    for name, model in models.items():

        output = model.forward(features, adj)

        

        print(f"\n{name}:")

        print(f"  输出形状: {output.shape}")

        print(f"  输出均值: {output.mean():.4f}")

        print(f"  输出标准差: {output.std():.4f}")

        print(f"  输出范围: [{output.min():.4f}, {output.max():.4f}]")

    

    # 节点嵌入分析

    print("\n" + "-" * 60)

    print("节点嵌入分析")

    print("-" * 60)

    

    # 收集所有模型的嵌入

    embeddings = {}

    for name, model in models.items():

        embeddings[name] = model.forward(features, adj)

    

    # 计算节点间的相似度（各模型）

    print("\n节点0的嵌入（各模型）:")

    for name, emb in embeddings.items():

        print(f"  {name}: {emb[0].round(3)}")

    

    # 模型间嵌入相关性

    print("\n模型间嵌入相关性:")

    model_names = list(embeddings.keys())

    for i, name1 in enumerate(model_names):

        for j, name2 in enumerate(model_names):

            if i < j:

                emb1_flat = embeddings[name1].flatten()

                emb2_flat = embeddings[name2].flatten()

                corr = np.corrcoef(emb1_flat, emb2_flat)[0, 1]

                print(f"  {name1} vs {name2}: {corr:.4f}")

    

    # 节点分类模拟

    print("\n" + "-" * 60)

    print("节点分类模拟")

    print("-" * 60)

    

    # 模拟节点标签

    np.random.seed(42)

    labels = np.random.randint(0, 2, N)

    

    # 简单分类器：使用嵌入的点积

    print("\n模拟分类性能:")

    for name, emb in embeddings.items():

        # 简化评估：使用标签一致性

        # 假设嵌入相似度高的节点有相同标签

        correct = 0

        for i in range(N):

            for j in range(i + 1, N):

                sim = np.dot(emb[i], emb[j]) / (np.linalg.norm(emb[i]) * np.linalg.norm(emb[j]) + 1e-8)

                if (sim > 0 and labels[i] == labels[j]) or (sim < 0 and labels[i] != labels[j]):

                    correct += 1

        

        acc = correct / (N * (N - 1) / 2)

        print(f"  {name}: 模拟准确率 = {acc:.4f}")

    

    # 图级别任务模拟

    print("\n" + "-" * 60)

    print("图级别任务模拟")

    print("-" * 60)

    

    # 图级别嵌入 = 所有节点嵌入的均值

    print("\n图级别嵌入（各模型）:")

    for name, emb in embeddings.items():

        graph_emb = np.mean(emb, axis=0)

        print(f"  {name}: 均值范数 = {np.linalg.norm(graph_emb):.4f}")

    

    # 抗噪声能力测试

    print("\n" + "-" * 60)

    print("抗噪声能力测试")

    print("-" * 60)

    

    noise_levels = [0.0, 0.1, 0.5, 1.0, 2.0]

    

    print("\n添加噪声后的输出稳定性:")

    for name, model in models.items():

        original_output = model.forward(features, adj)

        stabilities = []

        

        for noise in noise_levels:

            noisy_features = features + np.random.randn(N, node_dim) * noise

            noisy_output = model.forward(noisy_features, adj)

            

            # 计算与原始输出的差异

            diff = np.linalg.norm(noisy_output - original_output) / (np.linalg.norm(original_output) + 1e-8)

            stabilities.append(diff)

        

        print(f"  {name}: {[f'{s:.3f}' for s in stabilities]}")

    

    # 层数对输出的影响

    print("\n" + "-" * 60)

    print("多层堆叠效果（简化模拟）")

    print("-" * 60)

    

    print("\n叠加2层后的输出变化:")

    for name, model in models.items():

        output1 = model.forward(features, adj)

        

        # 模拟第二层

        if hasattr(model, 'W'):

            output2 = np.maximum(0, adj @ output1 @ (model.W * 0.5))

        else:

            output2 = output1

        

        change = np.linalg.norm(output2 - output1) / (np.linalg.norm(output1) + 1e-8)

        print(f"  {name}: 变化率 = {change:.4f}")

    

    print("\n" + "=" * 60)

    print("图神经网络综合对比测试完成！")

    print("=" * 60)

