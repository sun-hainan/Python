"""
条件DDPM：文本条件/cFG
Conditional DDPM: Text Conditioning / cFG

条件扩散模型通过额外的条件信息（文本、类别、图像等）
来引导生成过程，实现有条件的图像生成。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List, Dict
from abc import ABC, abstractmethod


class ConditionEncoder(ABC):
    """
    条件编码器基类
    
    将条件信息编码为模型可用的表示
    """
    
    @abstractmethod
    def encode(self, condition: any) -> np.ndarray:
        """编码条件"""
        pass


class TextEncoder(ConditionEncoder):
    """
    文本编码器
    
    将文本转换为嵌入向量
    
    参数:
        vocab_size: 词汇表大小
        embed_dim: 嵌入维度
        max_length: 最大序列长度
    """
    
    def __init__(self, vocab_size: int = 10000, embed_dim: int = 768, 
                 max_length: int = 77):
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.max_length = max_length
        
        # 简化的嵌入矩阵
        self.embedding = np.random.randn(vocab_size, embed_dim) * 0.02
    
    def encode(self, text: str) -> np.ndarray:
        """
        编码文本
        
        参数:
            text: 输入文本
            
        返回:
            文本嵌入 (max_length, embed_dim)
        """
        # 简化的编码：直接将文本的字符映射为token
        tokens = [ord(c) % self.vocab_size for c in text[:self.max_length]]
        
        # 填充
        while len(tokens) < self.max_length:
            tokens.append(0)
        
        tokens = np.array(tokens)
        
        # 查表
        embeddings = self.embedding[tokens]
        
        return embeddings
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        批量编码
        
        参数:
            texts: 文本列表
            
        返回:
            嵌入 (batch, max_length, embed_dim)
        """
        return np.array([self.encode(text) for text in texts])


class ClassEncoder(ConditionEncoder):
    """
    类别编码器
    
    将类别标签转换为one-hot向量
    
    参数:
        num_classes: 类别数量
    """
    
    def __init__(self, num_classes: int = 1000):
        self.num_classes = num_classes
    
    def encode(self, class_label: int) -> np.ndarray:
        """
        编码类别
        
        参数:
            class_label: 类别索引
            
        返回:
            One-hot向量
        """
        one_hot = np.zeros(self.num_classes)
        one_hot[class_label] = 1.0
        return one_hot
    
    def encode_batch(self, class_labels: List[int]) -> np.ndarray:
        """
        批量编码
        
        参数:
            class_labels: 类别索引列表
            
        返回:
            One-hot向量 (batch, num_classes)
        """
        return np.array([self.encode(c) for c in class_labels])


class ImageEncoder(ConditionEncoder):
    """
    图像编码器
    
    将条件图像编码为特征向量
    
    参数:
        feature_dim: 输出特征维度
    """
    
    def __init__(self, feature_dim: int = 512):
        self.feature_dim = feature_dim
        
        # 简化的编码器参数
        self.conv1 = np.random.randn(64, 3, 3, 3) * 0.02
        self.conv2 = np.random.randn(128, 64, 3, 3) * 0.02
        self.fc = np.random.randn(feature_dim, 128) * 0.02
    
    def encode(self, image: np.ndarray) -> np.ndarray:
        """
        编码图像
        
        参数:
            image: 图像 (H, W, C) 或 (B, H, W, C)
            
        返回:
            特征向量
        """
        # 简化的编码
        # 实际应用中会用完整的CNN编码器
        
        if image.ndim == 3:
            image = image[np.newaxis, ...]
        
        B, H, W, C = image.shape
        
        # 简化特征提取
        features = np.random.randn(B, 128) * 0.1
        features = features @ self.fc.T
        
        return features[0] if B == 1 else features
    
    def encode_batch(self, images: np.ndarray) -> np.ndarray:
        """
        批量编码
        
        参数:
            images: 图像 (B, H, W, C)
            
        返回:
            特征 (B, feature_dim)
        """
        B = len(images)
        features = np.random.randn(B, self.feature_dim) * 0.1
        return features


