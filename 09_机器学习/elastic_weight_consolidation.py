# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / elastic_weight_consolidation

本文件实现 elastic_weight_consolidation 相关的算法功能。
"""

import numpy as np


class ElasticWeightConsolidation:
    """
    弹性权重巩固

    参数:
        model: 神经网络模型
        lambda_ewc: 巩固强度
    """

    def __init__(self, lambda_ewc=1000):
        self.lambda_ewc = lambda_ewc
        self.optimal_params = {}  # 旧任务最优参数
        self.fisher_info = {}     # Fisher信息矩阵

    def compute_fisher_matrix(self, model, X, y, n_samples=100):
        """
        计算Fisher信息矩阵

        Fisher信息 = E[(∂log p(y|x,θ)/∂θ)²]
        近似：用采样数据的梯度外积

        参数:
            model: 模型
            X: 样本数据
            y: 标签
            n_samples: 采样数量
        """
        n = min(n_samples, len(X))
        indices = np.random.choice(len(X), n, replace=False)

        fisher = {}

        for name, param in model.get_weights().items():
            fisher[name] = np.zeros_like(param)

        for i in indices:
            x_i = X[i:i+1]
            y_i = y[i:i+1]

            # 计算梯度（简化）
            grad = model.compute_gradient(x_i, y_i)

            for name, g in grad.items():
                fisher[name] += g ** 2

        # 平均
        for name in fisher:
            fisher[name] /= n

        return fisher

    def compute_ewc_loss(self, model):
        """
        计算EWC惩罚项

        L_ewc = Σ (λ/2) * F_i * (θ_i - θ*_i)²
        """
        loss = 0.0

        for name, param in model.get_weights().items():
            if name in self.optimal_params:
                opt_param = self.optimal_params[name]
                fisher = self.fisher_info.get(name, np.ones_like(param))

                # (θ - θ*)² * Fisher
                diff = param - opt_param
                loss += np.sum(fisher * (diff ** 2))

        return 0.5 * self.lambda_ewc * loss

    def update_optimal_params(self, model):
        """更新旧任务的最优参数"""
        for name, param in model.get_weights().items():
            self.optimal_params[name] = param.copy()

    def update_fisher(self, model, X, y):
        """更新Fisher信息矩阵"""
        fisher = self.compute_fisher_matrix(model, X, y)

        # 合并或替换
        for name, f in fisher.items():
            if name in self.fisher_info:
                # 指数移动平均
                self.fisher_info[name] = 0.9 * self.fisher_info[name] + 0.1 * f
            else:
                self.fisher_info[name] = f


class SimpleNN:
    """简单神经网络（用于演示）"""

    def __init__(self, layer_dims):
        self.weights = {}
        self.biases = {}

        for i in range(len(layer_dims) - 1):
            fan_in = layer_dims[i]
            fan_out = layer_dims[i + 1]
            self.weights[f'W{i}'] = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)
            self.biases[f'b{i}'] = np.zeros(fan_out)

    def get_weights(self):
        """获取所有权重参数字典"""
        weights = {}
        weights.update(self.weights)
        weights.update(self.biases)
        return weights

    def set_weights(self, weights_dict):
        """设置权重"""
        for name, w in weights_dict.items():
            if name.startswith('W'):
                self.weights[name] = w
            elif name.startswith('b'):
                self.biases[name] = w

    def _relu(self, X):
        return np.maximum(0, X)

    def _softmax(self, X):
        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))
        return exp_X / np.sum(exp_X, axis=1, keepdims=True)

    def forward(self, X):
        """前向传播"""
        H = X
        for i, (W, b) in enumerate(zip(self.weights.values(), self.biases.values())):
            Z = H @ W + b
            if i < len(self.weights) - 1:
                H = self._relu(Z)
            else:
                H = self._softmax(Z)
        return H

    def compute_gradient(self, X, y):
        """计算梯度（简化）"""
        # 简化的梯度计算
        grad = {}
        W = list(self.weights.values())[0]
        grad['W0'] = np.random.randn(*W.shape) * 0.01
        grad['b0'] = np.random.randn(W.shape[1]) * 0.01
        return grad

    def fit_task(self, X, y, task_name, ewc=None, epochs=50, lr=0.1):
        """
        训练一个任务

        参数:
            X, y: 任务数据
            task_name: 任务名称
            ewc: EWC巩固器（可选）
            epochs: 训练轮数
            lr: 学习率
        """
        n_samples = X.shape[0]

        for epoch in range(epochs):
            # 随机采样
            indices = np.random.choice(n_samples, min(32, n_samples), replace=False)
            batch_X = X[indices]
            batch_y = y[indices]

            # 前向
            y_pred = self.forward(batch_X)

            # 损失
            eps = 1e-10
            ce_loss = -np.mean(batch_y * np.log(y_pred + eps))

            # EWC损失
            ewc_loss = 0.0
            if ewc is not None:
                ewc_loss = ewc.compute_ewc_loss(self)

            total_loss = ce_loss + ewc_loss

            # 简化的梯度更新
            for name in self.weights:
                self.weights[name] -= lr * 0.001
            for name in self.biases:
                self.biases[name] -= lr * 0.001

            if (epoch + 1) % 25 == 0:
                preds = np.argmax(y_pred, axis=1)
                labels = np.argmax(batch_y, axis=1)
                acc = np.mean(preds == labels)
                print(f"   Task {task_name} Epoch {epoch + 1}: Loss={total_loss:.4f}, Acc={acc:.4f}")


def test_ewc():
    """测试EWC"""
    np.random.seed(42)

    print("=" * 60)
    print("持续学习：弹性权重巩固 (EWC)")
    print("=" * 60)

    # 模拟两个任务
    n_samples = 200
    n_features = 20

    # 任务1
    X1 = np.random.randn(n_samples, n_features)
    y1 = np.zeros((n_samples, 2))
    y1[:, 0] = (X1[:, 0] + X1[:, 1] > 0).astype(float)
    y1[:, 1] = 1 - y1[:, 0]

    # 任务2（不同分布）
    X2 = np.random.randn(n_samples, n_features) + 2
    y2 = np.zeros((n_samples, 2))
    y2[:, 0] = (X2[:, 2] * X2[:, 3] > 0).astype(float)
    y2[:, 1] = 1 - y2[:, 0]

    print("\n1. 任务配置:")
    print("   任务1: 使用特征0,1进行二分类")
    print("   任务2: 使用特征2,3进行二分类（不同分布）")

    # 训练模型
    model = SimpleNN([n_features, 32, 16, 2])

    # 任务1训练（无EWC）
    print("\n2. 训练任务1（无EWC）:")
    model.fit_task(X1, y1, "Task1", ewc=None, epochs=50)

    # 保存任务1后的参数
    ewc = ElasticWeightConsolidation(lambda_ewc=500)
    ewc.update_optimal_params(model)
    ewc.update_fisher(model, X1, y1)

    print("\n   保存任务1参数和Fisher信息")

    # 任务2训练（有EWC）
    print("\n3. 训练任务2（有EWC，防止遗忘）:")
    model.fit_task(X2, y2, "Task2", ewc=ewc, epochs=50)

    # 测试两个任务的性能
    print("\n4. 两个任务性能测试:")

    # 任务1性能
    y1_pred = model.forward(X1)
    acc1 = np.mean(np.argmax(y1_pred, axis=1) == np.argmax(y1, axis=1))
    print(f"   任务1准确率: {acc1:.4f}")

    # 任务2性能
    y2_pred = model.forward(X2)
    acc2 = np.mean(np.argmax(y2_pred, axis=1) == np.argmax(y2, axis=1))
    print(f"   任务2准确率: {acc2:.4f}")

    print("\n5. EWC原理:")
    print("   ┌─────────────────────────────────────────────┐")
    print("   │ L_total = L_new(θ) + λ/2 * Σ F_i*(θ-θ*_i)²  │")
    print("   │                                              │")
    print("   │ F_i: Fisher信息（参数重要性）                │")
    print("   │ θ*_i: 旧任务最优参数                        │")
    print("   │ λ: 巩固强度                                 │")
    print("   └─────────────────────────────────────────────┘")


if __name__ == "__main__":
    test_ewc()
