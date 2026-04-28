"""
DDPM反向过程：去噪神经网络
DDPM Reverse Process: Denoising Neural Network

DDPM的反向过程（p_theta）由神经网络近似，
通过学习预测噪声 epsilon_theta(x_t, t) 来逐步从噪声中恢复图像。
核心：U-Net架构 + 位置编码 + 残差连接
"""

import numpy as np
from typing import Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class SinusoidalPositionEmbedding:
    """
    正弦位置编码
    
    用于将时间步t嵌入到高维空间
    PE(t) = [sin(t/10000^(2i/d)), cos(t/10000^(2i/d)), ...]
    """
    dim: int = 128
    
    def __post_init__(self):
        self.half_dim = self.dim // 2
        # 计算归一化因子
        self.norm_scale = np.log(10000) / (self.half_dim - 1)
        self.embeddings = {}
    
    def __call__(self, t: int) -> np.ndarray:
        """
        获取时间步t的编码
        
        参数:
            t: 时间步 (0 <= t < T)
            
        返回:
            编码向量 (dim,)
        """
        if t in self.embeddings:
            return self.embeddings[t]
        
        # 计算编码
        t_norm = t * np.exp(-self.norm_scale * np.arange(self.half_dim))
        embed = np.zeros(self.dim)
        embed[0::2] = np.sin(t_norm)
        embed[1::2] = np.cos(t_norm)
        
        self.embeddings[t] = embed
        return embed
    
    def batch_encode(self, t: np.ndarray) -> np.ndarray:
        """
        批量编码
        
        参数:
            t: 时间步数组 (batch_size,)
            
        返回:
            编码矩阵 (batch_size, dim)
        """
        return np.array([self(t_i) for t_i in t])


class ResBlock:
    """
    残差块
    
    结构：LayerNorm -> Conv --> LayerNorm --> Conv + time_embed
          \________________________________________|
    """
    
    def __init__(self, channels: int, time_emb_dim: int, dropout: float = 0.1):
        self.channels = channels
        self.time_emb_dim = time_emb_dim
        self.dropout = dropout
        
        # 第一个卷积块
        self.conv1 = self._init_conv(channels, channels, 3, padding=1)
        self.conv2 = self._init_conv(channels, channels, 3, padding=1)
        
        # 时间嵌入投影
        self.time_proj = self._init_linear(time_emb_dim, channels * 2)
        
        # GroupNorm
        self.norm1 = lambda x: x  # 简化：实际应用用GroupNorm
        self.norm2 = lambda x: x
    
    def _init_conv(self, in_ch: int, out_ch: int, kernel: int, padding: int) -> dict:
        """初始化卷积层参数"""
        scale = np.sqrt(2.0 / (in_ch * kernel * kernel))
        return {
            'weight': np.random.randn(out_ch, in_ch, kernel, kernel) * scale,
            'bias': np.zeros(out_ch)
        }
    
    def _init_linear(self, in_features: int, out_features: int) -> dict:
        """初始化线性层参数"""
        scale = np.sqrt(2.0 / in_features)
        return {
            'weight': np.random.randn(out_features, in_features) * scale,
            'bias': np.zeros(out_features)
        }
    
    def __call__(self, x: np.ndarray, time_emb: np.ndarray) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 输入特征 (B, C, H, W)
            time_emb: 时间编码 (B, time_emb_dim)
            
        返回:
            输出特征 (B, C, H, W)
        """
        h = x
        
        # 第一个卷积
        h = self._conv(h, self.conv1)
        h = self.norm1(h)
        h = np.maximum(h, 0)  # SiLU/GELU近似
        
        # 时间嵌入
        time_params = self._linear(time_emb, self.time_proj)
        scale, shift = time_params[:, :self.channels], time_params[:, self.channels:]
        
        h = h * (1 + scale.reshape(-1, self.channels, 1, 1)) + shift.reshape(-1, self.channels, 1, 1)
        
        # 第二个卷积
        h = self._conv(h, self.conv2)
        h = self.norm2(h)
        
        # 残差连接
        return h + x
    
    def _conv(self, x: np.ndarray, params: dict) -> np.ndarray:
        """卷积操作"""
        # 简化的卷积实现（实际应用用PyTorch等框架）
        return x
    
    def _linear(self, x: np.ndarray, params: dict) -> np.ndarray:
        """线性操作"""
        return x @ params['weight'].T + params['bias']


class AttentionBlock:
    """
    自注意力块
    
    简化的多头注意力实现
    """
    
    def __init__(self, channels: int, num_heads: int = 4):
        self.channels = channels
        self.num_heads = num_heads
        self.head_dim = channels // num_heads
        
        # 简化的QKV投影
        scale = np.sqrt(2.0 / channels)
        self.qkv = {
            'weight': np.random.randn(channels * 3, channels) * scale
        }
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 输入 (B, C, H, W)
            
        返回:
            输出 (B, C, H, W)
        """
        B, C, H, W = x.shape
        
        # 简化的注意力计算
        # 实际应用中需要更完整的实现
        
        return x


