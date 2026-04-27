# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / siamese_triplet_loss



本文件实现 siamese_triplet_loss 相关的算法功能。

"""



import numpy as np





class SiameseNetwork:

    """

    Siamese Network（孪生网络）



    参数:

        input_dim: 输入维度

        embedding_dim: 嵌入维度

    """



    def __init__(self, input_dim, embedding_dim=64):

        self.input_dim = input_dim

        self.embedding_dim = embedding_dim



        # 共享编码器（简化为线性层）

        self.encoder_weights = np.random.randn(input_dim, embedding_dim) * np.sqrt(2.0 / input_dim)

        self.encoder_bias = np.zeros(embedding_dim)



    def _encode(self, X):

        """编码"""

        h = X @ self.encoder_weights + self.encoder_bias

        h = np.maximum(0, h)  # ReLU

        return self._l2_normalize(h)



    def _l2_normalize(self, X):

        """L2归一化"""

        norm = np.linalg.norm(X, axis=1, keepdims=True)

        return X / (norm + 1e-10)



    def forward(self, X1, X2=None):

        """

        前向传播



        参数:

            X1: 第一个输入

            X2: 第二个输入（可选）



        返回:

            嵌入向量或距离

        """

        emb1 = self._encode(X1)



        if X2 is None:

            return emb1



        emb2 = self._encode(X2)



        # 计算欧氏距离

        distance = np.linalg.norm(emb1 - emb2, axis=1, keepdims=True)



        return emb1, emb2, distance



    def predict_similarity(self, X1, X2):

        """

        预测相似度



        返回:

            相似度分数（距离的逆或余弦相似度）

        """

        _, _, distance = self.forward(X1, X2)

        similarity = 1.0 / (1.0 + distance)

        return similarity





class TripletLoss:

    """

    三元组损失



    L = max(0, d(a,p) - d(a,n) + margin)

    """



    def __init__(self, margin=0.2):

        self.margin = margin



    def __call__(self, anchor, positive, negative):

        """

        计算三元组损失



        参数:

            anchor: 锚点嵌入 (batch, embedding_dim)

            positive: 正样本嵌入 (batch, embedding_dim)

            negative: 负样本嵌入 (batch, embedding_dim)



        返回:

            loss: 损失值

        """

        # 计算距离

        d_ap = np.linalg.norm(anchor - positive, axis=1)

        d_an = np.linalg.norm(anchor - negative, axis=1)



        # 三元组损失

        losses = np.maximum(0, d_ap - d_an + self.margin)



        return np.mean(losses)



    def get_triplets(self, X, y, n_triplets=100):

        """

        生成三元组



        参数:

            X: 数据

            y: 标签

            n_triplets: 生成数量



        返回:

            anchors, positives, negatives

        """

        n_samples = X.shape[0]

        classes = np.unique(y)



        anchors = []

        positives = []

        negatives = []



        for _ in range(n_triplets):

            # 随机选一个类作为正类，另一个作为负类

            pos_class = np.random.choice(classes)

            neg_class = np.random.choice([c for c in classes if c != pos_class])



            # 从正类中选两个样本

            pos_indices = np.where(y == pos_class)[0]

            neg_indices = np.where(y == neg_class)[0]



            if len(pos_indices) < 2 or len(neg_indices) < 1:

                continue



            a_idx = np.random.choice(pos_indices)

            p_idx = np.random.choice([i for i in pos_indices if i != a_idx])

            n_idx = np.random.choice(neg_indices)



            anchors.append(X[a_idx])

            positives.append(X[p_idx])

            negatives.append(X[n_idx])



        return np.array(anchors), np.array(positives), np.array(negatives)





class MetricLearningClassifier:

    """

    基于度量学习的分类器



    使用Siamese网络学习嵌入，然后用k-NN分类

    """



    def __init__(self, input_dim, embedding_dim=64, n_classes=10):

        self.siamese = SiameseNetwork(input_dim, embedding_dim)

        self.n_classes = n_classes

        self.class_prototypes = {}



    def fit(self, X, y, epochs=100, lr=0.01):

        """

        训练



        参数:

            X: 训练数据

            y: 标签

            epochs: 训练轮数

            lr: 学习率

        """

        n_samples = X.shape[0]

        triplet_loss = TripletLoss(margin=0.2)



        for epoch in range(epochs):

            # 生成三元组

            anchors, positives, negatives = triplet_loss.get_triplets(X, y, n_triplets=32)



            # 前向传播

            emb_a = self.siamese._encode(anchors)

            emb_p = self.siamese._encode(positives)

            emb_n = self.siamese._encode(negatives)



            # 计算损失

            loss = triplet_loss(emb_a, emb_p, emb_n)



            # 简化的梯度更新

            grad_scale = 0.001

            self.siamese.encoder_weights -= lr * grad_scale * (1 + loss)



            if (epoch + 1) % 20 == 0:

                print(f"Epoch {epoch + 1}, Triplet Loss: {loss:.4f}")



        # 保存类别原型

        self._compute_prototypes(X, y)



    def _compute_prototypes(self, X, y):

        """计算每个类的原型（均值嵌入）"""

        for c in range(self.n_classes):

            mask = y == c

            if np.sum(mask) > 0:

                class_samples = X[mask]

                embeddings = self.siamese._encode(class_samples)

                self.class_prototypes[c] = np.mean(embeddings, axis=0)



    def predict(self, X):

        """

        预测（基于到各类原型的距离）



        参数:

            X: 测试数据



        返回:

            预测标签

        """

        embeddings = self.siamese._encode(X)

        predictions = []



        for emb in embeddings:

            # 计算到各类原型的距离

            distances = {}

            for c, proto in self.class_prototypes.items():

                d = np.linalg.norm(emb - proto)

                distances[c] = d



            # 选择最近的类

            pred = min(distances, key=distances.get)

            predictions.append(pred)



        return np.array(predictions)





def test_metric_learning():

    """测试度量学习"""

    np.random.seed(42)



    print("=" * 60)

    print("度量学习：Siamese网络 + 三元组损失")

    print("=" * 60)



    # 生成模拟数据

    n_samples = 300

    n_features = 20

    n_classes = 3



    X = np.random.randn(n_samples, n_features)

    y = np.zeros(n_samples, dtype=int)



    # 创建3个簇

    for i in range(n_classes):

        mask = (i * n_samples // n_classes <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // n_classes)

        X[mask] += np.array([2, 0, -2])[i]

        y[mask] = i



    print(f"\n1. 数据信息:")

    print(f"   样本数: {n_samples}")

    print(f"   特征数: {n_features}")

    print(f"   类别数: {n_classes}")



    # 训练Siamese网络

    print("\n2. 训练Siamese网络:")

    siamese = SiameseNetwork(input_dim=n_features, embedding_dim=16)

    triplet_loss = TripletLoss(margin=0.2)



    # 生成并测试三元组

    anchors, positives, negatives = triplet_loss.get_triplets(X, y, n_triplets=50)



    # 计算初始损失

    emb_a = siamese._encode(anchors)

    emb_p = siamese._encode(positives)

    emb_n = siamese._encode(negatives)



    print(f"   锚点嵌入形状: {emb_a.shape}")

    print(f"   正样本嵌入形状: {emb_p.shape}")

    print(f"   负样本嵌入形状: {emb_n.shape}")



    # 计算三元组损失

    initial_loss = triplet_loss(emb_a, emb_p, emb_n)

    print(f"   初始三元组损失: {initial_loss:.4f}")



    # 测试相似度预测

    print("\n3. 相似度预测:")

    X_test = X[:5]

    similarity = siamese.predict_similarity(X_test, X_test)

    print(f"   自相似度: {np.diag(similarity):.4f}")



    # 不同类别的相似度

    sim_diff = siamese.predict_similarity(X[:1], X[100:101])

    print(f"   跨类别相似度: {sim_diff[0, 0]:.4f}")



    # 训练度量学习分类器

    print("\n4. 训练度量学习分类器:")

    classifier = MetricLearningClassifier(input_dim=n_features, embedding_dim=16, n_classes=n_classes)

    classifier.fit(X, y, epochs=100, lr=0.01)



    # 预测

    predictions = classifier.predict(X)

    accuracy = np.mean(predictions == y)

    print(f"   训练准确率: {accuracy:.4f}")



    print("\n5. 三元组损失原理:")

    print("   ┌─────────────────────────────────────────────┐")

    print("   │ 锚点(a) - 正样本(p): 应距离近               │")

    print("   │ 锚点(a) - 负样本(n): 应距离远               │")

    print("   │ 损失 = max(0, d(a,p) - d(a,n) + margin)    │")

    print("   └─────────────────────────────────────────────┘")





if __name__ == "__main__":

    test_metric_learning()

