# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / gnn_applications



本文件实现 gnn_applications 相关的算法功能。

"""



import numpy as np





# 简化的图神经网络层（复用到一起）



class SimpleGCNLayer:

    def __init__(self, in_dim, out_dim):

        self.W = np.random.randn(in_dim, out_dim) * np.sqrt(2.0 / in_dim)

    

    def forward(self, features, adj):

        adj = adj + np.eye(adj.shape[0])

        d = np.sum(adj, axis=1)

        d_inv_sqrt = np.power(d, -0.5)

        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.0

        adj_norm = np.diag(d_inv_sqrt) @ adj @ np.diag(d_inv_sqrt)

        return np.maximum(0, adj_norm @ features @ self.W)





class NodeClassifier:

    """节点分类器"""

    

    def __init__(self, num_features, hidden_dim, num_classes):

        self.gcn1 = SimpleGCNLayer(num_features, hidden_dim)

        self.gcn2 = SimpleGCNLayer(hidden_dim, num_classes)

    

    def forward(self, features, adj, mask=None):

        h = self.gcn1.forward(features, adj)

        h = np.maximum(0, h)

        logits = self.gcn2.forward(h, adj)

        

        if mask is not None:

            logits = logits[mask]

        

        return logits

    

    def predict(self, features, adj):

        logits = self.forward(features, adj)

        return np.argmax(logits, axis=1)





class EdgePredictor:

    """边预测器"""

    

    def __init__(self, node_dim, hidden_dim):

        self.node_dim = node_dim

        self.hidden_dim = hidden_dim

        

        self.W = np.random.randn(node_dim * 2, hidden_dim) * 0.01

        self.predictor = np.random.randn(hidden_dim, 1) * 0.01

    

    def forward(self, node_embeddings, edge_list):

        """

        预测边存在概率

        

        参数:

            node_embeddings: 节点嵌入 (N, node_dim)

            edge_list: 边列表 [(src, dst), ...]

        返回:

            scores: 边存在概率

        """

        scores = []

        

        for src, dst in edge_list:

            # 拼接源和目标节点嵌入

            combined = np.concatenate([node_embeddings[src], node_embeddings[dst]])

            

            #MLP

            h = np.maximum(0, combined @ self.W)

            score = 1 / (1 + np.exp(-(h @ self.predictor)[0, 0]))

            scores.append(score)

        

        return np.array(scores)





class GraphClassifier:

    """图分类器"""

    

    def __init__(self, node_dim, hidden_dim, num_classes):

        self.gcn1 = SimpleGCNLayer(node_dim, hidden_dim)

        self.gcn2 = SimpleGCNLayer(hidden_dim, hidden_dim)

        self.classifier = np.random.randn(hidden_dim, num_classes) * 0.01

    

    def forward(self, features, adj):

        """

        图分类前馈

        

        参数:

            features: 节点特征 (N, node_dim)

            adj: 邻接矩阵 (N, N)

        返回:

            graph_logits: 图级别logits (num_classes,)

        """

        # 图卷积

        h = self.gcn1.forward(features, adj)

        h = np.maximum(0, h)

        h = self.gcn2.forward(h, adj)

        h = np.maximum(0, h)

        

        # 图级别池化（平均）

        graph_repr = np.mean(h, axis=0)

        

        # 分类

        logits = graph_repr @ self.classifier

        

        return logits





def train_node_classification():

    """节点分类训练模拟"""

    print("=" * 55)

    print("节点分类示例")

    print("=" * 55)

    

    np.random.seed(42)

    

    # 创建测试图

    n = 100

    adj = np.zeros((n, n))

    

    # 生成社区结构

    for i in range(n):

        for j in range(i + 1, n):

            if i // 25 == j // 25:  # 同社区

                if np.random.random() < 0.4:

                    adj[i, j] = adj[j, i] = 1

            else:  # 不同社区

                if np.random.random() < 0.02:

                    adj[i, j] = adj[j, i] = 1

    

    # 节点特征

    features = np.random.randn(n, 16)

    

    # 节点标签（4个类别）

    labels = np.array([i // 25 for i in range(n)])

    

    # 划分训练/测试

    train_mask = np.zeros(n, dtype=bool)

    test_mask = np.zeros(n, dtype=bool)

    

    for c in range(4):

        class_nodes = np.where(labels == c)[0]

        np.random.shuffle(class_nodes)

        train_mask[class_nodes[:5]] = True

        test_mask[class_nodes[5:]] = True

    

    # 模型

    classifier = NodeClassifier(num_features=16, hidden_dim=32, num_classes=4)

    

    # 训练模拟

    print(f"\n图信息: {n}节点, {int(np.sum(adj)/2)}边")

    print(f"类别数: 4")

    print(f"训练节点: {train_mask.sum()}, 测试节点: {test_mask.sum()}")

    

    # 训练

    for epoch in range(100):

        logits = classifier.forward(features, adj, train_mask)

        train_labels = labels[train_mask]

        

        # 简化训练（交叉熵损失）

        probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)

        

        # 计算准确率

        preds = np.argmax(logits, axis=1)

        train_acc = np.mean(preds == train_labels)

        

        if (epoch + 1) % 20 == 0:

            print(f"Epoch {epoch+1}: Train Acc = {train_acc:.2%}")

    

    # 测试

    test_logits = classifier.forward(features, adj, test_mask)

    test_labels = labels[test_mask]

    test_preds = np.argmax(test_logits, axis=1)

    test_acc = np.mean(test_preds == test_labels)

    

    print(f"\n测试准确率: {test_acc:.2%}")

    

    return classifier, test_acc





def train_edge_prediction():

    """边预测训练模拟"""

    print("\n" + "=" * 55)

    print("边预测示例")

    print("=" * 55)

    

    np.random.seed(42)

    

    # 创建图

    n = 50

    adj = np.zeros((n, n))

    

    for i in range(n):

        for j in range(i + 1, n):

            if np.random.random() < 0.15:

                adj[i, j] = adj[j, i] = 1

    

    # 节点特征

    features = np.random.randn(n, 16)

    

    # 边预测器

    gcn = SimpleGCNLayer(16, 32)

    embeddings = gcn.forward(features, adj)

    embeddings = np.maximum(0, embeddings)

    

    predictor = EdgePredictor(node_dim=32, hidden_dim=16)

    

    # 真实边

    positive_edges = []

    for i in range(n):

        for j in range(i + 1, n):

            if adj[i, j] > 0:

                positive_edges.append((i, j))

    

    # 负样本边（不存在的边）

    negative_edges = []

    while len(negative_edges) < len(positive_edges):

        i, j = np.random.randint(0, n), np.random.randint(0, n)

        if i != j and adj[i, j] == 0:

            negative_edges.append((i, j))

    

    print(f"\n正样本边: {len(positive_edges)}")

    print(f"负样本边: {len(negative_edges)}")

    

    # 预测

    pos_scores = predictor.forward(embeddings, positive_edges)

    neg_scores = predictor.forward(embeddings, negative_edges)

    

    print(f"\n正样本分数: {np.mean(pos_scores):.4f}")

    print(f"负样本分数: {np.mean(neg_scores):.4f}")

    print(f"区分度: {np.mean(pos_scores > neg_scores):.2%}")

    

    return predictor





def train_graph_classification():

    """图分类训练模拟"""

    print("\n" + "=" * 55)

    print("图分类示例")

    print("=" * 55)

    

    np.random.seed(42)

    

    num_graphs = 50

    avg_nodes = 20

    num_classes = 2

    

    graphs = []

    graph_labels = []

    

    # 生成两类图

    for i in range(num_graphs):

        n = np.random.randint(avg_nodes // 2, avg_nodes * 2)

        

        features = np.random.randn(n, 8)

        

        # 类别0：稀疏图，类别1：密集图

        density = 0.1 if i < num_graphs // 2 else 0.4

        adj = (np.random.rand(n, n) < density).astype(float)

        adj = (adj + adj.T) / 2

        np.fill_diagonal(adj, 0)

        

        graphs.append({'features': features, 'adj': adj})

        graph_labels.append(i // (num_graphs // 2))

    

    print(f"\n图数量: {num_graphs}")

    print(f"类别0（图稀疏）: {sum(1 for l in graph_labels if l == 0)}")

    print(f"类别1（图密集）: {sum(1 for l in graph_labels if l == 1)}")

    

    # 模型

    classifier = GraphClassifier(node_dim=8, hidden_dim=16, num_classes=2)

    

    # 训练

    for epoch in range(50):

        total_loss = 0

        

        for g, label in zip(graphs, graph_labels):

            logits = classifier.forward(g['features'], g['adj'])

            

            # 简化损失

            probs = np.exp(logits) / np.sum(np.exp(logits))

            loss = -np.log(probs[label] + 1e-8)

            total_loss += loss

        

        if (epoch + 1) % 10 == 0:

            print(f"Epoch {epoch+1}: Avg Loss = {total_loss / len(graphs):.4f}")

    

    # 评估

    correct = 0

    for g, label in zip(graphs, graph_labels):

        logits = classifier.forward(g['features'], g['adj'])

        pred = np.argmax(logits)

        if pred == label:

            correct += 1

    

    acc = correct / len(graphs)

    print(f"\n图分类准确率: {acc:.2%}")

    

    return classifier, acc





if __name__ == "__main__":

    # 节点分类

    node_clf, node_acc = train_node_classification()

    

    # 边预测

    edge_pred = train_edge_prediction()

    

    # 图分类

    graph_clf, graph_acc = train_graph_classification()

    

    print("\n" + "=" * 55)

    print("应用示例总结")

    print("=" * 55)

    print(f"节点分类准确率: {node_acc:.2%}")

    print(f"边预测区分度: 基于嵌入相似度")

    print(f"图分类准确率: {graph_acc:.2%}")

    

    print("\n图神经网络应用示例测试完成！")

