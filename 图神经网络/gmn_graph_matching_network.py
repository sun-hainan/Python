# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / gmn_graph_matching_network



本文件实现 gmn_graph_matching_network 相关的算法功能。

"""



import numpy as np





# ============================

# 辅助函数

# ============================



def l2_normalize(x, axis=1):

    """L2归一化"""

    norm = np.linalg.norm(x, axis=axis, keepdims=True)

    return x / (norm + 1e-8)





def cosine_similarity(x, y):

    """余弦相似度"""

    x_norm = l2_normalize(x, axis=-1)

    y_norm = l2_normalize(y, axis=-1)

    return np.sum(x_norm * y_norm, axis=-1)





# ============================

# GMN层

# ============================



class GMNLayer:

    """

    图匹配网络层

    

    核心思想：通过交互比较两个图的节点，聚合匹配信息

    

    参数:

        node_dim: 节点特征维度

        edge_dim: 边特征维度

        hidden_dim: 隐藏层维度

    """

    

    def __init__(self, node_dim, edge_dim, hidden_dim=64):

        self.node_dim = node_dim

        self.edge_dim = edge_dim

        self.hidden_dim = hidden_dim

        

        # 节点特征变换

        self.W_node = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)

        self.b_node = np.zeros(hidden_dim)

        

        # 边特征变换

        self.W_edge = np.random.randn(edge_dim, hidden_dim) * np.sqrt(2.0 / edge_dim)

        self.b_edge = np.zeros(hidden_dim)

        

        # 交叉图交互（用于比较两个图的节点）

        self.W_cross = np.random.randn(hidden_dim * 2, hidden_dim) * np.sqrt(2.0 / hidden_dim)

        self.b_cross = np.zeros(hidden_dim)

        

        # 注意力

        self.W_attention = np.random.randn(hidden_dim, 1) * 0.01

    

    def forward(self, features1, features2, adj1=None, adj2=None):

        """

        GMN层前馈传播

        

        参数:

            features1: 图1的节点特征 (N1, node_dim)

            features2: 图2的节点特征 (N2, node_dim)

            adj1: 图1的邻接矩阵 (N1, N1)，可选

            adj2: 图2的邻接矩阵 (N2, N2)，可选

        返回:

            updated1: 更新后的图1节点特征 (N1, hidden_dim)

            updated2: 更新后的图2节点特征 (N2, hidden_dim)

            similarity_matrix: 节点相似度矩阵 (N1, N2)

        """

        N1 = features1.shape[0]

        N2 = features2.shape[0]

        

        # 1. 节点特征变换

        h1 = np.maximum(0, features1 @ self.W_node + self.b_node)

        h2 = np.maximum(0, features2 @ self.W_node + self.b_node)

        

        # 2. 计算交叉图注意力/相似度

        # similarity[i,j] = 节点i和节点j的相似度

        similarity_matrix = np.zeros((N1, N2))

        

        for i in range(N1):

            for j in range(N2):

                # 拼接两个节点特征

                combined = np.concatenate([h1[i], h2[j]])

                sim = combined @ self.W_cross[:h1.shape[1] * 2] + self.b_cross

                # 简化的相似度

                similarity_matrix[i, j] = np.exp(-np.sum((h1[i] - h2[j])[:self.hidden_dim]) ** 2) / self.hidden_dim

        

        # 3. 交叉图信息传递

        # 图1的节点聚合来自图2的信息

        cross_msg_1to2 = similarity_matrix.T @ h1  # (N2, hidden_dim)

        # 图2的节点聚合来自图1的信息

        cross_msg_2to1 = similarity_matrix @ h2  # (N1, hidden_dim)

        

        # 4. 更新节点表示

        # 结合自身表示和交叉图消息

        updated1 = np.maximum(0, h1 + cross_msg_2to1 @ (np.random.randn(self.hidden_dim, self.hidden_dim) * 0.01))

        updated2 = np.maximum(0, h2 + cross_msg_1to2 @ (np.random.randn(self.hidden_dim, self.hidden_dim) * 0.01))

        

        # 5. 可选：图内聚合（如果提供了邻接矩阵）

        if adj1 is not None:

            adj1_norm = adj1 / (np.sum(adj1, axis=1, keepdims=True) + 1e-8)

            updated1 = updated1 + 0.1 * (adj1_norm @ updated1)

        

        if adj2 is not None:

            adj2_norm = adj2 / (np.sum(adj2, axis=1, keepdims=True) + 1e-8)

            updated2 = updated2 + 0.1 * (adj2_norm @ updated2)

        

        return updated1, updated2, similarity_matrix





class GraphMatchingNetwork:

    """

    完整图匹配网络

    

    参数:

        node_dim: 节点特征维度

        hidden_dim: 隐藏层维度

        num_layers: GMN层数

    """

    

    def __init__(self, node_dim, hidden_dim=64, num_layers=3):

        self.node_dim = node_dim

        self.hidden_dim = hidden_dim

        self.num_layers = num_layers

        

        self.layers = []

        for _ in range(num_layers):

            self.layers.append(GMNLayer(node_dim, 0, hidden_dim))

            node_dim = hidden_dim  # 后续层输入维度变化

    

    def forward(self, features1, features2, adj1=None, adj2=None):

        """

        前馈传播

        

        参数:

            features1: 图1节点特征 (N1, node_dim)

            features2: 图2节点特征 (N2, node_dim)

            adj1, adj2: 邻接矩阵

        返回:

            graph_sim: 图级相似度

            node_sim: 节点级相似度矩阵

            embedding1, embedding2: 最终节点嵌入

        """

        h1 = features1

        h2 = features2

        

        similarity_matrices = []

        

        for i, layer in enumerate(self.layers):

            h1, h2, sim = layer.forward(h1, h2, 

                                         adj1 if i == 0 else None,

                                         adj2 if i == 0 else None)

            similarity_matrices.append(sim)

        

        # 图级相似度 = 节点级相似度的和

        final_sim = similarity_matrices[-1]

        graph_sim = np.sum(final_sim)

        

        # 归一化

        graph_sim = graph_sim / (h1.shape[0] * h2.shape[0] + 1e-8)

        

        return graph_sim, final_sim, h1, h2

    

    def predict_similarity(self, features1, features2, adj1=None, adj2=None):

        """

        预测两个图的相似度

        

        返回:

            similarity: 相似度分数 (0-1)

        """

        graph_sim, _, _, _ = self.forward(features1, features2, adj1, adj2)

        

        # Sigmoid映射到0-1

        return 1 / (1 + np.exp(-graph_sim))





class NodeAlignmentNetwork:

    """

    节点对齐网络（用于节点匹配任务）

    

    与GMN类似，但输出节点对应关系

    """

    

    def __init__(self, node_dim, hidden_dim=64):

        self.node_dim = node_dim

        self.hidden_dim = hidden_dim

        

        # 特征编码

        self.W_encode = np.random.randn(node_dim, hidden_dim) * np.sqrt(2.0 / node_dim)

        

        # 相似度计算

        self.W_sim = np.random.randn(hidden_dim, hidden_dim) * 0.01

    

    def encode(self, features):

        """编码节点特征"""

        return np.maximum(0, features @ self.W_encode)

    

    def compute_similarity_matrix(self, emb1, emb2):

        """计算相似度矩阵"""

        N1, N2 = emb1.shape[0], emb2.shape[0]

        

        # 广播计算成对相似度

        sim_matrix = np.zeros((N1, N2))

        

        for i in range(N1):

            for j in range(N2):

                diff = emb1[i] - emb2[j]

                sim_matrix[i, j] = np.exp(-np.sum(diff ** 2) / self.hidden_dim)

        

        return sim_matrix

    

    def sinkhorn(self, sim_matrix, num_iterations=10):

        """

        Sinkhorn算法：用于软对齐

        

        参数:

            sim_matrix: 相似度矩阵 (N1, N2)

            num_iterations: 迭代次数

        返回:

            alignment: 对齐矩阵

        """

        N1, N2 = sim_matrix.shape

        

        # 行归一化

        P = sim_matrix.copy()

        for _ in range(num_iterations):

            # 行归一化

            P = P / (np.sum(P, axis=1, keepdims=True) + 1e-8)

            # 列归一化

            P = P / (np.sum(P, axis=0, keepdims=True) + 1e-8)

        

        return P

    

    def forward(self, features1, features2):

        """

        前馈传播

        

        参数:

            features1: 图1节点特征

            features2: 图2节点特征

        返回:

            alignment: 软对齐矩阵 (N1, N2)

            sim_matrix: 原始相似度矩阵

        """

        # 编码

        emb1 = self.encode(features1)

        emb2 = self.encode(features2)

        

        # 相似度矩阵

        sim_matrix = self.compute_similarity_matrix(emb1, emb2)

        

        # Sinkhorn对齐

        alignment = self.Sinkhorn(sim_matrix)

        

        return alignment, sim_matrix





# ============================

# 测试代码

# ============================



if __MAME__ == "__main__":

    np.random.seed(42)

    

    print("=" * 55)

    print("图匹配网络（GMN）测试")

    print("=" * 55)

    

    # 创建两个测试图

    N1 = 5  # 图1节点数

    N2 = 6  # 图2节点数

    node_dim = 8

    

    features1 = np.random.randn(N1, node_dim)

    features2 = np.random.randn(N2, node_dim)

    

    # 邻接矩阵（可选）

    adj1 = np.zeros((N1, N1))

    adj2 = np.zeros((N2, N2))

    

    # 简单连接

    for i in range(N1 - 1):

        adj1[i, i+1] = adj1[i+1, i] = 1

    for i in range(N2 - 1):

        adj2[i, i+1] = adj2[i+1, i] = 1

    

    print(f"图1: {N1}节点, {int(np.sum(adj1)/2)}边")

    print(f"图2: {N2}节点, {int(np.sum(adj2)/2)}边")

    

    # 测试1：GMN层

    print("\n--- GMN层测试 ---")

    gmn_layer = GMNLayer(node_dim=node_dim, edge_dim=0, hidden_dim=16)

    

    updated1, updated2, sim_matrix = gmn_layer.forward(features1, features2, adj1, adj2)

    

    print(f"输入特征形状: ({features1.shape}, {features2.shape})")

    print(f"更新后特征形状: ({updated1.shape}, {updated2.shape})")

    print(f"相似度矩阵形状: {sim_matrix.shape}")

    

    # 查看相似度矩阵

    print(f"\n相似度矩阵:\n{sim_matrix.round(3)}")

    

    # 找出最相似的节点对

    max_i, max_j = np.unravel_index(np.argmax(sim_matrix), sim_matrix.shape)

    print(f"最相似节点对: 图1节点{max_i} <-> 图2节点{max_j}")

    

    # 测试2：完整GMN

    print("\n--- 完整GMN测试 ---")

    gmn = GraphMatchingNetwork(node_dim=node_dim, hidden_dim=16, num_layers=2)

    

    graph_sim, node_sim, emb1, emb2 = gmn.forward(features1, features2, adj1, adj2)

    

    print(f"图级相似度: {graph_sim:.4f}")

    print(f"节点嵌入形状: ({emb1.shape}, {emb2.shape})")

    

    # 测试3：相似度预测

    print("\n--- 相似度预测 ---")

    similarity_score = gmn.predict_similarity(features1, features2, adj1, adj2)

    

    print(f"预测相似度分数: {similarity_score:.4f}")

    print("(1表示完全相同，0表示完全不同)")

    

    # 测试4：节点对齐网络

    print("\n--- 节点对齐网络测试 ---")

    align_net = NodeAlignmentNetwork(node_dim=node_dim, hidden_dim=16)

    

    alignment, sim = align_net.forward(features1, features2)

    

    print(f"相似度矩阵形状: {sim.shape}")

    print(f"对齐矩阵形状: {alignment.shape}")

    print(f"\n对齐矩阵:\n{alignment.round(3)}")

    

    # 每个节点的最高对齐

    print("\n节点对齐结果:")

    for i in range(N1):

        aligned_j = np.argmax(alignment[i])

        confidence = alignment[i, aligned_j]

        print(f"  图1节点{i} -> 图2节点{aligned_j} (置信度: {confidence:.3f})")

    

    # 测试5：同构图 vs 异构图

    print("\n--- 同构图 vs 异构图相似度 ---")

    

    # 创建同构图（结构和特征相似）

    same_features1 = np.random.randn(4, 8) * 0.5 + np.array([1, 0, 0, 0, 0, 0, 0, 0])

    same_features2 = np.random.randn(4, 8) * 0.5 + np.array([1, 0, 0, 0, 0, 0, 0, 0])

    

    # 创建异构图

    diff_features1 = np.random.randn(4, 8) * 5

    diff_features2 = np.random.randn(4, 8)

    

    gmn_test = GraphMatchingNetwork(node_dim=8, hidden_dim=16, num_layers=2)

    

    sim_same = gmn_test.predict_similarity(same_features1, same_features2)

    sim_diff = gmn_test.predict_similarity(diff_features1, diff_features2)

    

    print(f"同构图相似度: {sim_same:.4f}")

    print(f"异构图相似度: {sim_diff:.4f}")

    print(f"同构图相似度 > 异构图: {sim_same > sim_diff}")

    

    # 测试6：多跳消息传递效果

    print("\n--- 多层GMN的效果 ---")

    for num_layers in [1, 2, 3, 5]:

        gmn_multi = GraphMatchingNetwork(node_dim=node_dim, hidden_dim=16, num_layers=num_layers)

        graph_sim, _, _, _ = gmn_multi.forward(features1, features2, adj1, adj2)

        print(f"  {num_layers}层: 图相似度={graph_sim:.4f}")

    

    # 测试7：嵌入空间分析

    print("\n--- 嵌入空间分析 ---")

    emb1_final, emb2_final = None, None

    

    for num_layers in [1, 2]:

        gmn_layers = GraphMatchingNetwork(node_dim=node_dim, hidden_dim=8, num_layers=num_layers)

        _, _, e1, e2 = gmn_layers.forward(features1, features2, adj1, adj2)

        emb1_final, emb2_final = e1, e2

    

    print(f"图1嵌入范围: [{emb1_final.min():.4f}, {emb1_final.max():.4f}]")

    print(f"图2嵌入范围: [{emb2_final.min():.4f}, {emb2_final.max():.4f}]")

    print(f"嵌入维度: {emb1_final.shape[1]}")

    

    # 测试8：Sinkhorn收敛性

    print("\n--- Sinkhorn收敛性 ---")

    test_sim = np.random.rand(5, 5)

    test_sim = test_sim / test_sim.sum()

    

    align_net2 = NodeAlignmentNetwork(node_dim=8, hidden_dim=16)

    alignment_final = align_net2.Sinkhorn(test_sim, num_iterations=20)

    

    print(f"对齐后矩阵行和: {np.sum(alignment_final, axis=1).round(3)}")

    print(f"对齐后矩阵列和: {np.sum(alignment_final, axis=0).round(3)}")

    

    print("\nGMN测试完成！")





# ============================

# 修复：__name__ == "__main__" 拼写错误

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 55)

    print("图匹配网络（GMN）测试")

    print("=" * 55)

    

    # 创建两个测试图

    N1 = 5  # 图1节点数

    N2 = 6  # 图2节点数

    node_dim = 8

    

    features1 = np.random.randn(N1, node_dim)

    features2 = np.random.randn(N2, node_dim)

    

    # 邻接矩阵（可选）

    adj1 = np.zeros((N1, N1))

    adj2 = np.zeros((N2, N2))

    

    # 简单连接

    for i in range(N1 - 1):

        adj1[i, i+1] = adj1[i+1, i] = 1

    for i in range(N2 - 1):

        adj2[i, i+1] = adj2[i+1, i] = 1

    

    print(f"图1: {N1}节点, {int(np.sum(adj1)/2)}边")

    print(f"图2: {N2}节点, {int(np.sum(adj2)/2)}边")

    

    # 测试1：GMN层

    print("\n--- GMN层测试 ---")

    gmn_layer = GMNLayer(node_dim=node_dim, edge_dim=0, hidden_dim=16)

    

    updated1, updated2, sim_matrix = gmn_layer.forward(features1, features2, adj1, adj2)

    

    print(f"输入特征形状: ({features1.shape}, {features2.shape})")

    print(f"更新后特征形状: ({updated1.shape}, {updated2.shape})")

    print(f"相似度矩阵形状: {sim_matrix.shape}")

    

    print(f"\n相似度矩阵:\n{sim_matrix.round(3)}")

    

    max_i, max_j = np.unravel_index(np.argmax(sim_matrix), sim_matrix.shape)

    print(f"最相似节点对: 图1节点{max_i} <-> 图2节点{max_j}")

    

    # 测试2：完整GMN

    print("\n--- 完整GMN测试 ---")

    gmn = GraphMatchingNetwork(node_dim=node_dim, hidden_dim=16, num_layers=2)

    

    graph_sim, node_sim, emb1, emb2 = gmn.forward(features1, features2, adj1, adj2)

    

    print(f"图级相似度: {graph_sim:.4f}")

    print(f"节点嵌入形状: ({emb1.shape}, {emb2.shape})")

    

    # 测试3：相似度预测

    print("\n--- 相似度预测 ---")

    similarity_score = gmn.predict_similarity(features1, features2, adj1, adj2)

    

    print(f"预测相似度分数: {similarity_score:.4f}")

    

    # 测试4：节点对齐网络

    print("\n--- 节点对齐网络测试 ---")

    align_net = NodeAlignmentNetwork(node_dim=node_dim, hidden_dim=16)

    

    alignment, sim = align_net.forward(features1, features2)

    

    print(f"对齐矩阵形状: {alignment.shape}")

    

    print("\n节点对齐结果:")

    for i in range(N1):

        aligned_j = np.argmax(alignment[i])

        confidence = alignment[i, aligned_j]

        print(f"  图1节点{i} -> 图2节点{aligned_j} (置信度: {confidence:.3f})")

    

    # 测试5：同构图 vs 异构图

    print("\n--- 同构图 vs 异构图相似度 ---")

    

    same_features1 = np.random.randn(4, 8) * 0.5 + np.array([1, 0, 0, 0, 0, 0, 0, 0])

    same_features2 = np.random.randn(4, 8) * 0.5 + np.array([1, 0, 0, 0, 0, 0, 0, 0])

    diff_features1 = np.random.randn(4, 8) * 5

    diff_features2 = np.random.randn(4, 8)

    

    gmn_test = GraphMatchingNetwork(node_dim=8, hidden_dim=16, num_layers=2)

    

    sim_same = gmn_test.predict_similarity(same_features1, same_features2)

    sim_diff = gmn_test.predict_similarity(diff_features1, diff_features2)

    

    print(f"同构图相似度: {sim_same:.4f}")

    print(f"异构图相似度: {sim_diff:.4f}")

    print(f"同构图相似度 > 异构图: {sim_same > sim_diff}")

    

    print("\nGMN测试完成！")

