"""
Stable Diffusion注意力机制
Stable Diffusion Attention Mechanism

Stable Diffusion使用交叉注意力机制实现文本到图像的条件生成。
U-Net中的自注意力和交叉注意力是生成质量的关键。
"""

import numpy as np
from typing import Optional, Tuple, Callable
from abc import ABC, abstractmethod


class Attention(ABC):
    """
    注意力机制基类
    
    参数:
        dim: 输入维度
        n_heads: 注意力头数
    """
    
    @abstractmethod
    def __init__(self, dim: int, n_heads: int):
        pass
    
    @abstractmethod
    def forward(self, x: np.ndarray) -> np.ndarray:
        pass


class SelfAttention(Attention):
    """
    自注意力机制
    
    Q = K = V = x
    
    参数:
        dim: 输入维度
        n_heads: 头数
        dropout: Dropout率
    """
    
    def __init__(self, dim: int, n_heads: int = 8, dropout: float = 0.0):
        self.dim = dim
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.scale = self.head_dim ** -0.5
        
        # 初始化参数
        self.to_qkv = np.random.randn(dim * 3, dim) * 0.02
        self.to_out = np.random.randn(dim, dim) * 0.02
    
    def split_heads(self, x: np.ndarray) -> np.ndarray:
        """
        分割多头
        
        参数:
            x: (B, N, D)
            
        返回:
            (B, heads, N, head_dim)
        """
        B, N, D = x.shape
        x = x.reshape(B, N, self.n_heads, self.head_dim)
        return x.transpose(0, 2, 1, 3)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 输入 (B, N, D)
            
        返回:
            输出 (B, N, D)
        """
        B, N, D = x.shape
        
        # 计算Q, K, V
        qkv = x @ self.to_qkv.T  # (B, N, 3*D)
        qkv = qkv.reshape(B, N, 3, self.n_heads, self.head_dim)
        qkv = qkv.transpose(2, 0, 3, 1, 4)  # (3, B, heads, N, head_dim)
        
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # 注意力计算
        attn = (q @ k.transpose(0, 1, 3, 2)) * self.scale  # (B, heads, N, N)
        attn = np.exp(attn - np.max(attn, axis=-1, keepdims=True))
        attn = attn / (np.sum(attn, axis=-1, keepdims=True) + 1e-8)
        
        # 应用注意力
        out = attn @ v  # (B, heads, N, head_dim)
        out = out.transpose(0, 2, 1, 3).reshape(B, N, D)
        
        # 输出投影
        out = out @ self.to_out.T
        
        return out


class CrossAttention(Attention):
    """
    交叉注意力机制
    
    用于Stable Diffusion中潜在图像与文本嵌入的交互
    
    参数:
        dim: 潜在维度
        context_dim: 上下文（文本）维度
        n_heads: 头数
    """
    
    def __init__(self, dim: int, context_dim: int, n_heads: int = 8):
        self.dim = dim
        self.context_dim = context_dim
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        self.scale = self.head_dim ** -0.5
        
        # 投影矩阵
        self.to_q = np.random.randn(dim, dim) * 0.02
        self.to_k = np.random.randn(context_dim, dim) * 0.02
        self.to_v = np.random.randn(context_dim, dim) * 0.02
        self.to_out = np.random.randn(dim, dim) * 0.02
    
    def forward(self, x: np.ndarray, context: np.ndarray) -> np.ndarray:
        """
        交叉注意力前向传播
        
        参数:
            x: 潜在表示 (B, N, dim) - Query来源
            context: 上下文 (B, M, context_dim) - Key/Value来源
            
        返回:
            输出 (B, N, dim)
        """
        B, N, D = x.shape
        _, M, C = context.shape
        
        # 计算Q, K, V
        q = x @ self.to_q.T  # (B, N, dim)
        k = context @ self.to_k.T  # (B, M, dim)
        v = context @ self.to_v.T  # (B, M, dim)
        
        # 分割多头
        q = q.reshape(B, N, self.n_heads, self.head_dim).transpose(0, 2, 1, 3)  # (B, heads, N, head_dim)
        k = k.reshape(B, M, self.n_heads, self.head_dim).transpose(0, 2, 1, 3)
        v = v.reshape(B, M, self.n_heads, self.head_dim).transpose(0, 2, 1, 3)
        
        # 注意力
        attn = (q @ k.transpose(0, 1, 3, 2)) * self.scale  # (B, heads, N, M)
        attn = np.exp(attn - np.max(attn, axis=-1, keepdims=True))
        attn = attn / (np.sum(attn, axis=-1, keepdims=True) + 1e-8)
        
        # 应用注意力
        out = attn @ v  # (B, heads, N, head_dim)
        out = out.transpose(0, 2, 1, 3).reshape(B, N, D)
        
        return out @ self.to_out.T


class SpatialAttention:
    """
    空间注意力
    
    应用于特征图的空间维度
    
    参数:
        channels: 通道数
    """
    
    def __init__(self, channels: int):
        self.channels = channels
        
        # 简化的空间注意力参数
        self.conv = np.random.randn(1, channels, 7, 7) * 0.02
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        空间注意力前向
        
        参数:
            x: 特征图 (B, C, H, W)
            
        返回:
            加权特征图
        """
        # 简化的空间注意力
        # 实际应用中会用 AvgPool/MaxPool -> Conv -> Sigmoid
        
        B, C, H, W = x.shape
        
        # 全局平均池化
        avg_out = np.mean(x, axis=(2, 3), keepdims=True)
        
        # 全局最大池化
        max_out = np.max(x, axis=(2, 3), keepdims=True)
        
        # 简化的注意力权重
        attn = (avg_out + max_out) * 0.5
        
        return x * attn


