# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / sparse_autoencoder

本文件实现 sparse_autoencoder 相关的算法功能。
"""

import numpy as np


class SparseAutoencoder:
    """
    稀疏自编码器实现

    参数:
        input_dim: 输入维度
        latent_dim: 潜在空间维度（可大于input_dim）
        hidden_dims: 编码器隐藏层维度
        sparsity_param: 目标稀疏度ρ（默认0.05）
        beta: 稀疏惩罚项系数
        lam: L2正则化系数
    """

    def __init__(self, input_dim, latent_dim, hidden_dims=[256],
                 sparsity_param=0.05, beta=3.0, lam=0.001):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dims = hidden_dims
        self.sparsity_param = sparsity_param
        self.beta = beta
        self.lam = lam

        # 初始化权重
        dims = [input_dim] + hidden_dims + [latent_dim]
        self.weights = []
        self.biases = []
        for i in range(len(dims) - 1):
            w = np.random.randn(dims[i], dims[i + 1]) * np.sqrt(2.0 / dims[i])
            b = np.zeros(dims[i + 1])
            self.weights.append(w)
            self.biases.append(b)

        # 解码器（转置权重共享或独立权重）
        decode_dims = [latent_dim] + list(reversed(hidden_dims)) + [input_dim]
        self.decode_weights = []
        self.decode_biases = []
        for i in range(len(decode_dims) - 1):
            w = np.random.randn(decode_dims[i], decode_dims[i + 1]) * np.sqrt(2.0 / decode_dims[i])
            b = np.zeros(decode_dims[i + 1])
            self.decode_weights.append(w)
            self.decode_biases.append(b)

    def _sigmoid(self, Z):
        """Sigmoid激活函数"""
        return 1.0 / (1.0 + np.exp(-np.clip(Z, -500, 500)))

    def _sigmoid_grad(self, A):
        """Sigmoid梯度"""
        return A * (1 - A)

    def _relu(self, X):
        """ReLU激活函数"""
        return np.maximum(0, X)

    def _relu_grad(self, Z):
        """ReLU梯度"""
        return (Z > 0).astype(float)

    def _kl_divergence(self, rho_hat):
        """
        计算KL散度稀疏惩罚
        KL(ρ || ρ̂) = ρ log(ρ/ρ̂) + (1-ρ) log((1-ρ)/(1-ρ̂))
        """
        rho = self.sparsity_param
        # 数值稳定计算
        small_val = 1e-10
        rho_hat = np.clip(rho_hat, small_val, 1 - small_val)
        kl = rho * np.log(rho / rho_hat) + (1 - rho) * np.log((1 - rho) / (1 - rho_hat))
        return np.sum(kl)

    def _encode(self, X):
        """编码过程"""
        H = X
        caches = []
        for w, b in zip(self.weights, self.biases):
            Z = H @ w + b
            A = self._relu(Z)  # 使用ReLU
            caches.append((Z, A, H))
            H = A
        return H, caches

    def _decode(self, Z):
        """解码过程"""
        H = Z
        caches = []
        for w, b in zip(self.decode_weights, self.decode_biases):
            Z = H @ w + b
            A = self._sigmoid(Z)  # 输出层用sigmoid归一化到[0,1]
            caches.append((Z, A, H))
            H = A
        return H, caches

    def _forward(self, X):
        """前向传播"""
        latent, enc_cache = self._encode(X)
        reconstructed, dec_cache = self._decode(latent)
        return reconstructed, enc_cache, dec_cache

    def _compute_loss(self, reconstructed, X, enc_cache):
        """计算带稀疏惩罚的损失"""
        # 重建损失
        recon_loss = np.mean((reconstructed - X) ** 2)

        # 计算潜在层的平均激活率
        _, A_last, _ = enc_cache[-1]
        rho_hat = np.mean(A_last, axis=0)

        # 稀疏惩罚
        sparse_loss = self.beta * self._kl_divergence(rho_hat)

        # L2正则化
        reg_loss = 0.0
        for w in self.weights:
            reg_loss += np.sum(w ** 2)
        for w in self.decode_weights:
            reg_loss += np.sum(w ** 2)
        reg_loss = self.lam * reg_loss

        total_loss = recon_loss + sparse_loss + reg_loss
        return total_loss, recon_loss, sparse_loss

    def _backward(self, reconstructed, X, enc_cache, dec_cache):
        """反向传播"""
        m = X.shape[0]
        grads = {}

        # 重建误差梯度
        dZ = 2.0 * (reconstructed - X) / m

        # 解码器梯度
        for i in range(len(self.decode_weights) - 1, -1, -1):
            Z, A, H = dec_cache[i]
            dW = H.T @ dZ
            db = np.sum(dZ, axis=0)
            dH = dZ @ self.decode_weights[i].T
            if i > 0:
                dZ = dH * self._sigmoid_grad(A)
            else:
                dZ = dH * self._relu_grad(Z)
            grads[f'dec_w{i}'] = dW
            grads[f'dec_b{i}'] = db

        # 编码器梯度（含稀疏惩罚的额外梯度）
        for i in range(len(self.weights) - 1, -1, -1):
            Z, A, H = enc_cache[i + 1]
            dW = H.T @ dZ
            db = np.sum(dZ, axis=0)
            dH = dZ @ self.weights[i].T
            dZ = dH * self._relu_grad(Z)

            # 添加稀疏惩罚梯度
            if i == len(self.weights) - 1:
                rho_hat = np.mean(A, axis=0)
                rho = self.sparsity_param
                sparsity_grad = self.beta * (rho / np.clip(A, 1e-10, None) - (1 - rho) / np.clip(1 - A, 1e-10, None))
                sparsity_grad = np.mean(sparsity_grad, axis=0)
                dZ += sparsity_grad.reshape(-1, 1) * self._relu_grad(Z).T

            grads[f'enc_w{i}'] = dW
            grads[f'enc_b{i}'] = db

        return grads

    def fit(self, X, epochs=100, lr=0.001, batch_size=32):
        """
        训练稀疏自编码器

        参数:
            X: 训练数据 (n_samples, n_features)
            epochs: 训练轮数
            lr: 学习率
            batch_size: 批量大小
        """
        n_samples = X.shape[0]
        for epoch in range(epochs):
            indices = np.random.permutation(n_samples)
            epoch_loss = 0.0
            epoch_recon = 0.0

            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch = X[indices[start:end]]

                # 前向传播
                reconstructed, enc_cache, dec_cache = self._forward(batch)

                # 计算损失
                loss, recon_loss, sparse_loss = self._compute_loss(reconstructed, batch, enc_cache)
                epoch_loss += loss * (end - start)
                epoch_recon += recon_loss * (end - start)

                # 反向传播
                grads = self._backward(reconstructed, batch, enc_cache, dec_cache)

                # 更新权重
                for i in range(len(self.weights)):
                    self.weights[i] -= lr * grads[f'enc_w{i}']
                    self.biases[i] -= lr * grads[f'enc_b{i}']
                for i in range(len(self.decode_weights)):
                    self.decode_weights[i] -= lr * grads[f'dec_w{i}']
                    self.decode_biases[i] -= lr * grads[f'dec_b{i}']

            if (epoch + 1) % 20 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss / n_samples:.6f}, "
                      f"Recon: {epoch_recon / n_samples:.6f}, Sparse: {sparse_loss:.6f}")

    def encode(self, X):
        """返回潜在表示"""
        latent, _ = self._encode(X)
        return latent


if __name__ == "__main__":
    # 测试数据：使用不同区域的随机数据模拟稀疏特征
    np.random.seed(42)
    n_samples = 500
    n_features = 20

    # 创建具有稀疏激活模式的数据
    X = np.random.randn(n_samples, n_features)
    # 前5个特征只在20%的样本中激活
    mask = np.random.rand(n_samples, 5) > 0.8
    X[:,
    :5] = np.where(mask, np.random.randn(n_samples, 5) * 3, 0.0)

    # 训练稀疏自编码器
    sae = SparseAutoencoder(
        input_dim=n_features,
        latent_dim=15,
        hidden_dims=[32],
        sparsity_param=0.05,
        beta=3.0,
        lam=0.0001
    )
    sae.fit(X, epochs=100, lr=0.01, batch_size=32)

    # 提取特征并检查稀疏性
    latent = sae.encode(X)
    mean_activation = np.mean(latent, axis=0)
    print(f"\n潜在表示平均激活率: {mean_activation}")
    print(f"稀疏神经元数量 (>5% 激活): {np.sum(mean_activation > 0.05)}")
    print(f"高度稀疏神经元 (<2% 激活): {np.sum(mean_activation < 0.02)}")
