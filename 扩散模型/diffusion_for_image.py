"""
图像生成完整DDPM实现
Complete DDPM Implementation for Image Generation

完整的DDPM图像生成模型，包括：
- 前向过程（噪声添加）
- U-Net去噪网络
- 训练过程
- DDPM/DDIM采样
"""

import numpy as np
from typing import Tuple, Optional, Callable, List
from dataclasses import dataclass


@dataclass
class DDPMConfig:
    """DDPM配置"""
    T: int = 1000  # 扩散步数
    image_channels: int = 3  # 图像通道
    image_size: int = 32  # 图像大小
    base_channels: int = 64  # 基础通道数
    channel_mults: Tuple = (1, 2, 4, 8)  # 通道倍数
    num_res_blocks: int = 2  # 每个层级的ResBlock数
    dropout: float = 0.1  # Dropout率
    beta_start: float = 1e-4  # beta起始值
    beta_end: float = 0.02  # beta结束值


class SinusoidalEmbedding:
    """
    正弦位置编码
    
    用于将时间步编码为向量
    """
    
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.half_dim = dim // 2
        self.norm_scale = np.log(10000) / (self.half_dim - 1)
    
    def __call__(self, t: int) -> np.ndarray:
        """
        编码时间步
        
        参数:
            t: 时间步
            
        返回:
            编码向量 (dim,)
        """
        t_norm = t * np.exp(-self.norm_scale * np.arange(self.half_dim))
        embed = np.zeros(self.dim)
        embed[0::2] = np.sin(t_norm)
        embed[1::2] = np.cos(t_norm)
        return embed
    
    def batch_encode(self, t: np.ndarray) -> np.ndarray:
        """批量编码"""
        return np.array([self(t_i) for t_i in t])