class MultiHeadAttentionBlock:
    """
    多头注意力块（包含残差连接和层归一化）
    
    参数:
        dim: 维度
        n_heads: 头数
        mlp_dim: FFN维度
    """
    
    def __init__(self, dim: int, n_heads: int = 8, mlp_dim: int = None):
        self.dim = dim
        self.n_heads = n_heads
        self.mlp_dim = mlp_dim or dim * 4
        
        # 自注意力
        self.self_attn = SelfAttention(dim, n_heads)
        
        # 交叉注意力
        self.cross_attn = CrossAttention(dim, dim)
        
        # 层归一化（简化）
        self.norm1 = lambda x: x
        self.norm2 = lambda x: x
        self.norm3 = lambda x: x
        
        # FFN
        self.ffn = self._init_ffn()
    
    def _init_ffn(self):
        """初始化FFN"""
        return {
            'fc1': np.random.randn(self.mlp_dim, self.dim) * 0.02,
            'fc2': np.random.randn(self.dim, self.mlp_dim) * 0.02,
        }
    
    def ffn_forward(self, x: np.ndarray) -> np.ndarray:
        """FFN前向"""
        h = x @ self.ffn['fc1'].T
        h = np.maximum(h, 0)  # GELU近似
        h = h @ self.ffn['fc2'].T
        return h
    
    def forward(self, x: np.ndarray, context: Optional[np.ndarray] = None) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 潜在表示
            context: 上下文（用于交叉注意力）
            
        返回:
            输出
        """
        # 自注意力 + 残差
        x = x + self.self_attn(self.norm1(x))
        
        # 交叉注意力（如果有context）
        if context is not None:
            x = x + self.cross_attn(self.norm2(x), context)
        
        # FFN + 残差
        x = x + self.ffn_forward(self.norm3(x))
        
        return x


class TransformerBlock:
    """
    Transformer块
    
    包含注意力、前馈网络和残差连接
    
    参数:
        dim: 维度
        n_heads: 头数
        dropout: Dropout率
    """
    
    def __init__(self, dim: int, n_heads: int = 8, dropout: float = 0.1):
        self.attn = SelfAttention(dim, n_heads, dropout)
        self.ffn = self._init_ffn(dim, dim * 4)
        
        # 层归一化
        self.norm1 = lambda x: x
        self.norm2 = lambda x: x
    
    def _init_ffn(self, dim: int, hidden_dim: int):
        """初始化FFN"""
        return {
            'fc1': np.random.randn(hidden_dim, dim) * 0.02,
            'fc2': np.random.randn(dim, hidden_dim) * 0.02,
        }
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """前向传播"""
        # 注意力 + 残差
        x = x + self.attn(self.norm1(x))
        
        # FFN + 残差
        h = self.ffn['fc1'] @ x.T
        h = np.maximum(h, 0)
        h = self.ffn['fc2'] @ h
        x = x + h.T
        
        return x


class AttentionUpsample:
    """
    带注意力的上采样
    
    在上采样时加入注意力机制
    """
    
    def __init__(self, channels: int):
        self.channels = channels
        self.attention = SpatialAttention(channels)
        self.conv = np.random.randn(channels, channels, 3, 3) * 0.02
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 特征图 (B, C, H, W)
            
        返回:
            上采样 + 注意力加权后的特征图
        """
        # 最近邻上采样
        B, C, H, W = x.shape
        x_upsampled = np.repeat(np.repeat(x, 2, axis=2), 2, axis=3)
        
        # 应用注意力
        out = self.attention(x_upsampled)
        
        return out