class ConditionalDiffusionModel:
    """
    条件扩散模型
    
    参数:
        denoise_fn: 去噪函数
        condition_encoder: 条件编码器
        T: 扩散步数
    """
    
    def __init__(self, denoise_fn: Callable, condition_encoder: ConditionEncoder,
                 T: int = 1000):
        self.denoise_fn = denoise_fn
        self.condition_encoder = condition_encoder
        self.T = T
        
        # 初始化调度
        self._init_schedule()
    
    def _init_schedule(self):
        """初始化噪声调度"""
        self.betas = np.linspace(1e-4, 0.02, self.T)
        self.alphas = 1 - self.betas
        self.alpha_bars = np.cumprod(self.alphas)
    
    def forward_diffusion(self, x_0: np.ndarray, t: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        前向扩散
        
        参数:
            x_0: 原始图像
            t: 时间步
            
        返回:
            (x_t, epsilon)
        """
        alpha_bar_t = self.alpha_bars[t]
        epsilon = np.random.randn(*x_0.shape)
        x_t = np.sqrt(alpha_bar_t) * x_0 + np.sqrt(1 - alpha_bar_t) * epsilon
        
        return x_t, epsilon
    
    def denoise_with_condition(self, x_t: np.ndarray, t: int, 
                               condition: any) -> np.ndarray:
        """
        条件去噪
        
        参数:
            x_t: 加噪图像
            t: 时间步
            condition: 条件
            
        返回:
            预测的噪声
        """
        # 编码条件
        cond_emb = self.condition_encoder.encode(condition)
        
        # 条件去噪
        noise_pred = self.denoise_fn(x_t, t, cond_emb)
        
        return noise_pred
    
    def training_loss(self, x_0: np.ndarray, condition: any) -> float:
        """
        计算训练损失
        
        参数:
            x_0: 原始图像
            condition: 条件
            
        返回:
            损失值
        """
        # 随机采样时间步
        t = np.random.randint(0, self.T)
        
        # 前向扩散
        x_t, epsilon = self.forward_diffusion(x_0, t)
        
        # 条件去噪预测
        epsilon_pred = self.denoise_with_condition(x_t, t, condition)
        
        # MSE损失
        loss = np.mean((epsilon - epsilon_pred) ** 2)
        
        return loss
    
    def sample(self, condition: any, shape: Tuple,
              n_steps: int = 50) -> np.ndarray:
        """
        条件采样
        
        参数:
            condition: 条件
            shape: 采样形状
            n_steps: 采样步数
            
        返回:
            生成的图像
        """
        # 从纯噪声开始
        x_t = np.random.randn(*shape)
        
        # 时间步
        timesteps = np.linspace(0, self.T - 1, n_steps, dtype=int)[::-1]
        
        for i, t in enumerate(timesteps):
            # 预测噪声
            epsilon_pred = self.denoise_with_condition(x_t, t, condition)
            
            # DDIM更新
            alpha_bar_t = self.alpha_bars[t]
            
            if i < len(timesteps) - 1:
                alpha_bar_prev = self.alpha_bars[timesteps[i + 1]]
            else:
                alpha_bar_prev = 1.0
            
            # 一步去噪
            x_0_pred = (x_t - np.sqrt(1 - alpha_bar_t) * epsilon_pred) / np.sqrt(alpha_bar_t)
            x_t = np.sqrt(alpha_bar_prev) * x_0_pred + np.sqrt(1 - alpha_bar_prev) * epsilon_pred
        
        return x_t


class ClassifierFreeGuidance:
    """
    无分类器引导
    
    参数:
        model: 条件模型
        guidance_scale: 引导权重
    """
    
    def __init__(self, model: ConditionalDiffusionModel, 
                 guidance_scale: float = 7.5):
        self.model = model
        self.guidance_scale = guidance_scale
    
    def predict(self, x_t: np.ndarray, t: int, 
               condition: any) -> np.ndarray:
        """
        CFG预测
        
        参数:
            x_t: 当前状态
            t: 时间步
            condition: 条件
            
        返回:
            引导后的预测
        """
        # 条件预测
        epsilon_cond = self.model.denoise_with_condition(x_t, t, condition)
        
        # 无条件预测（使用空条件）
        epsilon_uncond = self.model.denoise_with_condition(x_t, t, None)
        
        # CFG
        epsilon_cfg = epsilon_uncond + self.guidance_scale * (epsilon_cond - epsilon_uncond)
        
        return epsilon_cfg


class Img2ImgDiffusion:
    """
    Img2Img条件扩散模型
    
    基于输入图像进行转换/编辑
    
    参数:
        diffusion_model: 扩散模型
        strength: 变换强度 (0-1)
    """
    
    def __init__(self, diffusion_model: ConditionalDiffusionModel,
                 strength: float = 0.8):
        self.diffusion_model = diffusion_model
        self.strength = strength
    
    def transform(self, input_image: np.ndarray, 
                 condition: any,
                 n_steps: int = 50) -> np.ndarray:
        """
        图像转换
        
        参数:
            input_image: 输入图像
            condition: 条件（如目标风格描述）
            n_steps: 采样步数
            
        返回:
            转换后的图像
        """
        # 决定从哪一步开始（基于强度）
        start_step = int(n_steps * (1 - self.strength))
        
        # 对输入图像加噪到start_step
        if start_step > 0:
            t = start_step
            x_t, _ = self.diffusion_model.forward_diffusion(input_image, t)
        else:
            x_t = input_image
        
        # 条件采样
        timesteps = np.linspace(start_step, self.diffusion_model.T - 1, 
                               n_steps - start_step, dtype=int)[::-1]
        
        for i, t in enumerate(timesteps):
            epsilon_pred = self.diffusion_model.denoise_with_condition(x_t, t, condition)
            
            alpha_bar_t = self.diffusion_model.alpha_bars[t]
            
            if i < len(timesteps) - 1:
                alpha_bar_prev = self.diffusion_model.alpha_bars[timesteps[i + 1]]
            else:
                alpha_bar_prev = 1.0
            
            x_0_pred = (x_t - np.sqrt(1 - alpha_bar_t) * epsilon_pred) / np.sqrt(alpha_bar_t)
            x_t = np.sqrt(alpha_bar_prev) * x_0_pred + np.sqrt(1 - alpha_bar_prev) * epsilon_pred
        
        return x_t


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("条件DDPM测试（文本条件/cFG）")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 模拟去噪函数
    def mock_denoise(x_t, t, cond_emb):
        # 简化的条件去噪
        cond_effect = np.mean(cond_emb) if cond_emb is not None else 0
        return x_t * 0.05 + cond_effect * 0.01 + np.random.randn(*x_t.shape) * 0.01
    
    # 测试1：文本编码器
    print("\n1. 文本编码器:")
    
    text_encoder = TextEncoder(vocab_size=10000, embed_dim=768)
    
    text = "A beautiful sunset over the ocean"
    emb = text_encoder.encode(text)
    
    print(f"   文本: '{text}'")
    print(f"   嵌入形状: {emb.shape}")
    print(f"   嵌入范数: {np.linalg.norm(emb):.4f}")
    
    # 测试2：类别编码器
    print("\n2. 类别编码器:")
    
    class_encoder = ClassEncoder(num_classes=1000)
    
    for label in [0, 100, 999]:
        one_hot = class_encoder.encode(label)
        print(f"   类别{label}: 非零元素={np.sum(one_hot > 0)}")
    
    # 测试3：图像编码器
    print("\n3. 图像编码器:")
    
    img_encoder = ImageEncoder(feature_dim=512)
    
    image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    features = img_encoder.encode(image)
    
    print(f"   图像形状: {image.shape}")
    print(f"   特征形状: {features.shape}")
    
    # 测试4：条件扩散模型
    print("\n4. 条件扩散模型:")
    
    cond_model = ConditionalDiffusionModel(
        denoise_fn=mock_denoise,
        condition_encoder=text_encoder,
        T=1000
    )
    
    # 训练损失
    x_0 = np.random.randn(2, 3, 32, 32)
    condition = "A cat sitting on a sofa"
    
    loss = cond_model.training_loss(x_0, condition)
    print(f"   训练损失: {loss:.6f}")
    
    # 测试5：条件采样
    print("\n5. 条件采样:")
    
    generated = cond_model.sample(condition, shape=(1, 3, 32, 32), n_steps=10)
    print(f"   生成图像形状: {generated.shape}")
    print(f"   生成图像范围: [{generated.min():.4f}, {generated.max():.4f}]")
    
    # 测试6：无分类器引导
    print("\n6. 无分类器引导 (CFG):")
    
    cfg = ClassifierFreeGuidance(cond_model, guidance_scale=7.5)
    
    x_t = np.random.randn(1, 3, 32, 32)
    t = 500
    condition = "A beautiful landscape"
    
    epsilon_cond = cond_model.denoise_with_condition(x_t, t, condition)
    epsilon_uncond = cond_model.denoise_with_condition(x_t, t, None)
    epsilon_cfg = cfg.predict(x_t, t, condition)
    
    print(f"   条件预测均值: {np.mean(epsilon_cond):.6f}")
    print(f"   无条件预测均值: {np.mean(epsilon_uncond):.6f}")
    print(f"   CFG预测均值: {np.mean(epsilon_cfg):.6f}")
    print(f"   引导增强: {(np.mean(epsilon_cfg) - np.mean(epsilon_uncond)):.6f}")
    
    # 测试7：Img2Img
    print("\n7. Img2Img转换:")
    
    img2img = Img2ImgDiffusion(cond_model, strength=0.7)
    
    input_img = np.random.randn(1, 3, 32, 32)
    output_img = img2img.transform(input_img, condition="Turn into oil painting style")
    
    print(f"   输入形状: {input_img.shape}")
    print(f"   输出形状: {output_img.shape}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
