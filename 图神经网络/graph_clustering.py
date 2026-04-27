# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / graph_clustering



本文件实现 graph_clustering 相关的算法功能。

"""



import numpy as np

import random





def build_adj_list(adj):

    """构建邻接表"""

    N = adj.shape[0]

    adj_list = {i: [] for i in range(N)}

    for i in range(N):

        for j in range(N):

            if adj[i, j] > 0 and i != j:

                adj_list[i].append(j)

    return adj_list





def spectral_clustering(adj, num_clusters, normalized=True):

    """

    谱聚类算法

    

    参数:

        adj: 邻接矩阵 (N, N)

        num_clusters: 聚类数

        normalized: 是否使用归一化拉普拉斯矩阵

    返回:

        labels: 每个节点的聚类标签 (N,)

    """

    N = adj.shape[0]

    

    # 构建度矩阵

    degrees = np.sum(adj, axis=1)

    D = np.diag(degrees)

    

    # 拉普拉斯矩阵

    if normalized:

        # 归一化拉普拉斯矩阵: L_norm = I - D^(-1/2) * A * D^(-1/2)

        D_inv_sqrt = np.diag(1.0 / np.sqrt(degrees + 1e-8))

        L = np.eye(N) - D_inv_sqrt @ adj @ D_inv_sqrt

    else:

        # 非归一化拉普拉斯矩阵: L = D - A

        L = D - adj

    

    # 特征分解

    eigenvalues, eigenvectors = np.linalg.eigh(L)

    

    # 取最小的k个特征向量（跳过第一个，因为特征值为0）

    k = min(num_clusters, N)

    embedding = eigenvectors[:, 1:k+1]

    

    # K-means聚类（简化版）

    labels = simple_kmeans(embedding, num_clusters)

    

    return labels





def simple_kmeans(X, k, max_iter=100):

    """

    简化版K-means

    

    参数:

        X: 数据 (N, d)

        k: 聚类数

        max_iter: 最大迭代次数

    返回:

        labels: 聚类标签 (N,)

    """

    N = X.shape[0]

    

    # 随机初始化中心

    indices = np.random.choice(N, k, replace=False)

    centers = X[indices].copy()

    

    labels = np.zeros(N, dtype=int)

    

    for _ in range(max_iter):

        # 分配样本到最近的中心

        distances = np.zeros((N, k))

        for i in range(k):

            distances[:, i] = np.sum((X - centers[i]) ** 2, axis=1)

        

        new_labels = np.argmin(distances, axis=1)

        

        # 检查收敛

        if np.array_equal(labels, new_labels):

            break

        

        labels = new_labels

        

        # 更新中心

        for i in range(k):

            if np.sum(labels == i) > 0:

                centers[i] = np.mean(X[labels == i], axis=0)

    

    return labels





# ============================

# DeepWalk

# ============================



class DeepWalk:

    """

    DeepWalk：基于随机游走的节点嵌入

    

    核心思想：

    1. 从每个节点出发进行短随机游走

    2. 用Skip-gram学习节点嵌入

    

    参数:

        embedding_dim: 嵌入维度

        walk_length: 游走长度

        num_walks: 每个节点的游走次数

        window_size: Skip-gram窗口大小

    """

    

    def __init__(self, embedding_dim=64, walk_length=10, num_walks=10, window_size=5):

        self.embedding_dim = embedding_dim

        self.walk_length = walk_length

        self.num_walks = num_walks

        self.window_size = window_size

        

        self.embeddings = None

    

    def random_walk(self, start_node, adj_list):

        """

        从起始节点开始的随机游走

        

        参数:

            start_node: 起始节点

            adj_list: 邻接表

        返回:

            walk: 游走路径

        """

        walk = [start_node]

        current = start_node

        

        for _ in range(self.walk_length - 1):

            neighbors = adj_list.get(current, [])

            if len(neighbors) == 0:

                break

            current = random.choice(neighbors)

            walk.append(current)

        

        return walk

    

    def generate_walks(self, adj):

        """

        生成所有随机游走序列

        

        参数:

            adj: 邻接矩阵

        返回:

            walks: 所有游走序列列表

        """

        adj_list = build_adj_list(adj)

        walks = []

        nodes = list(adj_list.keys())

        

        for _ in range(self.num_walks):

            random.shuffle(nodes)

            for node in nodes:

                walk = self.random_walk(node, adj_list)

                walks.append(walk)

        

        return walks

    

    def skip_gram_train(self, walks, vocab_size):

        """

        Skip-gram训练（简化版）

        

        参数:

            walks: 游走序列列表

            vocab_size: 词汇表大小（节点数）

        返回:

            embeddings: 学习到的嵌入

        """

        # 初始化嵌入

        embeddings = np.random.randn(vocab_size, self.embedding_dim) * 0.1

        context_embeddings = np.random.randn(vocab_size, self.embedding_dim) * 0.1

        

        # 简化的训练过程

        learning_rate = 0.025

        num_epochs = 5

        

        for epoch in range(num_epochs):

            for walk in walks:

                for i, center_node in enumerate(walk):

                    # 窗口内的节点作为上下文

                    start = max(0, i - self.window_size)

                    end = min(len(walk), i + self.window_size + 1)

                    

                    for j in range(start, end):

                        if i == j:

                            continue

                        

                        context_node = walk[j]

                        

                        # 简化梯度更新

                        center_emb = embeddings[center_node]

                        context_emb = context_embeddings[context_node]

                        

                        # 计算得分

                        score = np.dot(center_emb, context_emb)

                        

                        # 简化的更新

                        grad = score - 1.0

                        embeddings[center_node] -= learning_rate * grad * context_emb

                        context_embeddings[context_node] -= learning_rate * grad * center_emb

        

        self.embeddings = embeddings

        return embeddings

    

    def fit(self, adj):

        """

        训练DeepWalk

        

        参数:

            adj: 邻接矩阵 (N, N)

        返回:

            embeddings: 节点嵌入 (N, embedding_dim)

        """

        N = adj.shape[0]

        

        # 生成游走

        walks = self.generate_walks(adj)

        

        # 训练Skip-gram

        embeddings = self.skip_gram_train(walks, N)

        

        return embeddings





# ============================

# Node2Vec

# ============================



class Node2Vec:

    """

    Node2Vec：结合BFS和DFS的节点嵌入

    

    与DeepWalk的区别：

    - 引入返回概率(p)和前进概率(q)

    - p控制BFS倾向（结构等价）

    - q控制DFS倾向（社区同质性）

    

    参数:

        embedding_dim: 嵌入维度

        walk_length: 游走长度

        num_walks: 每个节点的游走次数

        p: 返回概率

        q: 前进概率

    """

    

    def __init__(self, embedding_dim=64, walk_length=10, num_walks=10, p=1.0, q=1.0):

        self.embedding_dim = embedding_dim

        self.walk_length = walk_length

        self.num_walks = num_walks

        self.p = p

        self.q = q

        

        self.embeddings = None

    

    def get_alias_tables(self, adj):

        """

        预计算用于采样节点的概率分布

        

        参数:

            adj: 邻接矩阵

        返回:

            alias_nodes: 节点采样的别名表

            alias_edges: 边采样的别名表

        """

        N = adj.shape[0]

        adj_list = build_adj_list(adj)

        

        # 计算每个节点的出度分布

        alias_nodes = {}

        for node in range(N):

            neighbors = adj_list.get(node, [])

            if len(neighbors) == 0:

                alias_nodes[node] = (np.array([0]), np.array([1.0]))

                continue

            

            probs = np.ones(len(neighbors)) / len(neighbors)

            alias_nodes[node] = self._create_alias_table(probs)

        

        return alias_nodes, None

    

    def _create_alias_table(self, probs):

        """创建别名表"""

        # 简化实现：直接返回概率

        return probs

    

    def biased_random_walk(self, start_node, adj_list, alias_tables):

        """

        有偏随机游走

        

        参数:

            start_node: 起始节点

            adj_list: 邻接表

            alias_tables: 别名表

        返回:

            walk: 游走路径

        """

        walk = [start_node]

        current = start_node

        prev = None

        

        for _ in range(self.walk_length - 1):

            neighbors = adj_list.get(current, [])

            if len(neighbors) == 0:

                break

            

            # 计算采样概率

            if prev is None:

                # 第一个跳转：均匀采样

                probs = np.ones(len(neighbors)) / len(neighbors)

            else:

                # 计算转移概率

                unnormalized_probs = []

                for neighbor in neighbors:

                    if neighbor == prev:

                        # 返回上一个节点

                        unnormalized_probs.append(1.0 / self.p)

                    elif adj_list.get(neighbor, []).__contains__(prev):

                        # 与上一个节点相连

                        unnormalized_probs.append(1.0)

                    else:

                        # 其他节点

                        unnormalized_probs.append(1.0 / self.q)

                

                probs = np.array(unnormalized_probs)

                probs = probs / probs.sum()

            

            # 采样下一个节点

            next_node = np.random.choice(neighbors, p=probs)

            walk.append(next_node)

            prev = current

            current = next_node

        

        return walk

    

    def generate_walks(self, adj):

        """生成所有有偏游走"""

        adj_list = build_adj_list(adj)

        alias_tables = self.get_alias_tables(adj)[0]

        

        walks = []

        nodes = list(adj_list.keys())

        

        for _ in range(self.num_walks):

            random.shuffle(nodes)

            for node in nodes:

                walk = self.biased_random_walk(node, adj_list, alias_tables)

                walks.append(walk)

        

        return walks

    

    def fit(self, adj):

        """

        训练Node2Vec

        

        参数:

            adj: 邻接矩阵

        返回:

            embeddings: 节点嵌入

        """

        N = adj.shape[0]

        

        # 生成游走

        walks = self.generate_walks(adj)

        

        # 训练（复用DeepWalk的Skip-gram）

        deepwalk = DeepWalk(

            embedding_dim=self.embedding_dim,

            walk_length=self.walk_length,

            num_walks=1,  # 已经在generate_walks中处理

            window_size=5

        )

        

        # 简化的Skip-gram训练

        embeddings = np.random.randn(N, self.embedding_dim) * 0.1

        

        for walk in walks:

            for i, center in enumerate(walk):

                for j in range(max(0, i-2), min(len(walk), i+3)):

                    if i != j:

                        context = walk[j]

                        # 简化的更新

                        embeddings[center] += 0.01 * (embeddings[context] - embeddings[center])

        

        self.embeddings = embeddings

        return embeddings





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    random.seed(42)

    

    print("=" * 55)

    print("图聚类算法测试")

    print("=" * 55)

    

    # 创建测试图（两个社区）

    N = 20

    adj = np.zeros((N, N))

    

    # 社区1: 节点0-9

    for i in range(10):

        for j in range(i+1, 10):

            if np.random.random() < 0.5:

                adj[i, j] = adj[j, i] = 1

    

    # 社区2: 节点10-19

    for i in range(10, 20):

        for j in range(i+1, 20):

            if np.random.random() < 0.5:

                adj[i, j] = adj[j, i] = 1

    

    # 两个社区之间的连接

    for i in range(10):

        for j in range(10, 20):

            if np.random.random() < 0.05:

                adj[i, j] = adj[j, i] = 1

    

    print(f"节点数: {N}")

    print(f"边数: {int(np.sum(adj) / 2)}")

    

    # 测试1：谱聚类

    print("\n--- 谱聚类测试 ---")

    labels = spectral_clustering(adj, num_clusters=2)

    

    print("聚类结果:")

    print(f"  社区1 (节点0-9): {list(labels[:10])}")

    print(f"  社区2 (节点10-19): {list(labels[10:])}")

    

    # 计算聚类纯度

    cluster0_labels = labels[:10]

    cluster1_labels = labels[10:]

    purity0 = max(np.sum(cluster0_labels == 0), np.sum(cluster0_labels == 1)) / 10

    purity1 = max(np.sum(cluster1_labels == 0), np.sum(cluster1_labels == 1)) / 10

    print(f"  聚类纯度: {(purity0 + purity1) / 2:.2%}")

    

    # 测试2：DeepWalk

    print("\n--- DeepWalk测试 ---")

    deepwalk = DeepWalk(embedding_dim=8, walk_length=8, num_walks=5)

    dw_embeddings = deepwalk.fit(adj)

    

    print(f"DeepWalk嵌入形状: {dw_embeddings.shape}")

    

    # 嵌入相似度分析

    print("\n同社区节点对的嵌入相似度:")

    same_community_sims = []

    diff_community_sims = []

    

    for i in range(N):

        for j in range(i+1, N):

            sim = np.dot(dw_embeddings[i], dw_embeddings[j]) / (

                np.linalg.norm(dw_embeddings[i]) * np.linalg.norm(dw_embeddings[j]) + 1e-8

            )

            

            if (i < 10 and j < 10) or (i >= 10 and j >= 10):

                same_community_sims.append(sim)

            else:

                diff_community_sims.append(sim)

    

    print(f"  同社区相似度均值: {np.mean(same_community_sims):.4f}")

    print(f"  跨社区相似度均值: {np.mean(diff_community_sims):.4f}")

    

    # 测试3：Node2Vec

    print("\n--- Node2Vec测试 ---")

    

    # p=1, q=1 接近DeepWalk

    node2vec = Node2Vec(embedding_dim=8, walk_length=8, num_walks=5, p=1.0, q=1.0)

    n2v_embeddings = node2vec.fit(adj)

    

    print(f"Node2Vec嵌入形状: {n2v_embeddings.shape}")

    

    # 测试4：p和q的影响

    print("\n--- p和q参数的影响 ---")

    

    configs = [

        (0.5, 0.5),  # BFS倾向

        (0.5, 2.0),  # DFS倾向

        (2.0, 0.5),  # 高度BFS

        (2.0, 2.0),  # 接近随机

    ]

    

    for p, q in configs:

        n2v = Node2Vec(embedding_dim=8, walk_length=8, num_walks=5, p=p, q=q)

        emb = n2v.fit(adj)

        

        # 计算嵌入标准差

        emb_std = np.std(emb)

        print(f"  p={p}, q={q}: 嵌入标准差={emb_std:.4f}")

    

    # 测试5：拉普拉斯矩阵特征值分析

    print("\n--- 拉普拉斯矩阵特征值分析 ---")

    degrees = np.sum(adj, axis=1)

    D = np.diag(degrees)

    L = D - adj

    

    eigenvalues = np.linalg.eigvalsh(L)

    eigenvalues = np.sort(eigenvalues)

    

    print(f"最小的5个特征值: {eigenvalues[:5].round(4)}")

    print(f"特征值间隙: {eigenvalues[1] - eigenvalues[0]:.4f}")

    

    # 测试6：嵌入可视化前的准备

    print("\n--- 嵌入维度约简（PCA模拟） ---")

    # 使用前两个特征向量作为2D表示

    eigenvectors = np.linalg.eigh(L)[1]

    embedding_2d = eigenvectors[:, 1:3]

    

    print(f"2D嵌入形状: {embedding_2d.shape}")

    print(f"2D嵌入范围: [{embedding_2d.min():.4f}, {embedding_2d.max():.4f}]")

    

    # 测试7：社区检测质量评估

    print("\n--- 社区检测质量 ---")

    

    # 计算模块度

    m = np.sum(adj) / 2

    Q = 0

    for i in range(N):

        for j in range(N):

            if labels[i] == labels[j]:

                A_ij = adj[i, j]

                k_i = np.sum(adj[i])

                k_j = np.sum(adj[j])

                Q += A_ij - (k_i * k_j) / (2 * m)

    Q = Q / (2 * m)

    

    print(f"模块度Q: {Q:.4f}")

    print("(接近1表示社区划分质量好)")

    

    print("\n图聚类算法测试完成！")