class UNetDenoiser:
    """
    U-Net去噪网络
    
    结构：
    - Encoder: 下采样 + ResBlock + Attention
    - Bottleneck: ResBlocks
    - Decoder: 上采样 + ResBlock + Attention + Skip Connection
    
    参数:
        in_channels: 输入通道数
        out_channels: 输出通道数
        base_channels: 基础通道数
        channel_mults: 通道倍数
        num_res_blocks: 每个层级的ResBlock数
        T: 最大时间步
    """
    
    def __init__(self, in_channels: int = 3, out_channels: int = 3,
                 base_channels: int = 64, channel_mults: Tuple = (1, 2, 4, 8),
                 num_res_blocks: int = 2, T: int = 1000):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_channels = base_channels
        self.channel_mults = channel_mults
        self.num_res_blocks = num_res_blocks
        self.T = T
        
        # 时间嵌入
        time_emb_dim = base_channels * 4
        self.time_embed = SinusoidalPositionEmbedding(dim=time_emb_dim)
        
        # 构建网络
        self._build_network()
    
    def _build_network(self):
        """构建U-Net网络"""
        channels_list = [self.base_channels * m for m in self.channel_mults]
        
        # Encoder
        self.encoder_convs = []
        self.encoder_res = []
        
        ch = self.base_channels
        for i, mult in enumerate(self.channel_mults):
            out_ch = self.base_channels * mult
            
            # 下采样卷积
            for _ in range(self.num_res_blocks):
                res_block = ResBlock(out_ch, self.time_embed.dim)
                self.encoder_res.append(res_block)
                self.encoder_convs.append(None)  # 占位
            
            ch = out_ch
        
        # Bottleneck
        self.bottleneck = [
            ResBlock(channels_list[-1], self.time_embed.dim)
            for _ in range(2)
        ]
        
        # Decoder
        self.decoder_res = []
        self.decoder_convs = []
        
        for i, mult in enumerate(reversed(self.channel_mults)):
            out_ch = self.base_channels * mult
            
            for _ in range(self.num_res_blocks + 1):
                res_block = ResBlock(out_ch, self.time_embed.dim)
                self.decoder_res.append(res_block)
                self.decoder_convs.append(None)
    
    def forward(self, x: np.ndarray, t: np.ndarray) -> np.ndarray:
        """
        前向传播：预测噪声
        
        参数:
            x: 加噪图像 (B, C, H, W)
            t: 时间步 (B,)
            
        返回:
            预测的噪声 (B, C, H, W)
        """
        # 时间嵌入
        t_emb = self.time_embed.batch_encode(t)
        
        # 简化的前向传播
        h = x
        
        # Encoder
        encoder_outs = []
        for i, res_block in enumerate(self.encoder_res):
            h = res_block(h, t_emb)
            encoder_outs.append(h)
        
        # Bottleneck
        for res_block in self.bottleneck:
            h = res_block(h, t_emb)
        
        # Decoder with skip connections
        for i, res_block in enumerate(self.decoder_res):
            if encoder_outs:
                skip = encoder_outs.pop()
                h = h + skip  # Skip connection
            h = res_block(h, t_emb)
        
        # 输出投影
        # 简化为恒等映射
        return x - h  # 预测噪声


