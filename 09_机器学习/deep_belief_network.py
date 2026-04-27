# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / deep_belief_network

本文件实现 deep_belief_network 相关的算法功能。
"""

import numpy as np


class DeepBeliefNetwork:
    """
    深度信念网络实现

    参数:
        layer_dims: 各层维度列表，如[784, 256, 128, 10]
        rbm_learning_rate: RBM预训练学习率
        rbm_iterations: 每层RBM训练迭代次数
        rbm_k: CD-k采样步数
    """

    def __init__(self, layer_dims, rbm_learning_rate=0.01, rbm_iterations=100, rbm_k=1):
        self.layer_dims = layer_dims
        self.rbm_learning_rate = rbm_learning_rate
        self.rbm_iterations = rbm_iterations
        self.rbm_k = rbm_k
        self.rbms = []
        self.classification_weights = None
        self.classification_bias = None

    def _sigmoid(self, X):
        """Sigmoid激活函数"""
        return 1.0 / (1.0 + np.exp(-np.clip(X, -500, 500)))

    def _sample(self, probs):
        """伯努利采样"""
        return (np.random.rand(*probs.shape) < probs).astype(float)

    def _train_rbm_layer(self, v0, n_hidden):
        """
        训练单层RBM

        参数:
            v0: 可见层数据
            n_hidden: 隐藏层单元数

        返回:
            W: 权重矩阵
            b_v: 可见层偏置
            b_h: 隐藏层偏置
        """
        n_visible = v0.shape[1]
        W = np.random.randn(n_visible, n_hidden) * np.sqrt(2.0 / (n_visible + n_hidden))
        b_v = np.zeros(n_visible)
        b_h = np.zeros(n_hidden)

        for iteration in range(self.rbm_iterations):
            # 正相位
            h0_probs = self._sigmoid(b_h + v0 @ W)
            h0_sample = self._sample(h0_probs)
            positive_grad = v0.T @ h0_probs

            # 负相位（k步Gibbs）
            vk = v0.copy()
            for _ in range(self.rbm_k):
                hk_probs = self._sigmoid(b_h + vk @ W)
                hk_sample = self._sample(hk_probs)
                vk_probs = self._sigmoid(b_v + hk_sample @ W.T)
                vk = self._sample(vk_probs)

            negative_grad = vk.T @ hk_probs

            # 更新
            W += self.rbm_learning_rate * (positive_grad - negative_grad) / v0.shape[0]
            b_h += self.rbm_learning_rate * (np.mean(h0_probs - hk_probs, axis=0))
            b_v += self.rbm_learning_rate * (np.mean(v0 - vk, axis=0))

        return W, b_v, b_h

    def pretrain(self, X):
        """
        逐层贪心预训练

        参数:
            X: 训练数据 (n_samples, n_features)
        """
        current_input = X
        self.rbms = []

        for i in range(len(self.layer_dims) - 1):
            print(f"预训练 RBM 层 {i + 1}: {self.layer_dims[i]} -> {self.layer_dims[i + 1]}")
            W, b_v, b_h = self._train_rbm_layer(
                current_input,
                self.layer_dims[i + 1]
            )
            self.rbms.append({'W': W, 'b_v': b_v, 'b_h': b_h})

            # 提取特征作为下一层输入
            h_probs = self._sigmoid(b_h + current_input @ W)
            current_input = h_probs

        print(f"预训练完成，共 {len(self.rbms)} 层")

    def _forward(self, X):
        """前向传播：计算各层激活"""
        activations = [X]
        current = X
        for rbm in self.rbms:
            h = self._sigmoid(rbm['b_h'] + current @ rbm['W'])
            activations.append(h)
            current = h
        return activations

    def _backward(self, X, y, learning_rate=0.1):
        """
        反向传播微调

        参数:
            X: 输入数据
            y: 标签（one-hot编码）
            learning_rate: 学习率
        """
        activations = self._forward(X)
        n_layers = len(activations)

        # 输出层误差
        output = activations[-1]
        delta = output - y

        # 反向传播误差
        deltas = [delta]
        for i in range(n_layers - 2, 0, -1):
            # 误差传递到下一层
            d_next = delta @ self.rbms[i]['W'].T
            # Sigmoid梯度
            dZ = d_next * activations[i] * (1 - activations[i])
            deltas.insert(0, dZ)
            delta = dZ

        # 更新权重
        for i in range(n_layers - 1):
            # 激活来自前一层
            a_prev = activations[i]
            d = deltas[i]

            # 更新RBM权重（添加微调修正）
            self.rbms[i]['W'] -= learning_rate * (a_prev.T @ d) / X.shape[0]
            self.rbms[i]['b_h'] -= learning_rate * np.mean(d, axis=0)

    def finetune(self, X, y, epochs=100, learning_rate=0.1):
        """
        监督微调

        参数:
            X: 训练数据
            y: 标签（one-hot编码）
            epochs: 微调轮数
            learning_rate: 学习率
        """
        n_classes = y.shape[1]

        # 初始化分类层
        last_dim = self.layer_dims[-1]
        self.classification_weights = np.random.randn(last_dim, n_classes) * np.sqrt(2.0 / last_dim)
        self.classification_bias = np.zeros(n_classes)

        for epoch in range(epochs):
            # 前向传播
            activations = self._forward(X)
            output = activations[-1]

            # 分类层
            logits = output @ self.classification_weights + self.classification_bias
            probs = self._softmax(logits)

            # 分类层误差
            delta = probs - y

            # 更新分类层
            self.classification_weights -= learning_rate * (output.T @ delta) / X.shape[0]
            self.classification_bias -= learning_rate * np.mean(delta, axis=0)

            # 反向传播到DBN
            delta = delta @ self.classification_weights.T
            deltas = [delta]

            for i in range(len(self.rbms) - 1, 0, -1):
                d_next = delta @ self.rbms[i]['W'].T
                dZ = d_next * activations[i] * (1 - activations[i])
                deltas.insert(0, dZ)
                delta = dZ

            # 更新DBN权重
            for i in range(len(self.rbms)):
                self.rbms[i]['W'] -= learning_rate * (activations[i].T @ deltas[i]) / X.shape[0]

            if (epoch + 1) % 20 == 0:
                predictions = np.argmax(probs, axis=1)
                labels = np.argmax(y, axis=1)
                accuracy = np.mean(predictions == labels)
                loss = -np.mean(y * np.log(probs + 1e-10))
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")

    def _softmax(self, X):
        """Softmax函数"""
        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))
        return exp_X / np.sum(exp_X, axis=1, keepdims=True)

    def predict_proba(self, X):
        """预测概率"""
        activations = self._forward(X)
        output = activations[-1]
        logits = output @ self.classification_weights + self.classification_bias
        return self._softmax(logits)

    def predict(self, X):
        """预测类别"""
        return np.argmax(self.predict_proba(X), axis=1)


if __name__ == "__main__":
    # 生成模拟数据
    np.random.seed(42)
    n_samples = 500
    n_features = 20
    n_classes = 3

    # 创建模拟数据集
    X = np.random.randn(n_samples, n_features)
    # 创建3个簇
    for i in range(n_classes):
        mask = (i * n_samples // n_classes <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // n_classes)
        X[mask] += np.array([1, 2, 0])[i] * np.random.randn(np.sum(mask), 1)

    # One-hot编码标签
    y = np.zeros((n_samples, n_classes))
    labels = np.zeros(n_samples, dtype=int)
    for i in range(n_classes):
        mask = (i * n_samples // n_classes <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // n_classes)
        y[mask, i] = 1
        labels[mask] = i

    # 归一化
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-10)

    # 训练DBN
    dbn = DeepBeliefNetwork(
        layer_dims=[n_features, 16, 8, n_classes],
        rbm_learning_rate=0.1,
        rbm_iterations=200,
        rbm_k=1
    )

    print("=" * 50)
    print("阶段1: 无监督预训练")
    print("=" * 50)
    dbn.pretrain(X)

    print("\n" + "=" * 50)
    print("阶段2: 监督微调")
    print("=" * 50)
    dbn.finetune(X, y, epochs=100, learning_rate=0.5)

    # 评估
    predictions = dbn.predict(X)
    accuracy = np.mean(predictions == labels)
    print(f"\n最终准确率: {accuracy:.4f}")

    # 测试推理
    X_test = X[:10]
    probs = dbn.predict_proba(X_test)
    print(f"测试预测概率形状: {probs.shape}")
