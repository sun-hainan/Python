"""
无分类器引导（Classifier-Free Guidance, CFG）
Classifier-Free Guidance

CFG是一种无需训练分类器即可实现条件生成的技术。
通过在条件和非条件预测之间进行插值来实现引导效果。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List


class ConditionalModel:
    """
    条件模型接口
    
    支持条件和非条件生成
    
    参数:
        model: 基础神经网络
    """
    
    def __init__(self, model: Callable):
        self.model = model
        self.has_condition = True
    
    def __call__(self, x: np.ndarray, t: np.ndarray, 
                y: Optional[np.ndarray] = None) -> np.ndarray:
        """
        前向传播
        
        参数:
            x: 加噪输入
            t: 时间步
            y: 条件（None表示无条件）
            
        返回:
            模型输出
        """
        if y is None:
            # 无条件预测
            return self.model(x, t, condition=None)
        else:
            # 条件预测
            return self.model(x, t, condition=y)


class ClassifierFreeGuidance:
    """
    无分类器引导
    
    核心思想：
    epsilon_cond = epsilon_theta(x_t, y)  # 条件预测
    epsilon_uncond = epsilon_theta(x_t, None)  # 无条件预测
    epsilon_cfg = epsilon_uncond + w * (epsilon_cond - epsilon_uncond)
    
    其中 w 是引导权重（通常 7-10）
    
    参数:
        model: 条件扩散模型
        guidance_scale: 引导权重 w
    """
    
    def __init__(self, model: ConditionalModel, guidance_scale: float = 7.5):
        self.model = model
        self.guidance_scale = guidance_scale
    
    def predict(self, x_t: np.ndarray, t: np.ndarray, 
                y: np.ndarray) -> np.ndarray:
        """
        使用CFG预测
        
        参数:
            x_t: 加噪图像
            t: 时间步
            y: 条件嵌入
            
        返回:
            引导后的预测
        """
        # 条件预测
        epsilon_cond = self.model(x_t, t, y)
        
        # 无条件预测（y=None）
        epsilon_uncond = self.model(x_t, t, None)
        
        # CFG公式
        epsilon_cfg = epsilon_uncond + self.guidance_scale * (epsilon_cond - epsilon_uncond)
        
        return epsilon_cfg
    
    def update_guidance_scale(self, new_scale: float):
        """更新引导权重"""
        self.guidance_scale = new_scale


class CFGSampling:
    """
    CFG采样器
    
    参数:
        model: 条件模型
        guidance_scale: 引导权重
        schedule: 噪声调度
    """
    
    def __init__(self, model: ConditionalModel, 
                 guidance_scale: float = 7.5,
                 betas: Optional[np.ndarray] = None,
                 T: int = 1000):
        self.model = model
        self.guidance_scale = guidance_scale
        self.T = T
        
        # 初始化调度
        if betas is None:
            self.betas = np.linspace(1e-4, 0.02, T)
        else:
            self.betas = betas
        
        self.alphas = 1 - self.betas
        self.alpha_bars = np.cumprod(self.alphas)
    
    def sample(self, shape: Tuple, y: np.ndarray,
              n_steps: int = 50) -> np.ndarray:
        """
        CFG引导采样
        
        参数:
            shape: 采样形状
            y: 条件嵌入
            n_steps: 采样步数
            
        返回:
            生成的图像
        """
        # 从纯噪声开始
        x_t = np.random.randn(*shape)
        
        # 时间步
        timesteps = np.linspace(0, self.T - 1, n_steps, dtype=int)[::-1]
        
        for i, t in enumerate(timesteps):
            # 使用CFG预测
            epsilon_cfg = self.predict_with_cfg(x_t, t, y)
            
            # DDIM更新
            alpha_bar_t = self.alpha_bars[t]
            
            if i < len(timesteps) - 1:
                alpha_bar_prev = self.alpha_bars[timesteps[i + 1]]
            else:
                alpha_bar_prev = 1.0
            
            # 一步去噪
            x_t = self._denoise_step(x_t, epsilon_cfg, alpha_bar_t, alpha_bar_prev)
        
        return x_t
    
    def predict_with_cfg(self, x_t: np.ndarray, t: int, 
                        y: np.ndarray) -> np.ndarray:
        """
        CFG预测
        
        参数:
            x_t: 当前状态
            t: 时间步
            y: 条件
            
        返回:
            引导后的噪声预测
        """
        cfg = ClassifierFreeGuidance(self.model, self.guidance_scale)
        return cfg.predict(x_t, np.array([t]), y)
    
    def _denoise_step(self, x_t: np.ndarray, epsilon_pred: np.ndarray,
                     alpha_bar_t: float, alpha_bar_prev: float) -> np.ndarray:
        """
        单步去噪
        
        参数:
            x_t: 当前状态
            epsilon_pred: 预测的噪声
            alpha_bar_t: 当前累积alpha
            alpha_bar_prev: 前一步累积alpha
            
        返回:
            去噪后的状态
        """
        # 简化的DDIM更新
        x_0_pred = (x_t - np.sqrt(1 - alpha_bar_t) * epsilon_pred) / np.sqrt(alpha_bar_t)
        
        x_prev = np.sqrt(alpha_bar_prev) * x_0_pred + \
                 np.sqrt(1 - alpha_bar_prev) * epsilon_pred
        
        return x_prev


class NegativePromptSampling:
    """
    负提示词采样（CFG的扩展）
    
    使用负提示词来引导生成
    
    参数:
        model: 条件模型
        guidance_scale: 主引导权重
        neg_guidance_scale: 负引导权重
    """
    
    def __init__(self, model: ConditionalModel,
                 guidance_scale: float = 7.5,
                 neg_guidance_scale: float = 1.0):
        self.model = model
        self.guidance_scale = guidance_scale
        self.neg_guidance_scale = neg_guidance_scale
    
    def predict(self, x_t: np.ndarray, t: np.ndarray,
               y_pos: np.ndarray, y_neg: np.ndarray) -> np.ndarray:
        """
        使用正负提示词预测
        
        参数:
            x_t: 加噪输入
            t: 时间步
            y_pos: 正提示词嵌入
            y_neg: 负提示词嵌入
            
        返回:
            预测噪声
        """
        # 条件预测
        epsilon_pos = self.model(x_t, t, y_pos)
        
        # 无条件预测
        epsilon_uncond = self.model(x_t, t, None)
        
        # 负提示词预测
        epsilon_neg = self.model(x_t, t, y_neg)
        
        # 扩展CFG公式
        epsilon_cfg = epsilon_uncond
        epsilon_cfg += self.guidance_scale * (epsilon_pos - epsilon_uncond)
        epsilon_cfg -= self.neg_guidance_scale * (epsilon_neg - epsilon_uncond)
        
        return epsilon_cfg


class CFGScheduler:
    """
    CFG调度器
    
    在采样过程中动态调整引导权重
    
    参数:
        guidance_scales: 引导权重列表
    """
    
    def __init__(self, guidance_scales: Optional[List[float]] = None):
        if guidance_scales is None:
            # 默认：开始时高引导，逐渐降低
            self.guidance_scales = np.linspace(10.0, 5.0, 50)
        else:
            self.guidance_scales = np.array(guidance_scales)
    
    def get_guidance_scale(self, step: int) -> float:
        """
        获取当前步的引导权重
        
        参数:
            step: 当前步
            
        返回:
            引导权重
        """
        if step < len(self.guidance_scales):
            return self.guidance_scales[step]
        return self.guidance_scales[-1]


class PromptBlending:
    """
    提示词混合
    
    在生成过程中插值多个提示词
    
    参数:
        model: 条件模型
    """
    
    def __init__(self, model: ConditionalModel):
        self.model = model
    
    def blend_predictions(self, x_t: np.ndarray, t: np.ndarray,
                         prompts: List[np.ndarray], weights: List[float]) -> np.ndarray:
        """
        混合多个提示词的预测
        
        参数:
            x_t: 加噪输入
            t: 时间步
            prompts: 提示词嵌入列表
            weights: 对应权重
            
        返回:
            加权平均的预测
        """
        # 归一化权重
        weights = np.array(weights, dtype=float)
        weights = weights / np.sum(weights)
        
        predictions = []
        for prompt in prompts:
            pred = self.model(x_t, t, prompt)
            predictions.append(pred)
        
        # 加权平均
        blended = np.zeros_like(predictions[0])
        for pred, w in zip(predictions, weights):
            blended += w * pred
        
        return blended


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("无分类器引导(CFG)测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 模拟条件模型
    class MockConditionalModel:
        def __call__(self, x, t, condition):
            base = x * 0.1
            if condition is not None:
                base = base + condition * 0.01
            return base
    
    model = MockConditionalModel()
    cond_model = ConditionalModel(model)
    
    # 测试1：基础CFG
    print("\n1. 无分类器引导基础:")
    
    cfg = ClassifierFreeGuidance(cond_model, guidance_scale=7.5)
    
    x_t = np.random.randn(2, 3, 32, 32)
    t = np.array([500])
    y = np.random.randn(2, 10)  # 条件嵌入
    
    epsilon_cond = cond_model(x_t, t, y)
    epsilon_uncond = cond_model(x_t, t, None)
    epsilon_cfg = cfg.predict(x_t, t, y)
    
    print(f"   条件预测均值: {np.mean(epsilon_cond):.6f}")
    print(f"   无条件预测均值: {np.mean(epsilon_uncond):.6f}")
    print(f"   CFG预测均值: {np.mean(epsilon_cfg):.6f}")
    print(f"   引导增强: {(np.mean(epsilon_cfg) - np.mean(epsilon_uncond)):.6f}")
    
    # 测试2：不同引导权重
    print("\n2. 不同引导权重效果:")
    
    for w in [1.0, 3.0, 7.5, 10.0, 15.0]:
        cfg.update_guidance_scale(w)
        epsilon_cfg = cfg.predict(x_t, t, y)
        print(f"   w={w:5.1f}: 预测范围=[{epsilon_cfg.min():.4f}, {epsilon_cfg.max():.4f}]")
    
    # 测试3：CFG采样
    print("\n3. CFG引导采样:")
    
    betas = np.linspace(1e-4, 0.02, 1000)
    
    class MockCondModel:
        def __call__(self, x, t, condition):
            return np.random.randn(*x.shape) * 0.1
    
    sampler = CFGSampling(MockCondModel(), guidance_scale=7.5, betas=betas[:50], T=50)
    
    shape = (1, 3, 32, 32)
    y = np.random.randn(1, 10)
    
    x_0 = sampler.sample(shape, y, n_steps=50)
    print(f"   采样形状: {x_0.shape}")
    print(f"   采样均值: {np.mean(x_0):.6f}")
    print(f"   采样方差: {np.var(x_0):.6f}")
    
    # 测试4：负提示词
    print("\n4. 负提示词引导:")
    
    neg_cfg = NegativePromptSampling(cond_model, guidance_scale=7.5, neg_guidance_scale=1.0)
    
    y_pos = np.random.randn(2, 10)
    y_neg = np.random.randn(2, 10) * 0.5
    
    epsilon_blended = neg_cfg.predict(x_t, t, y_pos, y_neg)
    print(f"   正负提示词混合预测均值: {np.mean(epsilon_blended):.6f}")
    
    # 测试5：CFG调度
    print("\n5. CFG动态调度:")
    
    cfg_scheduler = CFGScheduler()
    
    print("   引导权重曲线:")
    for step in [0, 10, 25, 40, 49]:
        w = cfg_scheduler.get_guidance_scale(step)
        print(f"   Step {step}: w={w:.2f}")
    
    # 测试6：提示词混合
    print("\n6. 提示词混合:")
    
    blend = PromptBlending(cond_model)
    
    prompts = [
        np.random.randn(2, 10),  # prompt 1
        np.random.randn(2, 10),  # prompt 2
        np.random.randn(2, 10),  # prompt 3
    ]
    weights = [0.5, 0.3, 0.2]
    
    blended_pred = blend.blend_predictions(x_t, t, prompts, weights)
    print(f"   混合预测形状: {blended_pred.shape}")
    print(f"   混合预测均值: {np.mean(blended_pred):.6f}")
    
    # 测试7：引导效果可视化
    print("\n7. 引导强度分析:")
    
    print("   w=1.0 (无引导):  epsilon_cfg ≈ epsilon_uncond")
    print("   w=7.5 (标准):    epsilon显著增强条件效应")
    print("   w→∞:            epsilon_cfg ≈ epsilon_cond")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
