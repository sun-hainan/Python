# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / gradient_centralization

本文件实现 gradient_centralization 相关的算法功能。
"""

import numpy as np


class GradientCentralization:
    """
    梯度中心化优化器装饰器

    用法：
        optimizer = SGD(...)
        gc_optimizer = GradientCentralization(optimizer)
    """

    def __init__(self, optimizer):
        self.optimizer = optimizer

    def step(self, weights, grads):
        """
        带梯度中心化的参数更新

        参数:
            weights: 权重字典 {name: array}
            grads: 梯度字典 {name: array}
        """
        # 中心化梯度
        centered_grads = {}
        for name, grad in grads.items():
            centered_grads[name] = grad - np.mean(grad)

        # 调用原始优化器
        self.optimizer.step(weights, centered_grads)


class GCSGD:
    """
    带梯度中心化的SGD

    参数:
        lr: 学习率
        momentum: 动量系数
        weight_decay: 权重衰减
    """

    def __init__(self, lr=0.01, momentum=0.9, weight_decay=0.0):
        self.lr = lr
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.velocity = {}

    def step(self, weights, grads):
        """
        更新权重（含梯度中心化）

        参数:
            weights: 权重字典
            grads: 梯度字典
        """
        for name, W in weights.items():
            # 中心化梯度
            grad = grads[name]
            grad_centered = grad - np.mean(grad)

            # 动量
            if name not in self.velocity:
                self.velocity[name] = np.zeros_like(W)

            v = self.momentum * self.velocity[name] - self.lr * grad_centered

            # 权重衰减
            if self.weight_decay > 0:
                v -= self.lr * self.weight_decay * W

            self.velocity[name] = v
            weights[name] = W + v


class GCAdam:
    """
    带梯度中心化的Adam

    参数:
        lr: 学习率
        beta1: 一阶矩估计衰减
        beta2: 二阶矩估计衰减
        eps: 数值稳定项
    """

    def __init__(self, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = {}  # 一阶矩
        self.v = {}  # 二阶矩
        self.t = 0   # 时间步

    def step(self, weights, grads):
        """更新权重（含梯度中心化）"""
        self.t += 1

        for name, W in weights.items():
            grad = grads[name]

            # 梯度中心化
            grad_centered = grad - np.mean(grad)

            # 初始化 moments
            if name not in self.m:
                self.m[name] = np.zeros_like(W)
                self.v[name] = np.zeros_like(W)

            # 更新 moments
            self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad_centered
            self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * (grad_centered ** 2)

            # 偏差校正
            m_hat = self.m[name] / (1 - self.beta1 ** self.t)
            v_hat = self.v[name] / (1 - self.beta2 ** self.t)

            # 更新
            weights[name] = W - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class SimpleNeuralNetworkGC:
    """
    使用梯度中心化的神经网络示例
    """

    def __init__(self, layer_dims, use_gc=True, lr=0.01):
        self.layer_dims = layer_dims
        self.use_gc = use_gc
        self.lr = lr

        # 初始化权重
        self.weights = []
        self.biases = []
        for i in range(len(layer_dims) - 1):
            fan_in = layer_dims[i]
            fan_out = layer_dims[i + 1]
            W = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)
            b = np.zeros(fan_out)
            self.weights.append(W)
            self.biases.append(b)

        # 优化器
        if use_gc:
            self.optimizer = GCSGD(lr=lr, momentum=0.9)
        else:
            self.optimizer = GCSGD(lr=lr, momentum=0.9)  # 不用GC的版本

    def _relu(self, X):
        return np.maximum(0, X)

    def _relu_grad(self, Z):
        return (Z > 0).astype(float)

    def _softmax(self, X):
        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))
        return exp_X / np.sum(exp_X, axis=1, keepdims=True)

    def _forward(self, X):
        caches = []
        H = X
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            Z = H @ W + b
            caches.append((Z, H))
            if i < len(self.weights) - 1:
                H = self._relu(Z)
            else:
                H = self._softmax(Z)
        return H, caches

    def _backward(self, y_pred, y_true, caches):
        m = y_pred.shape[0]
        grads = {'W': [], 'b': []}

        dZ = y_pred - y_true
        for i in range(len(self.weights) - 1, -1, -1):
            Z, H = caches[i]

            dW = H.T @ dZ / m
            db = np.sum(dZ, axis=0) / m

            grads['W'].insert(0, dW)
            grads['b'].insert(0, db)

            if i > 0:
                dH = dZ @ self.weights[i].T
                dZ = dH * self._relu_grad(Z)

        return grads

    def fit(self, X, y, epochs=100, batch_size=32):
        """训练"""
        n_samples = X.shape[0]

        for epoch in range(epochs):
            indices = np.random.permutation(n_samples)
            epoch_loss = 0.0

            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch_X = X[indices[start:end]]
                batch_y = y[indices[start:end]]

                # 前向
                y_pred, caches = self._forward(batch_X)

                # 损失
                eps = 1e-10
                loss = -np.mean(batch_y * np.log(y_pred + eps))
                epoch_loss += loss * (end - start)

                # 反向
                grads = self._backward(y_pred, batch_y, caches)

                # 更新（梯度中心化在优化器内实现）
                grad_dict = {f'W{i}': grads['W'][i] for i in range(len(self.weights))}
                w_dict = {f'W{i}': self.weights[i] for i in range(len(self.weights))}

                self.optimizer.step(w_dict, grad_dict)

                # 同步回来
                for i in range(len(self.weights)):
                    self.weights[i] = w_dict[f'W{i}']

            if (epoch + 1) % 20 == 0:
                preds = np.argmax(self._forward(X)[0], axis=1)
                labels = np.argmax(y, axis=1)
                acc = np.mean(preds == labels)
                print(f"Epoch {epoch + 1}, Loss: {epoch_loss/n_samples:.4f}, Acc: {acc:.4f}")


def compare_gc_vs_no_gc():
    """对比有/无梯度中心化的效果"""
    np.random.seed(42)

    # 生成数据
    n_samples = 300
    n_features = 20
    n_classes = 3

    X = np.random.randn(n_samples, n_features)
    for i in range(n_classes):
        mask = (i * n_samples // n_classes <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // n_classes)
        X[mask] += [1, 2, 0][i]

    y = np.zeros((n_samples, n_classes))
    labels = np.zeros(n_samples, dtype=int)
    for i in range(n_classes):
        mask = (i * n_samples // n_classes <= np.arange(n_samples)) & (np.arange(n_samples) < (i + 1) * n_samples // n_classes)
        y[mask, i] = 1
        labels[mask] = i

    X = (X - X.mean(0)) / (X.std(0) + 1e-10)

    print("=" * 60)
    print("梯度中心化效果对比")
    print("=" * 60)

    print("\n1. 无梯度中心化:")
    model_no_gc = SimpleNeuralNetworkGC([n_features, 32, 16, n_classes], use_gc=False, lr=0.1)
    model_no_gc.fit(X, y, epochs=100, batch_size=32)

    print("\n2. 有梯度中心化:")
    model_gc = SimpleNeuralNetworkGC([n_features, 32, 16, n_classes], use_gc=True, lr=0.1)
    model_gc.fit(X, y, epochs=100, batch_size=32)

    print("\n3. 梯度统计对比:")
    # 计算几个batch的梯度
    test_X = X[:32]
    test_y = y[:32]

    # 无GC
    _, caches = model_no_gc._forward(test_X)
    _, grads = model_no_gc._backward(model_no_gc._forward(test_X)[0], test_y, caches)
    grad_no_gc = grads['W'][-1]
    print(f"  无GC - 梯度均值: {np.mean(grad_no_gc):.6f}, 标准差: {np.std(grad_no_gc):.6f}")

    # 有GC
    _, caches = model_gc._forward(test_X)
    _, grads = model_gc._backward(model_gc._forward(test_X)[0], test_y, caches)
    grad_gc = grads['W'][-1]
    grad_gc_centered = grad_gc - np.mean(grad_gc)
    print(f"  有GC - 梯度均值: {np.mean(grad_gc_centered):.6f}, 标准差: {np.std(grad_gc_centered):.6f}")


if __name__ == "__main__":
    compare_gc_vs_no_gc()
