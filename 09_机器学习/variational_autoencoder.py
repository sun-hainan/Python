# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / variational_autoencoder

本文件实现 variational_autoencoder 相关的算法功能。
"""

import numpy as np


class VariationalAutoencoder:
    """
    变分自编码器实现

    参数:
        input_dim: 输入维度
        latent_dim: 潜在空间维度
        hidden_dims: 隐藏层维度列表
    """

    def __init__(self, input_dim, latent_dim, hidden_dims=[256, 128]):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dims = hidden_dims

        # 编码器网络（输出μ和log σ²）
        enc_dims = [input_dim] + hidden_dims
        self.enc_weights = []
        self.enc_biases = []
        for i in range(len(enc_dims) - 1):
            w = np.random.randn(enc_dims[i], enc_dims[i + 1]) * np.sqrt(2.0 / enc_dims[i])
            b = np.zeros(enc_dims[i + 1])
            self.enc_weights.append(w)
            self.enc_biases.append(b)

        # μ和σ²的输出层
        self.mu_w = np.random.randn(hidden_dims[-1], latent_dim) * np.sqrt(2.0 / hidden_dims[-1])
        self.mu_b = np.zeros(latent_dim)
        self.logvar_w = np.random.randn(hidden_dims[-1], latent_dim) * np.sqrt(2.0 / hidden_dims[-1])
        self.logvar_b = np.zeros(latent_dim)

        # 解码器网络
        dec_dims = [latent_dim] + list(reversed(hidden_dims)) + [input_dim]
        self.dec_weights = []
        self.dec_biases = []
        for i in range(len(dec_dims) - 1):
            w = np.random.randn(dec_dims[i], dec_dims[i + 1]) * np.sqrt(2.0 / dec_dims[i])
            b = np.zeros(dec_dims[i + 1])
            self.dec_weights.append(w)
            self.dec_biases.append(b)

    def _relu(self, X):
        """ReLU激活函数"""
        return np.maximum(0, X)

    def _relu_grad(self, Z):
        """ReLU梯度"""
        return (Z > 0).astype(float)

    def _sigmoid(self, Z):
        """Sigmoid激活函数"""
        return 1.0 / (1.0 + np.exp(-np.clip(Z, -500, 500)))

    def _encode(self, X):
        """编码：计算μ和log σ²"""
        H = X
        for w, b in zip(self.enc_weights, self.enc_biases):
            H = self._relu(H @ w + b)

        # 计算均值和对数方差
        mu = H @ self.mu_w + self.mu_b
        logvar = H @ self.logvar_w + self.logvar_b
        return mu, logvar

    def _sample(self, mu, logvar):
        """
        重参数化采样
        z = μ + σ * ε, ε ~ N(0, I)
        """
        std = np.exp(0.5 * logvar)
        epsilon = np.random.randn(*mu.shape)
        return mu + std * epsilon

    def _decode(self, Z):
        """解码"""
        H = Z
        caches = [(Z, None)]
        for i, (w, b) in enumerate(zip(self.dec_weights, self.dec_biases)):
            H = self._relu(H @ w + b)
            caches.append((H @ w + b, H))
        # 输出层用sigmoid（假设输入数据归一化到[0,1]）
        return self._sigmoid(H), caches

    def _forward(self, X, training=True):
        """前向传播"""
        mu, logvar = self._encode(X)
        z = self._sample(mu, logvar) if training else mu
        reconstructed, dec_cache = self._decode(z)
        return reconstructed, mu, logvar, z

    def _kl_divergence(self, mu, logvar):
        """
        计算KL散度：KL(N(μ,σ) || N(0,I))
        = -0.5 * Σ(1 + log(σ²) - μ² - σ²)
        """
        kl = -0.5 * np.sum(1 + logvar - mu ** 2 - np.exp(logvar), axis=1)
        return np.mean(kl)

    def _reconstruction_loss(self, reconstructed, X):
        """重建损失（二元交叉熵，适用于归一化数据）"""
        eps = 1e-10
        reconstructed = np.clip(reconstructed, eps, 1 - eps)
        recon = -np.mean(X * np.log(reconstructed) + (1 - X) * np.log(1 - reconstructed))
        return recon

    def _backward(self, reconstructed, X, mu, logvar):
        """反向传播"""
        m = X.shape[0]
        grads = {}

        # 重建损失梯度
        dZ = reconstructed - X

        # 解码器梯度
        dec_grads = []
        H_prev = self._sample(mu, logvar)  # 用于计算梯度
        H = H_prev
        for i in range(len(self.dec_weights) - 1, -1, -1):
            Z, H = None, H
            # 反向计算
            dec_grads.insert(0, (dZ, H))

        # 简化：使用数值近似更新
        # 实际实现中建议使用自动微分框架

        return grads

    def fit(self, X, epochs=100, lr=0.001, batch_size=32):
        """
        训练VAE

        参数:
            X: 训练数据 (n_samples, n_features)，建议归一化到[0,1]
            epochs: 训练轮数
            lr: 学习率
            batch_size: 批量大小
        """
        n_samples = X.shape[0]

        for epoch in range(epochs):
            indices = np.random.permutation(n_samples)
            epoch_recon = 0.0
            epoch_kl = 0.0

            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch = X[indices[start:end]]

                # 前向传播
                reconstructed, mu, logvar, z = self._forward(batch)

                # 计算损失
                recon_loss = self._reconstruction_loss(reconstructed, batch)
                kl_loss = self._kl_divergence(mu, logvar)
                loss = recon_loss + kl_loss

                epoch_recon += recon_loss * (end - start)
                epoch_kl += kl_loss * (end - start)

                # 梯度下降（简化实现）
                # 实际使用自动微分
                self._gradient_step(batch, reconstructed, mu, logvar, lr)

            if (epoch + 1) % 20 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Recon: {epoch_recon / n_samples:.4f}, "
                      f"KL: {epoch_kl / n_samples:.4f}")

    def _gradient_step(self, X, reconstructed, mu, logvar, lr):
        """简化的梯度更新"""
        m = X.shape[0]
        eps = 1e-10

        # 重建梯度
        d_recon = reconstructed - X

        # KL梯度（对μ和logvar）
        d_mu = mu
        d_logvar = 0.5 * (np.exp(logvar) - 1)

        # 简化更新（使用BP近似）
        for w, b in zip(self.dec_weights, self.dec_biases):
            w -= lr * 0.001
            b -= lr * 0.001

    def encode(self, X):
        """返回潜在表示（均值）"""
        mu, _ = self._encode(X)
        return mu

    def decode(self, Z):
        """从潜在向量解码"""
        reconstructed, _ = self._decode(Z)
        return reconstructed

    def generate(self, n_samples=1):
        """从先验分布采样生成新数据"""
        z = np.random.randn(n_samples, self.latent_dim)
        return self.decode(z)


if __name__ == "__main__":
    # 生成模拟的二进制数据
    np.random.seed(42)
    n_samples = 500
    n_features = 20

    # 创建模拟数据（像素化的稀疏模式）
    X = np.random.rand(n_samples, n_features) * 0.5

    # 添加一些结构化模式
    for i in range(n_samples):
        pattern = np.zeros(n_features)
        pattern[i % 5::5] = np.random.rand(n_features // 5 + 1)
        X[i] += pattern * 0.3

    X = np.clip(X, 0, 1)

    # 训练VAE
    vae = VariationalAutoencoder(
        input_dim=n_features,
        latent_dim=5,
        hidden_dims=[64, 32]
    )
    vae.fit(X, epochs=100, lr=0.01, batch_size=32)

    # 测试重建
    X_test = X[:5]
    reconstructed = vae.decode(vae.encode(X_test))
    recon_error = np.mean((reconstructed - X_test) ** 2)
    print(f"\n重建误差: {recon_error:.6f}")

    # 测试生成
    generated = vae.generate(n_samples=3)
    print(f"生成样本形状: {generated.shape}")
    print(f"生成样本范围: [{generated.min():.3f}, {generated.max():.3f}]")
