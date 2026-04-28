"""
潜在扩散模型（Latent Diffusion Model, LDM）
Latent Diffusion Model

LDM在潜在空间进行扩散，而不是直接在像素空间。
通过预训练的VAE将图像压缩到低维潜在空间，
大幅降低计算成本，同时保持高质量生成。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class VAEConfig:
    """
    VAE配置
    
    属性:
        latent_channels: 潜在空间通道数
        latent_size: 潜在空间大小
        encoder_hidden_dims: encoder隐藏层维度
        decoder_hidden_dims: decoder隐藏层维度
    """
    latent_channels: int = 4
    latent_size: int = 32
    encoder_hidden_dims: List[int] = None
    
    def __post_init__(self):
        if self.encoder_hidden_dims is None:
            self.encoder_hidden_dims = [128, 256, 512, 512]


class Encoder:
    """
    VAE编码器
    
    将图像压缩到潜在空间
    
    参数:
        in_channels: 输入通道
        latent_channels: 潜在空间通道
        hidden_dims: 隐藏层维度
    """
    
    def __init__(self, in_channels: int = 3, latent_channels: int = 4,
                 hidden_dims: List[int] = None):
        self.in_channels = in_channels
        self.latent_channels = latent_channels
        self.hidden_dims = hidden_dims or [128, 256, 512]
        
        # 简化的网络参数
        self._init_params()
    
    def _init_params(self):
        """初始化网络参数"""
        # 简化：使用随机权重模拟
        self.params = {
            'conv1': np.random.randn(64, self.in_channels, 3, 3) * 0.01,
            'conv2': np.random.randn(128, 64, 3, 3) * 0.01,
            'conv3': np.random.randn(256, 128, 3, 3) * 0.01,
            'mu': np.random.randn(self.latent_channels, 256, 3, 3) * 0.01,
            'log_var': np.random.randn(self.latent_channels, 256, 3, 3) * 0.01,
        }
    
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        前向传播
        
        参数:
            x: 输入图像 (B, C, H, W)
            
        返回:
            (mu, log_var) 潜在空间均值和对数方差
        """
        # 简化的编码过程
        # 实际应用中会经过多层卷积、ResNet块、下采样等
        
        B, C, H, W = x.shape
        
        # 模拟下采样：每层2x下采样
        latent_H = H // 8  # 假设4层下采样，每层2x
        latent_W = W // 8
        
        # 模拟中间表示
        h = np.random.randn(B, 256, latent_H, latent_W) * 0.1
        
        # 计算mu和log_var
        mu = np.random.randn(B, self.latent_channels, latent_H, latent_W) * 0.1
        log_var = np.random.randn(B, self.latent_channels, latent_H, latent_W) * 0.01
        
        return mu, log_var
    
    def reparameterize(self, mu: np.ndarray, log_var: np.ndarray) -> np.ndarray:
        """
        重参数化技巧
        
        z = mu + sigma * epsilon, epsilon ~ N(0, I)
        
        参数:
            mu: 均值
            log_var: 对数方差
            
        返回:
            潜在编码
        """
        std = np.exp(0.5 * log_var)
        epsilon = np.random.randn(*std.shape)
        return mu + std * epsilon


class Decoder:
    """
    VAE解码器
    
    从潜在空间重建图像
    
    参数:
        latent_channels: 潜在空间通道
        out_channels: 输出通道
        hidden_dims: 隐藏层维度
    """
    
    def __init__(self, latent_channels: int = 4, out_channels: int = 3,
                 hidden_dims: List[int] = None):
        self.latent_channels = latent_channels
        self.out_channels = out_channels
        self.hidden_dims = hidden_dims or [512, 256, 128]
        
        self._init_params()
    
    def _init_params(self):
        """初始化网络参数"""
        self.params = {
            'conv1': np.random.randn(256, self.latent_channels, 3, 3) * 0.01,
            'conv2': np.random.randn(128, 256, 3, 3) * 0.01,
            'conv3': np.random.randn(64, 128, 3, 3) * 0.01,
            'conv_out': np.random.randn(self.out_channels, 64, 3, 3) * 0.01,
        }
    
    def forward(self, z: np.ndarray) -> np.ndarray:
        """
        前向传播
        
        参数:
            z: 潜在编码 (B, latent_channels, H, W)
            
        返回:
            重建图像
        """
        # 简化的解码过程
        # 实际应用会经过多层反卷积、上采样、ResNet块等
        
        B, C, H, W = z.shape
        
        # 模拟上采样：恢复到原图大小（假设压缩了8x）
        out_H = H * 8
        out_W = W * 8
        
        # 简化的重建
        x_recon = np.random.randn(B, self.out_channels, out_H, out_W) * 0.1
        
        return x_recon


