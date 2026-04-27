# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / transfer_learning



本文件实现 transfer_learning 相关的算法功能。

"""



import numpy as np





class TransferLearningFeatureExtractor:

    """

    特征提取器



    使用预训练模型的特征提取能力

    """



    def __init__(self, input_dim, hidden_dim=128):

        self.input_dim = input_dim

        self.hidden_dim = hidden_dim



        # 模拟预训练特征提取器

        # 实际中会使用VGG、ResNet等预训练模型

        self.feature_weights = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / input_dim)

        self.freeze_pretrained_layers()



    def freeze_pretrained_layers(self):

        """冻结预训练层"""

        self.frozen = True



    def extract_features(self, X):

        """

        提取特征



        参数:

            X: 输入数据



        返回:

            features: 提取的特征

        """

        # 模拟预训练特征提取

        features = X @ self.feature_weights

        features = np.maximum(0, features)  # ReLU

        return features





class TransferLearningClassifier:

    """

    迁移学习分类器



    参数:

        input_dim: 输入特征维度

        hidden_dim: 隐藏层维度

        output_dim: 输出类别数

        freeze_backbone: 是否冻结骨干网络

    """



    def __init__(self, input_dim, hidden_dim=256, output_dim=10, freeze_backbone=True):

        self.freeze_backbone = freeze_backbone



        # 骨干网络（特征提取器）

        self.backbone = TransferLearningFeatureExtractor(input_dim, hidden_dim)



        # 分类头

        self.classifier_weights = np.random.randn(hidden_dim, output_dim) * np.sqrt(2.0 / hidden_dim)

        self.classifier_bias = np.zeros(output_dim)



        if freeze_backbone:

            self.backbone.freeze_pretrained_layers()



    def _softmax(self, X):

        """Softmax"""

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def forward(self, X):

        """

        前向传播



        参数:

            X: 输入数据

        """

        # 特征提取

        features = self.backbone.extract_features(X)



        # 分类

        logits = features @ self.classifier_weights + self.classifier_bias

        probs = self._softmax(logits)



        return probs, features



    def fit(self, X, y, epochs=100, lr=0.01, lr_backbone=0.0001):

        """

        训练



        参数:

            X, y: 训练数据

            epochs: 训练轮数

            lr: 分类头学习率

            lr_backbone: 骨干网络学习率（如果未冻结）

        """

        n_samples = X.shape[0]



        for epoch in range(epochs):

            # 随机采样

            indices = np.random.choice(n_samples, min(32, n_samples), replace=False)

            batch_X = X[indices]

            batch_y = y[indices]



            # 前向

            probs, features = self.forward(batch_X)



            # 损失

            eps = 1e-10

            loss = -np.mean(batch_y * np.log(probs + eps))



            # 反向（简化）

            # 分类头梯度

            grad_logits = probs - batch_y

            grad_W = features.T @ grad_logits / len(batch_X)

            grad_b = np.mean(grad_logits, axis=0)



            # 更新分类头

            self.classifier_weights -= lr * grad_W

            self.classifier_bias -= lr * grad_b



            # 如果未冻结，更新骨干网络

            if not self.freeze_backbone:

                # 用更小的学习率

                grad_features = grad_logits @ self.classifier_weights.T

                grad_backbone = batch_X.T @ grad_features / len(batch_X) * 0.01  # 简化

                self.backbone.feature_weights -= lr_backbone * grad_backbone



            if (epoch + 1) % 20 == 0:

                preds = np.argmax(probs, axis=1)

                labels = np.argmax(batch_y, axis=1)

                acc = np.mean(preds == labels)

                print(f"Epoch {epoch + 1}, Loss: {loss:.4f}, Acc: {acc:.4f}")





class FineTuningStrategy:

    """

    微调策略集合

    """



    @staticmethod

    def full_fine_tuning(model, X, y, epochs=100, lr=0.001):

        """全部微调"""

        print("   策略: 全部微调")

        # 所有参数都用相同学习率

        model.freeze_backbone = False

        model.fit(X, y, epochs=epochs, lr=lr, lr_backbone=lr)



    @staticmethod

    def layer_wise_unfreezing(model, X, y, unfreeze_epochs=20, lr=0.01):

        """

        逐层解冻



        从最后一层开始逐步解冻

        """

        print("   策略: 逐层解冻")



        # 阶段1: 只训练分类头

        model.freeze_backbone = True

        print("   阶段1: 训练分类头")

        model.fit(X, y, epochs=unfreeze_epochs, lr=lr, lr_backbone=lr)



        # 阶段2: 解冻部分骨干层

        print("   阶段2: 解冻部分层")

        model.freeze_backbone = False

        model.fit(X, y, epochs=unfreeze_epochs, lr=lr * 0.1, lr_backbone=lr * 0.1)



    @staticmethod

    def discriminative_learning_rates(model, X, y, epochs=100,

                                      lr_head=0.01, lr_backbone=0.001):

        """

        区分学习率



        分类头用大学习率，骨干用小学习率

        """

        print("   策略: 区分学习率")

        model.freeze_backbone = False

        model.fit(X, y, epochs=epochs, lr=lr_head, lr_backbone=lr_backbone)





def test_transfer_learning():

    """测试迁移学习"""

    np.random.seed(42)



    print("=" * 60)

    print("迁移学习测试")

    print("=" * 60)



    # 模拟数据：ImageNet预训练场景

    # 源域：大规模数据训练的模型

    # 目标域：只有少量数据的特定任务



    # 源域特征（模拟预训练模型提取的特征）

    n_source = 5000

    source_features_dim = 512  # 预训练模型输出维度



    # 生成模拟源域特征

    source_features = np.random.randn(n_source, source_features_dim)



    # 目标域数据（少样本）

    n_target = 100

    target_features_dim = 512

    n_classes = 5



    target_features = np.random.randn(n_target, target_features_dim)

    labels = np.random.randint(0, n_classes, n_target)

    target_y = np.zeros((n_target, n_classes))

    target_y[np.arange(n_target), labels] = 1



    print(f"\n1. 数据信息:")

    print(f"   源域样本数: {n_source} (预训练)")

    print(f"   目标域样本数: {n_target} (少样本)")

    print(f"   特征维度: {target_features_dim}")

    print(f"   类别数: {n_classes}")



    # 特征提取策略

    print("\n2. 特征提取策略:")

    classifier = TransferLearningClassifier(

        input_dim=target_features_dim,

        hidden_dim=128,

        output_dim=n_classes,

        freeze_backbone=True  # 冻结骨干，只训练分类头

    )



    print("   骨干网络: 冻结（使用预训练特征）")

    print("   分类头: 可训练")



    classifier.fit(target_features, target_y, epochs=100, lr=0.01)



    # 测试特征提取效果

    probs, features = classifier.forward(target_features)

    preds = np.argmax(probs, axis=1)

    acc = np.mean(preds == labels)

    print(f"\n   特征提取准确率: {acc:.4f}")



    # 微调策略对比

    print("\n3. 微调策略对比:")



    print("\n   策略1: 全量微调")

    classifier_full = TransferLearningClassifier(

        input_dim=target_features_dim,

        hidden_dim=128,

        output_dim=n_classes,

        freeze_backbone=False

    )

    classifier_full.fit(target_features, target_y, epochs=50, lr=0.001)



    print("\n   策略2: 区分学习率")

    classifier_disc = TransferLearningClassifier(

        input_dim=target_features_dim,

        hidden_dim=128,

        output_dim=n_classes,

        freeze_backbone=False

    )

    FineTuningStrategy.discriminative_learning_rates(

        classifier_disc, target_features, target_y,

        epochs=50, lr_head=0.01, lr_backbone=0.001

    )



    print("\n4. 何时使用哪种策略:")

    print("   ┌─────────────────────────────────────────────┐")

    print("   │ 特征提取（冻结）:                           │")

    print("   │   - 目标数据少 (< 1k)                      │")

    print("   │   - 源域和目标域相似                        │")

    print("   │   - 需要快速部署                            │")

    print("   │                                            │")

    print("   │ 微调（解冻）:                               │")

    print("   │   - 目标数据中等 (1k-50k)                  │")

    print("   │   - 域差异较大                              │")

    print("   │   - 需要更高精度                            │")

    print("   └─────────────────────────────────────────────┘")





if __name__ == "__main__":

    test_transfer_learning()

