# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / autoencoder

本文件实现 autoencoder 相关的算法功能。
"""

import numpy as np


class Autoencoder:
    """
    标准自编码器
    
    参数:
        input_dim: 输入维度
        hidden_dims: 编码器各层维度列表
    """
    
    def __init__(self, input_dim, hidden_dims=[64, 32, 16]):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        
        # 构建编码器
        self.encoder_weights = []
        self.encoder_biases = []
        
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            self.encoder_weights.append(np.random.randn(prev_dim, hidden_dim) * np.sqrt(2.0 / prev_dim))
            self.encoder_biases.append(np.zeros(hidden_dim))
            prev_dim = hidden_dim
        
        # 编码器输出维度
        self.latent_dim = hidden_dims[-1]
        
        # 构建解码器（镜像结构）
        self.decoder_weights = []
        self.decoder_biases = []
        
        for hidden_dim in reversed(hidden_dims[:-1]):
            self.decoder_weights.append(np.random.randn(prev_dim, hidden_dim) * np.sqrt(2.0 / prev_dim))
            self.decoder_biases.append(np.zeros(hidden_dim))
            prev_dim = hidden_dim
        
        # 解码器输出层
        self.decoder_weights.append(np.random.randn(prev_dim, input_dim) * np.sqrt(2.0 / prev_dim))
        self.decoder_biases.append(np.zeros(input_dim))
    
    def encode(self, x):
        """编码"""
        h = x
        for i in range(len(self.encoder_weights)):
            h = h @ self.encoder_weights[i] + self.encoder_biases[i]
            h = np.maximum(0, h)  # ReLU激活
        return h
    
    def decode(self, z):
        """解码"""
        h = z
        for i in range(len(self.decoder_weights)):
            h = h @ self.decoder_weights[i] + self.decoder_biases[i]
            if i < len(self.decoder_weights) - 1:
                h = np.maximum(0, h)  # ReLU
            else:
                h = np.tanh(h)  # 输出归一化到[-1, 1]
        return h
    
    def forward(self, x):
        """前馈"""
        z = self.encode(x)
        x_recon = self.decode(z)
        return x_recon, z
    
    def reconstruction_loss(self, x, x_recon):
        """重构损失"""
        return np.mean((x - x_recon) ** 2)
    
    def train_step(self, x, lr=0.001):
        """简化的训练步骤"""
        # 前馈
        z = self.encode(x)
        x_recon = self.decode(z)
        
        # 重构损失
        loss = self.reconstruction_loss(x, x_recon)
        
        # 简化的梯度更新（实际应使用反向传播）
        error = x - x_recon
        for i in range(len(self.encoder_weights)):
            # 更新编码器
            grad_w = x.T @ error if i == 0 else z.T @ error
            self.encoder_weights[i] += lr * grad_w * 0.001
            self.encoder_biases[i] += lr * np.mean(error, axis=0)
        
        return loss


class DenoisingAutoencoder:
    """
    去噪自编码器
    
    通过对输入添加噪声并重构原始clean输入来学习鲁棒表示
    
    参数:
        input_dim: 输入维度
        hidden_dims: 隐藏层维度
        noise_level: 噪声强度
    """
    
    def __init__(self, input_dim, hidden_dims=[64, 32], noise_level=0.1):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.noise_level = noise_level
        
        # 共享自编码器
        self.autoencoder = Autoencoder(input_dim, hidden_dims)
    
    def add_noise(self, x):
        """添加噪声"""
        noise = np.random.randn(*x.shape) * self.noise_level
        x_noisy = x + noise
        return np.clip(x_noisy, 0, 1)  # 假设输入在[0,1]范围
    
    def forward(self, x, denoise=True):
        """前馈"""
        if denoise:
            x_noisy = self.add_noise(x)
        else:
            x_noisy = x
        
        x_recon, z = self.autoencoder.forward(x_noisy)
        return x_recon, z
    
    def train_step(self, x, lr=0.001):
        """训练步骤"""
        # 添加噪声
        x_noisy = self.add_noise(x)
        
        # 重构
        x_recon, z = self.autoencoder.forward(x_noisy)
        
        # 计算损失
        loss = self.autoencoder.reconstruction_loss(x, x_recon)
        
        return loss


class VariationalAutoencoder:
    """
    变分自编码器（VAE）
    
    参数:
        input_dim: 输入维度
        latent_dim: 潜在空间维度
        hidden_dims: 隐藏层维度
    """
    
    def __init__(self, input_dim, latent_dim=8, hidden_dims=[64, 32]):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dims = hidden_dims
        
        prev_dim = input_dim
        
        # 编码器
        self.enc_hidden_weights = []
        self.enc_hidden_biases = []
        
        for hidden_dim in hidden_dims:
            self.enc_hidden_weights.append(np.random.randn(prev_dim, hidden_dim) * np.sqrt(2.0 / prev_dim))
            self.enc_hidden_biases.append(np.zeros(hidden_dim))
            prev_dim = hidden_dim
        
        # 均值和对数方差网络
        self.fc_mu = np.random.randn(prev_dim, latent_dim) * 0.01
        self.b_mu = np.zeros(latent_dim)
        self.fc_logvar = np.random.randn(prev_dim, latent_dim) * 0.01
        self.b_logvar = np.zeros(latent_dim)
        
        # 解码器
        prev_dim = latent_dim
        self.dec_hidden_weights = []
        self.dec_hidden_biases = []
        
        for hidden_dim in reversed(hidden_dims):
            self.dec_hidden_weights.append(np.random.randn(prev_dim, hidden_dim) * np.sqrt(2.0 / prev_dim))
            self.dec_hidden_biases.append(np.zeros(hidden_dim))
            prev_dim = hidden_dim
        
        self.fc_out = np.random.randn(prev_dim, input_dim) * np.sqrt(2.0 / prev_dim)
        self.b_out = np.zeros(input_dim)
    
    def encode(self, x):
        """编码为均值和对数方差"""
        h = x
        for i in range(len(self.enc_hidden_weights)):
            h = h @ self.enc_hidden_weights[i] + self.enc_hidden_biases[i]
            h = np.maximum(0, h)
        
        mu = h @ self.fc_mu + self.b_mu
        logvar = h @ self.fc_logvar + self.b_logvar
        
        return mu, logvar
    
    def reparameterize(self, mu, logvar):
        """重参数化技巧"""
        std = np.exp(0.5 * logvar)
        eps = np.random.randn(*mu.shape)
        z = mu + std * eps
        return z
    
    def decode(self, z):
        """解码"""
        h = z
        for i in range(len(self.dec_hidden_weights)):
            h = h @ self.dec_hidden_weights[i] + self.dec_hidden_biases[i]
            h = np.maximum(0, h)
        
        x_recon = h @ self.fc_out + self.b_out
        x_recon = 1 / (1 + np.exp(-x_recon))  # Sigmoid（假设输入在[0,1]）
        
        return x_recon
    
    def forward(self, x):
        """前馈"""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        x_recon = self.decode(z)
        
        return x_recon, mu, logvar, z
    
    def loss(self, x, x_recon, mu, logvar, beta=1.0):
        """
        VAE损失
        
        loss = reconstruction_loss + beta * KL_divergence
        """
        # 重构损失（二进制交叉熵，假设输入是二值的）
        recon_loss = -np.mean(x * np.log(x_recon + 1e-8) + (1 - x) * np.log(1 - x_recon + 1e-8))
        
        # KL散度
        kl_loss = -0.5 * np.mean(1 + logvar - mu**2 - np.exp(logvar))
        
        return recon_loss + beta * kl_loss, recon_loss, kl_loss


if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("自编码器测试")
    print("=" * 55)
    
    # 创建数据
    input_dim = 100
    n_samples = 200
    
    # 生成高度结构化的数据（用于测试自编码器能否学习到结构）
    x = np.zeros((n_samples, input_dim))
    
    for i in range(n_samples):
        # 每个样本有3个激活的簇
        cluster1_start = np.random.randint(0, 20)
        cluster2_start = np.random.randint(40, 60)
        cluster3_start = np.random.randint(80, 95)
        
        x[i, cluster1_start:cluster1_start+10] = 1
        x[i, cluster2_start:cluster2_start+15] = 1
        x[i, cluster3_start:cluster3_start+5] = 1
    
    print(f"数据形状: {x.shape}")
    print(f"数据稀疏度: {1 - x.mean():.2%}")
    
    # 测试标准自编码器
    print("\n--- 标准自编码器 ---")
    ae = Autoencoder(input_dim=input_dim, hidden_dims=[64, 32, 16, 8])
    
    # 训练
    losses = []
    for epoch in range(100):
        loss = ae.train_step(x, lr=0.01)
        losses.append(loss)
    
    # 重构
    x_recon, z = ae.forward(x)
    final_loss = ae.reconstruction_loss(x, x_recon)
    
    print(f"初始损失: {losses[0]:.4f}")
    print(f"最终损失: {final_loss:.4f}")
    print(f"潜在维度: {z.shape[1]}")
    
    # 测试去噪自编码器
    print("\n--- 去噪自编码器 ---")
    dae = DenoisingAutoencoder(input_dim=input_dim, hidden_dims=[64, 32], noise_level=0.1)
    
    dae_losses = []
    for epoch in range(100):
        loss = dae.train_step(x, lr=0.01)
        dae_losses.append(loss)
    
    x_recon_dae, z_dae = dae.forward(x)
    print(f"去噪AE最终损失: {dae_losses[-1]:.4f}")
    
    # 测试VAE
    print("\n--- 变分自编码器 ---")
    vae = VariationalAutoencoder(input_dim=input_dim, latent_dim=8, hidden_dims=[32, 16])
    
    vae_losses = []
    for epoch in range(100):
        x_recon, mu, logvar, z = vae.forward(x)
        loss, recon, kl = vae.loss(x, x_recon, mu, logvar)
        vae_losses.append(loss)
        
        # 简化更新（实际需要反向传播）
        vae.fc_out += 0.001 * (x - x_recon) @ np.linalg.pinv(z)
    
    print(f"VAE最终损失: {vae_losses[-1]:.4f}")
    
    # 生成新样本
    print("\n--- 从VAE生成新样本 ---")
    # 从先验采样
    z_sample = np.random.randn(5, 8)
    x_generated = vae.decode(z_sample)
    
    print(f"生成样本形状: {x_generated.shape}")
    print(f"生成样本激活率: {x_generated.mean():.4f}")
    
    # 潜在空间插值
    print("\n--- 潜在空间插值 ---")
    z1, z2 = z[0], z[10]  # 两个样本的潜在表示
    
    print("在两个样本之间插值:")
    for alpha in [0.0, 0.25, 0.5, 0.75, 1.0]:
        z_interp = (1 - alpha) * z1 + alpha * z2
        x_interp = vae.decode(z_interp.reshape(1, -1))
        activation = np.sum(x_interp > 0.5) / input_dim
        print(f"  alpha={alpha:.2f}: 激活比例={activation:.4f}")
    
    # 压缩效率分析
    print("\n--- 压缩效率分析 ---")
    original_bits = input_dim * 8  # 假设浮点数8字节
    compressed_bits = z.shape[1] * 8 + 32 * 16 + 16 * 8  # 潜在+权重
    compression_ratio = original_bits / compressed_bits
    
    print(f"原始表示: {original_bits} bits")
    print(f"压缩表示: {compressed_bits} bits")
    print(f"压缩比: {compression_ratio:.2f}x")
    
    print("\n自编码器测试完成！")