class VAE:
    """
    变分自编码器 (Variational Autoencoder)
    
    参数:
        config: VAE配置
    """
    
    def __init__(self, config: VAEConfig):
        self.config = config
        self.encoder = Encoder(
            in_channels=3,
            latent_channels=config.latent_channels
        )
        self.decoder = Decoder(
            latent_channels=config.latent_channels,
            out_channels=3
        )
    
    def encode(self, x: np.ndarray) -> np.ndarray:
        """
        编码图像到潜在空间
        
        参数:
            x: 输入图像
            
        返回:
            潜在编码
        """
        mu, log_var = self.encoder.forward(x)
        z = self.encoder.reparameterize(mu, log_var)
        return z
    
    def decode(self, z: np.ndarray) -> np.ndarray:
        """
        从潜在空间解码
        
        参数:
            z: 潜在编码
            
        返回:
            重建图像
        """
        return self.decoder.forward(z)
    
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        完整的前向传播
        
        参数:
            x: 输入图像
            
        返回:
            (重建图像, mu, log_var)
        """
        mu, log_var = self.encoder.forward(x)
        z = self.encoder.reparameterize(mu, log_var)
        x_recon = self.decoder.forward(z)
        
        return x_recon, mu, log_var
    
    def elbo_loss(self, x: np.ndarray, x_recon: np.ndarray,
                  mu: np.ndarray, log_var: np.ndarray) -> Tuple[float, float, float]:
        """
        计算ELBO损失
        
        L = L_recon + L_KL
        
        参数:
            x: 原始图像
            x_recon: 重建图像
            mu: 均值
            log_var: 对数方差
            
        返回:
            (总损失, 重建损失, KL散度)
        """
        # 重建损失（简化为MSE）
        recon_loss = np.mean((x - x_recon) ** 2)
        
        # KL散度：KL(N(mu, sigma) || N(0, I))
        kl_loss = -0.5 * np.mean(
            1 + log_var - mu**2 - np.exp(log_var)
        )
        
        total_loss = recon_loss + kl_loss
        
        return total_loss, recon_loss, kl_loss


class LatentDiffusionModel:
    """
    潜在扩散模型
    
    在VAE的潜在空间中进行扩散过程
    
    参数:
        vae: VAE模型
        diffusion_model: 扩散模型（U-Net等）
        T: 扩散步数
        schedule: 噪声调度
    """
    
    def __init__(self, vae: VAE, diffusion_model, T: int = 1000,
                 schedule_type: str = 'linear'):
        self.vae = vae
        self.diffusion_model = diffusion_model
        self.T = T
        self.schedule_type = schedule_type
        
        # 初始化调度
        self._init_schedule()
    
    def _init_schedule(self):
        """初始化噪声调度"""
        if self.schedule_type == 'linear':
            self.betas = np.linspace(1e-4, 0.02, self.T)
        elif self.schedule_type == 'cosine':
            steps = np.arange(self.T + 1)
            f_t = np.cos((steps / self.T + 0.008) / 1.008 * np.pi / 2) ** 2
            f_0 = f_t[0]
            alpha_bars = f_t / f_0
            self.betas = 1 - alpha_bars[1:] / alpha_bars[:-1]
            self.betas = np.clip(self.betas, 0, 0.999)
        
        self.alphas = 1 - self.betas
        self.alpha_bars = np.cumprod(self.alphas)
    
    def encode_to_latent(self, x: np.ndarray) -> np.ndarray:
        """
        将图像编码到潜在空间
        
        参数:
            x: 图像
            
        返回:
            潜在编码
        """
        return self.vae.encode(x)
    
    def decode_from_latent(self, z: np.ndarray) -> np.ndarray:
        """
        从潜在空间解码
        
        参数:
            z: 潜在编码
            
        返回:
            图像
        """
        return self.vae.decode(z)
    
    def forward_diffusion_latent(self, z: np.ndarray, t: int) -> np.ndarray:
        """
        在潜在空间进行前向扩散
        
        参数:
            z: 潜在编码
            t: 时间步
            
        返回:
            加噪潜在编码
        """
        alpha_bar_t = self.alpha_bars[t]
        
        epsilon = np.random.randn(*z.shape)
        z_t = np.sqrt(alpha_bar_t) * z + np.sqrt(1 - alpha_bar_t) * epsilon
        
        return z_t, epsilon
    
    def training_loss(self, x: np.ndarray) -> float:
        """
        计算训练损失
        
        参数:
            x: 原始图像
            
        返回:
            损失值
        """
        # 编码到潜在空间
        z_0 = self.encode_to_latent(x)
        
        # 随机采样时间步
        t = np.random.randint(0, self.T)
        
        # 前向扩散
        z_t, epsilon = self.forward_diffusion_latent(z_0, t)
        
        # 预测噪声（简化）
        epsilon_pred = self.diffusion_model(z_t, t)
        
        # MSE损失
        loss = np.mean((epsilon - epsilon_pred) ** 2)
        
        return loss
    
    def sample(self, shape: Tuple, 
               n_steps: int = 50) -> np.ndarray:
        """
        采样新图像
        
        参数:
            shape: 潜在空间形状 (B, C, H, W)
            n_steps: 采样步数
            
        返回:
            生成的图像
        """
        # 从纯噪声开始
        z_t = np.random.randn(*shape)
        
        # 时间步（用于DDIM加速）
        timesteps = np.linspace(0, self.T - 1, n_steps, dtype=int)[::-1]
        
        for i, t in enumerate(timesteps):
            # 预测噪声
            epsilon_pred = self.diffusion_model(z_t, t)
            
            # 一步去噪（简化）
            alpha_t = self.alphas[t]
            alpha_bar_t = self.alpha_bars[t]
            
            if i < len(timesteps) - 1:
                alpha_bar_prev = self.alpha_bars[timesteps[i + 1]]
            else:
                alpha_bar_prev = 1.0
            
            # DDIM更新
            z_t = np.sqrt(alpha_bar_prev) * (z_t - np.sqrt(1 - alpha_bar_t) * epsilon_pred) / np.sqrt(alpha_bar_t)
            z_t = z_t + np.sqrt(1 - alpha_bar_prev) * epsilon_pred * 0.1
        
        # 解码到像素空间
        x = self.decode_from_latent(z_t)
        
        return x


class CrossAttention:
    """
    交叉注意力机制（用于条件LDM）
    
    在潜在扩散模型中实现文本到图像的条件生成
    
    参数:
        dim: 潜在维度
        n_heads: 注意力头数
        context_dim: 上下文（文本）维度
    """
    
    def __init__(self, dim: int = 768, n_heads: int = 8, context_dim: int = 768):
        self.dim = dim
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.context_dim = context_dim
        
        # 简化的注意力参数
        self.to_q = np.random.randn(dim, dim) * 0.01
        self.to_k = np.random.randn(context_dim, dim) * 0.01
        self.to_v = np.random.randn(context_dim, dim) * 0.01
        self.to_out = np.random.randn(dim, dim) * 0.01
    
    def forward(self, x: np.ndarray, context: np.ndarray) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 潜在表示 (B, seq_len, dim)
            context: 上下文/文本嵌入 (B, context_seq_len, context_dim)
            
        返回:
            注意力输出
        """
        B, N, D = x.shape
        _, M, _ = context.shape
        
        # 计算Q, K, V
        Q = x @ self.to_q  # (B, N, D)
        K = context @ self.to_k  # (B, M, D)
        V = context @ self.to_v  # (B, M, D)
        
        # 简化的注意力计算
        # 实际应用中需要multi-head attention
        
        # 计算注意力权重
        attn = Q @ K.transpose(0, 2, 1) / np.sqrt(self.head_dim)  # (B, N, M)
        attn = np.exp(attn - np.max(attn, axis=-1, keepdims=True))
        attn = attn / np.sum(attn, axis=-1, keepdims=True)
        
        # 应用注意力
        out = attn @ V  # (B, N, D)
        
        return out @ self.to_out


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("潜在扩散模型(LDM)测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：VAE编解码
    print("\n1. VAE编解码:")
    
    config = VAEConfig(latent_channels=4, latent_size=32)
    vae = VAE(config)
    
    # 模拟图像
    x = np.random.randn(2, 3, 256, 256)
    
    # 编码
    z = vae.encode(x)
    print(f"   输入形状: {x.shape}")
    print(f"   潜在编码形状: {z.shape}")
    
    # 解码
    x_recon = vae.decode(z)
    print(f"   重建形状: {x_recon.shape}")
    
    # 测试2：ELBO损失
    print("\n2. ELBO损失计算:")
    
    x_recon, mu, log_var = vae.forward(x)
    
    total_loss, recon_loss, kl_loss = vae.elbo_loss(x, x_recon, mu, log_var)
    print(f"   总损失: {total_loss:.6f}")
    print(f"   重建损失: {recon_loss:.6f}")
    print(f"   KL散度: {kl_loss:.6f}")
    
    # 测试3：潜在扩散
    print("\n3. 潜在扩散模型:")
    
    # 模拟扩散模型
    class MockDiffusionModel:
        def __call__(self, z_t, t):
            return np.random.randn(*z_t.shape) * 0.1
    
    diffusion_model = MockDiffusionModel()
    
    ldm = LatentDiffusionModel(vae, diffusion_model, T=1000, schedule_type='linear')
    
    z_0 = np.random.randn(2, 4, 32, 32)
    t = 500
    
    z_t, epsilon = ldm.forward_diffusion_latent(z_0, t)
    print(f"   原始潜在编码形状: {z_0.shape}")
    print(f"   加噪后形状: {z_t.shape}")
    print(f"   时间步t={t}的alpha_bar: {ldm.alpha_bars[t]:.6f}")
    
    # 测试4：训练损失
    print("\n4. LDM训练损失:")
    
    x_batch = np.random.randn(4, 3, 256, 256)
    loss = ldm.training_loss(x_batch)
    print(f"   训练损失: {loss:.6f}")
    
    # 测试5：采样
    print("\n5. LDM图像采样:")
    
    latent_shape = (1, 4, 32, 32)
    x_generated = ldm.sample(latent_shape, n_steps=50)
    print(f"   生成图像形状: {x_generated.shape}")
    
    # 测试6：交叉注意力
    print("\n6. 交叉注意力机制:")
    
    cross_attn = CrossAttention(dim=768, n_heads=8, context_dim=768)
    
    # 潜在表示
    x = np.random.randn(2, 16, 768)  # (B, seq_len, dim)
    # 文本嵌入
    context = np.random.randn(2, 8, 768)  # (B, context_seq_len, dim)
    
    out = cross_attn(x, context)
    print(f"   潜在表示形状: {x.shape}")
    print(f"   文本嵌入形状: {context.shape}")
    print(f"   输出形状: {out.shape}")
    
    # 测试7：压缩比
    print("\n7. 空间压缩比:")
    
    input_size = 256 * 256 * 3
    latent_size = 32 * 32 * 4
    compression_ratio = input_size / latent_size
    
    print(f"   像素空间: {input_size:,} 维度")
    print(f"   潜在空间: {latent_size:,} 维度")
    print(f"   压缩比: {compression_ratio:.1f}x")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
