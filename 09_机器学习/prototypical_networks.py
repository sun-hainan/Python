# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / prototypical_networks



本文件实现 prototypical_networks 相关的算法功能。

"""



import numpy as np





class PrototypicalNetwork:

    """

    原型网络



    参数:

        input_dim: 输入维度

        embedding_dim: 嵌入维度

    """



    def __init__(self, input_dim, embedding_dim=64):

        self.input_dim = input_dim

        self.embedding_dim = embedding_dim



        # 编码器（简化为线性层 + ReLU）

        self.W = np.random.randn(input_dim, embedding_dim) * np.sqrt(2.0 / input_dim)

        self.b = np.zeros(embedding_dim)



    def _encode(self, X):

        """编码到嵌入空间"""

        h = X @ self.W + self.b

        h = np.maximum(0, h)  # ReLU

        # L2归一化

        return h / (np.linalg.norm(h, axis=1, keepdims=True) + 1e-10)



    def _compute_prototypes(self, support_X, support_y, n_classes):

        """

        计算各类原型



        参数:

            support_X: 支持集（训练样本）

            support_y: 支持集标签

            n_classes: 类别数



        返回:

            prototypes: 每类原型 (n_classes, embedding_dim)

        """

        prototypes = np.zeros((n_classes, self.embedding_dim))



        for c in range(n_classes):

            # 找到类c的所有样本

            mask = support_y == c

            class_samples = support_X[mask]



            if len(class_samples) > 0:

                # 计算原型（类均值）

                class_embeddings = self._encode(class_samples)

                prototypes[c] = np.mean(class_embeddings, axis=0)



        # 重新归一化原型

        norms = np.linalg.norm(prototypes, axis=1, keepdims=True)

        norms = np.where(norms == 0, 1, norms)

        prototypes = prototypes / norms



        return prototypes



    def fit(self, X, y, epochs=100, lr=0.01):

        """

        元训练



        参数:

            X: 所有训练数据

            y: 标签

            epochs: 训练轮数

            lr: 学习率

        """

        n_samples = X.shape[0]

        classes = np.unique(y)

        n_classes = len(classes)



        for epoch in range(epochs):

            # 随机采样一个episode

            # N-way K-shot

            n_way = min(5, n_classes)

            k_shot = 5



            # 选择N个类

            selected_classes = np.random.choice(classes, n_way, replace=False)



            # 每类采样K个作为支持集

            support_X = []

            support_y = []

            for c in selected_classes:

                class_indices = np.where(y == c)[0]

                sampled = np.random.choice(class_indices, min(k_shot, len(class_indices)), replace=False)

                support_X.append(X[sampled])

                support_y.extend([np.where(selected_classes == c)[0][0]] * len(sampled))



            support_X = np.vstack(support_X)

            support_y = np.array(support_y)



            # 计算原型

            prototypes = self._compute_prototypes(support_X, support_y, n_way)



            # 前向

            embeddings = self._encode(support_X)



            # 计算距离并softmax

            distances = self._euclidean_distance(embeddings, prototypes)

            log_probs = self._softmax(-distances)



            # 计算损失（负对数似然）

            loss = -np.mean(log_probs[np.arange(len(support_y)), support_y])



            # 简化梯度更新

            grad_scale = 0.001

            self.W -= lr * grad_scale



            if (epoch + 1) % 20 == 0:

                # 计算准确率

                preds = np.argmax(log_probs, axis=1)

                acc = np.mean(preds == support_y)

                print(f"Epoch {epoch + 1}, Loss: {loss:.4f}, Acc: {acc:.4f}")



    def _euclidean_distance(self, A, B):

        """计算欧氏距离矩阵"""

        # A: (n, d), B: (m, d) -> (n, m)

        na = np.sum(A ** 2, axis=1, keepdims=True)

        nb = np.sum(B ** 2, axis=1, keepdims=True)

        dist = na + nb.T - 2 * A @ B.T

        return np.sqrt(np.clip(dist, 0, None))



    def _softmax(self, X):

        """Softmax"""

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def predict(self, query_X, prototypes):

        """

        预测（基于到原型的距离）



        参数:

            query_X: 查询样本

            prototypes: 原型 (n_classes, embedding_dim)



        返回:

            预测类别

        """

        query_embeddings = self._encode(query_X)

        distances = self._euclidean_distance(query_embeddings, prototypes)

        probs = self._softmax(-distances)

        return np.argmax(probs, axis=1), probs





class EpisodicSampler:

    """

    Episode采样器



    用于少样本学习的episode构建

    """



    def __init__(self, X, y, n_classes):

        self.X = X

        self.y = y

        self.n_classes = n_classes

        self.classes = np.unique(y)



    def sample_episode(self, n_way, k_shot, n_query=15):

        """

        采样一个episode



        参数:

            n_way: 每episode的类别数

            k_shot: 每类支持样本数

            n_query: 每类查询样本数



        返回:

            support_X, support_y, query_X, query_y

        """

        # 选择类别

        selected_classes = np.random.choice(self.classes, n_way, replace=False)



        support_X, support_y = [], []

        query_X, query_y = [], []



        for i, c in enumerate(selected_classes):

            class_indices = np.where(self.y == c)[0]

            sampled = np.random.choice(class_indices, k_shot + n_query, replace=False)



            support_X.append(self.X[sampled[:k_shot]])

            support_y.extend([i] * k_shot)



            query_X.append(self.X[sampled[k_shot:]])

            query_y.extend([i] * n_query)



        return (np.vstack(support_X), np.array(support_y),

                np.vstack(query_X), np.array(query_y))





def test_prototypical_networks():

    """测试原型网络"""

    np.random.seed(42)



    print("=" * 60)

    print("少样本学习：原型网络")

    print("=" * 60)



    # 模拟少样本场景

    n_samples_per_class = 30

    n_features = 20

    n_classes = 10



    # 创建数据：每个类只有少量样本

    X = []

    y = []



    for c in range(n_classes):

        # 每个类30个样本，但只有5个用于训练

        class_center = np.random.randn(n_features) * 3

        class_samples = class_center + np.random.randn(n_samples_per_class, n_features)

        X.append(class_samples)

        y.extend([c] * n_samples_per_class)



    X = np.vstack(X)

    y = np.array(y)



    print(f"\n1. 数据信息:")

    print(f"   总样本数: {len(y)}")

    print(f"   类别数: {n_classes}")

    print(f"   每类样本数: {n_samples_per_class}")



    # 训练原型网络

    print("\n2. 训练原型网络（5-way 1-shot）:")

    model = PrototypicalNetwork(input_dim=n_features, embedding_dim=32)



    # 模拟训练

    for epoch in range(100):

        # 采样episode

        n_way = 5

        k_shot = 5

        n_query = 15



        # 随机选择5个类

        selected_classes = np.random.choice(n_classes, n_way, replace=False)



        # 采样支持集和查询集

        support_X, support_y = [], []

        query_X, query_y = [], []



        for i, c in enumerate(selected_classes):

            class_indices = np.where(y == c)[0]

            sampled = np.random.choice(class_indices, k_shot + n_query, replace=False)



            support_X.append(X[sampled[:k_shot]])

            support_y.extend([i] * k_shot)



            query_X.append(X[sampled[k_shot:]])

            query_y.extend([i] * n_query)



        support_X = np.vstack(support_X)

        support_y = np.array(support_y)

        query_X = np.vstack(query_X)

        query_y = np.array(query_y)



        # 前向

        embeddings = model._encode(support_X)

        prototypes = model._compute_prototypes(support_X, support_y, n_way)



        # 计算距离

        distances = model._euclidean_distance(embeddings, prototypes)

        log_probs = model._softmax(-distances)



        # 损失

        loss = -np.mean(log_probs[np.arange(len(support_y)), support_y])



        # 更新

        model.W -= 0.001



        if (epoch + 1) % 20 == 0:

            preds = np.argmax(log_probs, axis=1)

            acc = np.mean(preds == support_y)

            print(f"   Epoch {epoch + 1}, Loss: {loss:.4f}, Support Acc: {acc:.4f}")



    # 测试少样本分类

    print("\n3. 少样本分类测试（5-way 1-shot）:")

    n_way = 5

    k_shot = 1

    n_query = 5



    # 采样新episode

    selected_classes = np.random.choice(n_classes, n_way, replace=False)



    support_X, support_y = [], []

    query_X, query_y = [], []



    for i, c in enumerate(selected_classes):

        class_indices = np.where(y == c)[0]

        sampled = np.random.choice(class_indices, k_shot + n_query, replace=False)



        support_X.append(X[sampled[:k_shot]])

        support_y.extend([i] * k_shot)



        query_X.append(X[sampled[k_shot:]])

        query_y.extend([i] * n_query)



    support_X = np.vstack(support_X)

    support_y = np.array(support_y)

    query_X = np.vstack(query_X)

    query_y = np.array(query_y)



    # 计算原型

    prototypes = model._compute_prototypes(support_X, support_y, n_way)



    # 预测

    preds, probs = model.predict(query_X, prototypes)

    acc = np.mean(preds == query_y)



    print(f"   支持集准确率: {np.mean(model.predict(support_X, prototypes)[0] == support_y):.4f}")

    print(f"   查询集准确率: {acc:.4f}")



    print("\n4. 原型网络关键点:")

    print("   - 将样本映射到嵌入空间")

    print("   - 每类样本的均值作为原型")

    print("   - 基于欧氏距离进行分类")

    print("   - 适合少样本场景（5-way 1-shot/5-shot）")





if __name__ == "__main__":

    test_prototypical_networks()