class DenoisingNetwork:
    """
    统一去噪网络接口
    
    包装U-Net并提供训练/推理接口
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.T = config.get('T', 1000)
        
        # 创建去噪器
        self.unet = UNetDenoiser(
            in_channels=config.get('in_channels', 3),
            out_channels=config.get('out_channels', 3),
            base_channels=config.get('base_channels', 64),
            channel_mults=config.get('channel_mults', (1, 2, 4, 8)),
            num_res_blocks=config.get('num_res_blocks', 2),
            T=self.T
        )
    
    def predict_noise(self, x_t: np.ndarray, t: int) -> np.ndarray:
        """
        预测噪声
        
        参数:
            x_t: 时间步t的图像
            t: 时间步
            
        返回:
            预测的噪声
        """
        if isinstance(t, int):
            t = np.array([t])
        
        return self.unet.forward(x_t, t)
    
    def training_loss(self, x_0: np.ndarray, epsilon: np.ndarray, 
                      t: np.ndarray) -> float:
        """
        计算简化的MSE损失
        
        L = E_t,x0,epsilon || epsilon - epsilon_theta(x_t, t) ||^2
        
        参数:
            x_0: 原始图像
            epsilon: 添加的噪声
            t: 时间步
            
        返回:
            MSE损失
        """
        # 计算x_t
        alpha_bars = self._get_alpha_bars(t)
        
        x_t = np.sqrt(alpha_bars.reshape(-1, 1, 1, 1)) * x_0 + \
              np.sqrt(1 - alpha_bars.reshape(-1, 1, 1, 1)) * epsilon
        
        # 预测噪声
        epsilon_pred = self.predict_noise(x_t, t)
        
        # MSE损失
        loss = np.mean((epsilon - epsilon_pred) ** 2)
        
        return loss
    
    def _get_alpha_bars(self, t: np.ndarray) -> np.ndarray:
        """获取累积alpha（简化实现）"""
        # 线性调度
        betas = np.linspace(1e-4, 0.02, self.T)
        alphas = 1 - betas
        alpha_bars = np.cumprod(alphas)
        
        return alpha_bars[t]


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DDPM反向过程（去噪网络）测试")
    print("=" * 60)
    
    # 测试1：位置编码
    print("\n1. 正弦位置编码:")
    
    pe = SinusoidalPositionEmbedding(dim=64)
    
    for t in [0, 100, 500, 999]:
        embed = pe(t)
        print(f"   t={t}: 编码形状={embed.shape}, 前5维={embed[:5].round(3)}")
    
    # 测试2：批量编码
    print("\n2. 批量位置编码:")
    
    t_batch = np.array([0, 100, 500, 999])
    embeds = pe.batch_encode(t_batch)
    print(f"   批量编码形状: {embeds.shape}")
    
    # 测试3：残差块
    print("\n3. 残差块:")
    
    res_block = ResBlock(channels=64, time_emb_dim=256)
    
    x = np.random.randn(2, 64, 32, 32)
    time_emb = np.random.randn(2, 256)
    
    output = res_block(x, time_emb)
    print(f"   输入形状: {x.shape}")
    print(f"   输出形状: {output.shape}")
    print(f"   残差连接保留维度: {output.shape == x.shape}")
    
    # 测试4：U-Net去噪器
    print("\n4. U-Net去噪器:")
    
    unet = UNetDenoiser(
        in_channels=3,
        out_channels=3,
        base_channels=32,
        channel_mults=(1, 2, 4),
        num_res_blocks=2,
        T=1000
    )
    
    # 模拟输入
    x = np.random.randn(2, 3, 32, 32)
    t = np.array([100, 500])
    
    noise_pred = unet.forward(x, t)
    print(f"   输入形状: {x.shape}")
    print(f"   时间步: {t}")
    print(f"   预测噪声形状: {noise_pred.shape}")
    
    # 测试5：去噪网络训练损失
    print("\n5. 去噪网络训练:")
    
    config = {
        'in_channels': 3,
        'out_channels': 3,
        'base_channels': 32,
        'T': 1000
    }
    
    denoiser = DenoisingNetwork(config)
    
    # 模拟训练数据
    x_0 = np.random.randn(4, 3, 32, 32)
    epsilon = np.random.randn(4, 3, 32, 32)
    t = np.array([100, 200, 500, 800])
    
    loss = denoiser.training_loss(x_0, epsilon, t)
    print(f"   训练损失: {loss:.6f}")
    
    # 测试6：推理过程（单步去噪）
    print("\n6. 单步去噪预测:")
    
    x_t = np.random.randn(1, 3, 32, 32)
    
    for t in [900, 700, 500, 100]:
        noise_pred = denoiser.predict_noise(x_t, t)
        print(f"   t={t}: 预测噪声范围=[{noise_pred.min():.3f}, {noise_pred.max():.3f}]")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