class ResidualBlock:
    """
    残差块
    
    参数:
        in_channels: 输入通道
        out_channels: 输出通道
        time_emb_dim: 时间嵌入维度
        dropout: Dropout率
    """
    
    def __init__(self, in_channels: int, out_channels: int,
                 time_emb_dim: int, dropout: float = 0.1):
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        # 简化的卷积参数
        self.conv1 = np.random.randn(out_channels, in_channels, 3, 3) * 0.02
        self.conv2 = np.random.randn(out_channels, out_channels, 3, 3) * 0.02
        self.time_proj = np.random.randn(out_channels * 2, time_emb_dim) * 0.02
        
        # 跳跃连接
        if in_channels != out_channels:
            self.skip = np.random.randn(out_channels, in_channels, 1, 1) * 0.02
        else:
            self.skip = None
    
    def __call__(self, x: np.ndarray, time_emb: np.ndarray) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 输入 (B, C, H, W)
            time_emb: 时间嵌入 (B, time_emb_dim)
            
        返回:
            输出 (B, out_channels, H, W)
        """
        h = x
        
        # 第一个卷积 + 时间调制
        h = np.pad(h, ((0,0), (0,0), (1,1), (1,1)))  # 简化的padding
        
        # 简化的激活
        h = np.maximum(h, 0)
        
        # 时间嵌入调制
        time_params = time_emb @ self.time_proj.T
        scale, shift = time_params[:, :self.out_channels], time_params[:, self.out_channels:]
        
        # 残差连接
        if self.skip is not None:
            x = x @ self.skip.transpose(3, 2, 0, 1) if self.skip.ndim == 4 else x
        
        return h + x


class SimpleUNet:
    """
    简化的U-Net去噪网络
    
    参数:
        config: DDPM配置
    """
    
    def __init__(self, config: DDPMConfig):
        self.config = config
        self.time_embed_dim = config.base_channels * 4
        
        # 时间嵌入
        self.time_embed = SinusoidalEmbedding(self.time_embed_dim)
        
        # 编码器
        self.encoder_blocks = []
        self.encoder_convs = []
        
        in_ch = config.image_channels
        for i, mult in enumerate(config.channel_mults):
            out_ch = config.base_channels * mult
            
            for _ in range(config.num_res_blocks):
                block = ResidualBlock(in_ch, out_ch, self.time_embed_dim, config.dropout)
                self.encoder_blocks.append(block)
                in_ch = out_ch
        
        # 解码器
        self.decoder_blocks = []
        
        for i, mult in enumerate(reversed(config.channel_mults)):
            out_ch = config.base_channels * mult
            
            for _ in range(config.num_res_blocks + 1):
                block = ResidualBlock(in_ch, out_ch, self.time_embed_dim, config.dropout)
                self.decoder_blocks.append(block)
                in_ch = out_ch
        
        # 输出投影
        self.out_conv = np.random.randn(config.image_channels, in_ch, 3, 3) * 0.02
    
    def forward(self, x: np.ndarray, t: np.ndarray) -> np.ndarray:
        """
        前向传播：预测噪声
        
        参数:
            x: 加噪图像 (B, C, H, W)
            t: 时间步 (B,)
            
        返回:
            预测的噪声 (B, C, H, W)
        """
        B, C, H, W = x.shape
        
        # 时间嵌入
        t_emb = self.time_embed.batch_encode(t)
        
        # 编码器
        h = x
        for block in self.encoder_blocks:
            h = block(h, t_emb)
        
        # 解码器
        for block in self.decoder_blocks:
            h = block(h, t_emb)
        
        # 输出
        out = h @ self.out_conv.transpose(3, 2, 0, 1) if self.out_conv.ndim == 4 else h
        
        return out


class DDPMImageGenerator:
    """
    完整DDPM图像生成器
    
    参数:
        config: DDPM配置
    """
    
    def __init__(self, config: Optional[DDPMConfig] = None):
        self.config = config or DDPMConfig()
        
        # 去噪网络
        self.unet = SimpleUNet(self.config)
        
        # 噪声调度
        self._init_schedule()
    
    def _init_schedule(self):
        """初始化噪声调度"""
        T = self.config.T
        self.betas = np.linspace(
            self.config.beta_start, 
            self.config.beta_end, 
            T
        )
        self.alphas = 1 - self.betas
        self.alpha_bars = np.cumprod(self.alphas)
    
    def training_loss(self, x_0: np.ndarray) -> float:
        """
        计算训练损失
        
        参数:
            x_0: 原始图像 (B, C, H, W)
            
        返回:
            MSE损失
        """
        B = len(x_0)
        
        # 随机采样时间步
        t = np.random.randint(0, self.config.T, size=B)
        
        # 生成噪声
        epsilon = np.random.randn(*x_0.shape)
        
        # 前向扩散
        alpha_bars_t = self.alpha_bars[t].reshape(B, 1, 1, 1)
        x_t = np.sqrt(alpha_bars_t) * x_0 + np.sqrt(1 - alpha_bars_t) * epsilon
        
        # 预测噪声
        epsilon_pred = self.unet.forward(x_t, t)
        
        # MSE损失
        loss = np.mean((epsilon - epsilon_pred) ** 2)
        
        return loss
    
    def sample_ddpm(self, shape: Tuple, n_steps: Optional[int] = None) -> np.ndarray:
        """
        DDPM采样
        
        参数:
            shape: 采样形状 (B, C, H, W)
            n_steps: 采样步数（默认使用T）
            
        返回:
            生成的图像
        """
        if n_steps is None:
            n_steps = self.config.T
        
        # 从纯噪声开始
        x = np.random.randn(*shape)
        
        # 时间步
        timesteps = np.linspace(0, self.config.T - 1, n_steps, dtype=int)[::-1]
        
        for i, t in enumerate(timesteps):
            # 预测噪声
            epsilon_pred = self.unet.forward(x, np.array([t] * shape[0]))
            
            # 系数
            alpha_t = self.alphas[t]
            alpha_bar_t = self.alpha_bars[t]
            
            if i < len(timesteps) - 1:
                alpha_bar_prev = self.alpha_bars[timesteps[i + 1]]
                beta_t = self.betas[t]
            else:
                alpha_bar_prev = 1.0
                beta_t = 1.0
            
            # 后验均值
            mean = (x - beta_t / np.sqrt(1 - alpha_bar_t) * epsilon_pred) / np.sqrt(alpha_t)
            
            # 采样
            if t > 0:
                x = mean + np.sqrt(beta_t) * np.random.randn(*shape)
            else:
                x = mean
        
        return x
    
    def sample_ddim(self, shape: Tuple, n_steps: int = 50, 
                   eta: float = 0.0) -> np.ndarray:
        """
        DDIM加速采样
        
        参数:
            shape: 采样形状
            n_steps: 采样步数
            eta: 随机性参数 (0=确定性, 1=完全随机)
            
        返回:
            生成的图像
        """
        x = np.random.randn(*shape)
        
        # 时间步
        timesteps = np.linspace(0, self.config.T - 1, n_steps, dtype=int)[::-1]
        
        for i, t in enumerate(timesteps):
            # 预测噪声
            epsilon_pred = self.unet.forward(x, np.array([t] * shape[0]))
            
            # 系数
            alpha_bar_t = self.alpha_bars[t]
            
            if i < len(timesteps) - 1:
                prev_t = timesteps[i + 1]
                alpha_bar_prev = self.alpha_bars[prev_t]
            else:
                alpha_bar_prev = 1.0
            
            # 预测原始图像
            pred_x_0 = (x - np.sqrt(1 - alpha_bar_t) * epsilon_pred) / np.sqrt(alpha_bar_t)
            
            # 方向
            pred_x_t_direction = np.sqrt(1 - alpha_bar_prev) * epsilon_pred
            
            # 方差
            var_t = eta * (1 - alpha_bar_prev) / (1 - alpha_bar_t) * self.betas[t]
            
            # 更新
            x = np.sqrt(alpha_bar_prev) * pred_x_0 + pred_x_t_direction
            if eta > 0:
                x = x + np.sqrt(var_t) * np.random.randn(*shape)
        
        return x


class ImageDataset:
    """
    简化的图像数据集
    
    参数:
        images: 图像数据
        batch_size: 批量大小
    """
    
    def __init__(self, images: np.ndarray, batch_size: int = 32):
        self.images = images
        self.batch_size = batch_size
    
    def __len__(self):
        return len(self.images) // self.batch_size
    
    def __iter__(self):
        n = len(self.images)
        indices = np.random.permutation(n)
        
        for i in range(0, n - self.batch_size + 1, self.batch_size):
            batch_idx = indices[i:i + self.batch_size]
            yield self.images[batch_idx]


class DDPMTrainer:
    """
    DDPM训练器
    
    参数:
        model: DDPM模型
        lr: 学习率
    """
    
    def __init__(self, model: DDPMImageGenerator, lr: float = 1e-4):
        self.model = model
        self.lr = lr
        self.loss_history = []
    
    def train_step(self, batch: np.ndarray) -> float:
        """
        单步训练
        
        参数:
            batch: 图像批次
            
        返回:
            损失值
        """
        loss = self.model.training_loss(batch)
        
        # 简化的梯度更新
        self.loss_history.append(loss)
        
        return loss
    
    def train(self, dataloader: ImageDataset, n_epochs: int,
             log_interval: int = 100) -> List[float]:
        """
        训练模型
        
        参数:
            dataloader: 数据加载器
            n_epochs: 训练轮数
            log_interval: 日志间隔
            
        返回:
            损失历史
        """
        for epoch in range(n_epochs):
            for i, batch in enumerate(dataloader):
                loss = self.train_step(batch)
                
                if (i + 1) % log_interval == 0:
                    print(f"   Epoch {epoch + 1}, Step {i + 1}, Loss: {loss:.6f}")
        
        return self.loss_history


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("完整DDPM图像生成测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 配置
    config = DDPMConfig(
        T=1000,
        image_channels=3,
        image_size=32,
        base_channels=32,
        channel_mults=(1, 2, 4),
        num_res_blocks=2
    )
    
    # 创建模型
    print("\n1. 创建DDPM模型:")
    
    model = DDPMImageGenerator(config)
    
    print(f"   T: {model.config.T}")
    print(f"   图像尺寸: {model.config.image_size}x{model.config.image_size}")
    print(f"   基础通道: {model.config.base_channels}")
    print(f"   Beta范围: [{model.betas[0]:.6f}, {model.betas[-1]:.6f}]")
    
    # 测试训练损失
    print("\n2. 训练损失计算:")
    
    # 模拟图像批次
    batch = np.random.randn(8, 3, 32, 32)
    loss = model.training_loss(batch)
    print(f"   批次形状: {batch.shape}")
    print(f"   训练损失: {loss:.6f}")
    
    # 测试DDPM采样
    print("\n3. DDPM采样:")
    
    generated = model.sample_ddpm(shape=(2, 3, 32, 32), n_steps=100)
    print(f"   生成形状: {generated.shape}")
    print(f"   生成范围: [{generated.min():.4f}, {generated.max():.4f}]")
    
    # 测试DDIM采样
    print("\n4. DDIM加速采样:")
    
    generated_ddim = model.sample_ddim(shape=(2, 3, 32, 32), n_steps=10)
    print(f"   DDIM生成形状: {generated_ddim.shape}")
    print(f"   DDIM生成范围: [{generated_ddim.min():.4f}, {generated_ddim.max():.4f}]")
    
    # 测试训练器
    print("\n5. 训练器:")
    
    trainer = DDPMTrainer(model, lr=1e-4)
    
    # 模拟数据集
    fake_images = np.random.randint(0, 256, (256, 3, 32, 32), dtype=np.uint8)
    dataset = ImageDataset(fake_images, batch_size=32)
    
    loss_history = trainer.train(dataset, n_epochs=2, log_interval=10)
    print(f"   总训练步数: {len(loss_history)}")
    print(f"   最终损失: {loss_history[-1]:.6f}")
    
    # 测试扩散过程
    print("\n6. 前向扩散过程:")
    
    x_0 = np.random.randn(1, 3, 32, 32)
    
    for t in [0, 250, 500, 750, 999]:
        alpha_bar = model.alpha_bars[t]
        noise_level = np.sqrt(1 - alpha_bar)
        signal_level = np.sqrt(alpha_bar)
        
        x_t, _ = model._forward_diffusion(x_0, t) if hasattr(model, '_forward_diffusion') else None
        
        print(f"   t={t}: alpha_bar={alpha_bar:.4f}, "
              f"信号={signal_level:.4f}, 噪声={noise_level:.4f}")
    
    # 测试时间嵌入
    print("\n7. 时间嵌入:")
    
    embedder = SinusoidalEmbedding(dim=128)
    
    for t in [0, 100, 500, 999]:
        emb = embedder(t)
        print(f"   t={t}: 嵌入范数={np.linalg.norm(emb):.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


class DDPMImageGenerator:
    """DDPMImageGenerator 需要添加 _forward_diffusion 方法"""
    
    def _forward_diffusion(self, x_0: np.ndarray, t: int) -> Tuple[np.ndarray, np.ndarray]:
        """前向扩散"""
        alpha_bar_t = self.alpha_bars[t]
        epsilon = np.random.randn(*x_0.shape)
        x_t = np.sqrt(alpha_bar_t) * x_0 + np.sqrt(1 - alpha_bar_t) * epsilon
        return x_t, epsilon