class SkipConnection:
    """
    跳跃连接管理
    
    用于U-Net编码器到解码器的特征传递
    """
    
    def __init__(self):
        self.skip_features = {}
    
    def store(self, name: str, feature: np.ndarray):
        """存储编码器特征"""
        self.skip_features[name] = feature
    
    def retrieve(self, name: str) -> Optional[np.ndarray]:
        """获取编码器特征"""
        return self.skip_features.get(name)
    
    def clear(self):
        """清除所有存储的特征"""
        self.skip_features = {}


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Stable Diffusion注意力机制测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：自注意力
    print("\n1. 自注意力机制:")
    
    self_attn = SelfAttention(dim=64, n_heads=8)
    
    x = np.random.randn(2, 16, 64)  # (B, N, D)
    out = self_attn.forward(x)
    
    print(f"   输入形状: {x.shape}")
    print(f"   输出形状: {out.shape}")
    print(f"   注意力头数: {self_attn.n_heads}")
    print(f"   每头维度: {self_attn.head_dim}")
    
    # 测试2：交叉注意力
    print("\n2. 交叉注意力机制:")
    
    cross_attn = CrossAttention(dim=64, context_dim=128, n_heads=8)
    
    x = np.random.randn(2, 16, 64)  # 潜在表示
    context = np.random.randn(2, 8, 128)  # 文本嵌入
    
    out = cross_attn.forward(x, context)
    
    print(f"   潜在表示形状: {x.shape}")
    print(f"   文本嵌入形状: {context.shape}")
    print(f"   输出形状: {out.shape}")
    
    # 测试3：多头注意力块
    print("\n3. 多头注意力块:")
    
    mha_block = MultiHeadAttentionBlock(dim=64, n_heads=8)
    
    x = np.random.randn(2, 16, 64)
    context = np.random.randn(2, 8, 64)
    
    out = mha_block.forward(x, context)
    
    print(f"   输入形状: {x.shape}")
    print(f"   上下文形状: {context.shape}")
    print(f"   输出形状: {out.shape}")
    
    # 测试4：空间注意力
    print("\n4. 空间注意力:")
    
    spatial_attn = SpatialAttention(channels=64)
    
    x = np.random.randn(2, 64, 32, 32)  # (B, C, H, W)
    out = spatial_attn.forward(x)
    
    print(f"   输入形状: {x.shape}")
    print(f"   输出形状: {out.shape}")
    
    # 测试5：Transformer块
    print("\n5. Transformer块:")
    
    transformer = TransformerBlock(dim=64, n_heads=8)
    
    x = np.random.randn(2, 16, 64)
    out = transformer.forward(x)
    
    print(f"   输入形状: {x.shape}")
    print(f"   输出形状: {out.shape}")
    
    # 测试6：U-Net跳跃连接
    print("\n6. U-Net跳跃连接:")
    
    skip_conn = SkipConnection()
    
    # 模拟编码器特征
    for i in range(4):
        feature = np.random.randn(2, 64, 32 // (2**i), 32 // (2**i))
        skip_conn.store(f'encoder_{i}', feature)
        print(f"   存储 encoder_{i}: {feature.shape}")
    
    # 模拟解码器检索
    for i in range(4):
        feature = skip_conn.retrieve(f'encoder_{i}')
        print(f"   检索 encoder_{i}: {feature.shape}")
    
    # 测试7：注意力可视化
    print("\n7. 注意力权重分析:")
    
    # 简化的注意力权重计算
    B, N, D = 1, 16, 64
    q = np.random.randn(B, N, D)
    k = np.random.randn(B, N, D)
    
    scale = D ** -0.5
    attn = (q @ k.transpose(0, 2, 1)) * scale
    attn = np.exp(attn - np.max(attn, axis=-1, keepdims=True))
    attn = attn / np.sum(attn, axis=-1, keepdims=True)
    
    # 对角线注意力（自注意力）
    diag_avg = np.mean(np.diag(attn[0]))
    print(f"   平均自注意力权重（对角线）: {diag_avg:.4f}")
    print(f"   总注意力权重和: {np.sum(attn[0]):.2f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
