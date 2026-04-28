"""
DDPM前向过程：加噪马尔可夫链
DDPM Forward Process: Noise Addition Markov Chain

DDPM的前向过程（q）是一个固定的马尔可夫链，
通过T步逐步向数据添加高斯噪声，最终得到近似各向同性高斯分布。
关键性质：任意时间步t的闭式解
x_t = sqrt(bar_alpha_t) * x_0 + sqrt(1 - bar_alpha_t) * epsilon
"""

import numpy as np
from typing import Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class DiffusionSchedule:
    """
    扩散调度配置
    
    属性:
        T: 扩散步数
        beta_start: 噪声方差起始值
        beta_end: 噪声方差结束值
        schedule_type: 调度类型 ('linear', 'cosine', 'sqrt')
    """
    T: int = 1000
    beta_start: float = 1e-4
    beta_end: float = 0.02
    schedule_type: str = 'linear'
    
    def __post_init__(self):
        """初始化调度参数"""
        self._compute_betas()
        self._compute_alphas()
        self._compute_alpha_bars()
    
    def _compute_betas(self):
        """计算每个时间步的beta（噪声方差）"""
        if self.schedule_type == 'linear':
            # 线性调度
            self.betas = np.linspace(self.beta_start, self.beta_end, self.T)
        elif self.schedule_type == 'cosine':
            # 余弦调度（SDE扩散模型常用）
            steps = np.arange(self.T + 1)
            s = 0.008  # 偏移参数
            alphas_cumsum = np.cos((steps / self.T + s) / (1 + s) * np.pi / 2) ** 2
            alphas_cumsum = alphas_cumsum / alphas_cumsum[0]
            self.betas = 1 - alphas_cumsum[1:] / alphas_cumsum[:-1]
            self.betas = np.clip(self.betas, 0, 0.999)
        elif self.schedule_type == 'sqrt':
            # 平方根调度
            self.betas = np.linspace(self.beta_start ** 0.5, self.beta_end ** 0.5, self.T) ** 2
        else:
            raise ValueError(f"Unknown schedule type: {self.schedule_type}")
    
    def _compute_alphas(self):
        """计算alpha_t = 1 - beta_t"""
        self.alphas = 1.0 - self.betas
    
    def _compute_alpha_bars(self):
        """计算累积alpha: bar_alpha_t = prod_{s=1}^{t} alpha_s"""
        self.alpha_bars = np.cumprod(self.alphas)
        self.alpha_bars = np.concatenate([[1.0], self.alpha_bars])


class ForwardProcess:
    """
    DDPM前向过程
    
    前向过程 q(x_t | x_{t-1}) = N(x_t; sqrt(1 - beta_t) * x_{t-1}, beta_t * I)
    
    参数:
        schedule: 扩散调度配置
    """
    
    def __init__(self, schedule: DiffusionSchedule):
        self.schedule = schedule
        self.T = schedule.T
        self.betas = schedule.betas
        self.alphas = schedule.alphas
        self.alpha_bars = schedule.alpha_bars
    
    def step(self, x: np.ndarray, t: int) -> np.ndarray:
        """
        单步前向加噪
        
        参数:
            x: 输入图像 (H, W, C) 或 (B, C, H, W)
            t: 时间步 (0 <= t < T)
            
        返回:
            加噪后的图像
        """
        beta_t = self.betas[t]
        alpha_t = self.alphas[t]
        
        # 从 N(sqrt(1-beta_t) * x_{t-1}, beta_t * I) 采样
        noise = np.random.randn(*x.shape)
        x_t = np.sqrt(alpha_t) * x + np.sqrt(beta_t) * noise
        
        return x_t
    
    def step_with_noise(self, x_0: np.ndarray, t: int, 
                        noise: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用指定噪声进行前向过程（用于训练）
        
        参数:
            x_0: 原始图像
            t: 时间步
            noise: 可选的预生成噪声
            
        返回:
            (x_t, epsilon) 元组
        """
        alpha_bar_t = self.alpha_bars[t]
        
        if noise is None:
            epsilon = np.random.randn(*x_0.shape)
        else:
            epsilon = noise
        
        # x_t = sqrt(alpha_bar_t) * x_0 + sqrt(1 - alpha_bar_t) * epsilon
        x_t = np.sqrt(alpha_bar_t) * x_0 + np.sqrt(1 - alpha_bar_t) * epsilon
        
        return x_t, epsilon
    
    def sample_from_prior(self, shape: Tuple) -> np.ndarray:
        """
        从先验分布（纯噪声）采样
        
        参数:
            shape: 采样形状
            
        返回:
            纯噪声样本
        """
        return np.random.randn(*shape)
    
    def sample_at_arbitrary_t(self, x_0: np.ndarray, t: int) -> np.ndarray:
        """
        任意时间步的闭式采样
        
        参数:
            x_0: 原始图像
            t: 时间步
            
        返回:
            x_t
        """
        alpha_bar_t = self.alpha_bars[t]
        
        epsilon = np.random.randn(*x_0.shape)
        x_t = np.sqrt(alpha_bar_t) * x_0 + np.sqrt(1 - alpha_bar_t) * epsilon
        
        return x_t
    
    def variance(self, t: int) -> float:
        """
        获取时间步t的噪声方差
        
        参数:
            t: 时间步
            
        返回:
            beta_t
        """
        return self.betas[t]


class ForwardProcessBatch:
    """
    批量前向过程（用于训练）
    
    一次生成多个时间步的噪声样本
    """
    
    def __init__(self, schedule: DiffusionSchedule, image_size: int = 32, 
                 channels: int = 3):
        self.schedule = schedule
        self.image_size = image_size
        self.channels = channels
        self.T = schedule.T
    
    def sample(self, x_0: np.ndarray, batch_size: int = 32) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        批量采样训练数据
        
        参数:
            x_0: 原始图像 (B, C, H, W)
            batch_size: 批量大小
            
        返回:
            (x_t, t, epsilon) 元组
        """
        batch = x_0[:batch_size] if len(x_0) >= batch_size else x_0
        actual_batch = len(batch)
        
        # 随机采样时间步
        t = np.random.randint(0, self.T, size=actual_batch)
        
        # 生成噪声
        epsilon = np.random.randn(*batch.shape)
        
        # 计算x_t
        alpha_bars_t = self.schedule.alpha_bars[t].reshape(actual_batch, 1, 1, 1)
        sqrt_alpha_bar = np.sqrt(alpha_bars_t)
        sqrt_one_minus_alpha_bar = np.sqrt(1 - alpha_bars_t)
        
        x_t = sqrt_alpha_bar * batch + sqrt_one_minus_alpha_bar * epsilon
        
        return x_t, t, epsilon


class ContinuousTimeExtension:
    """
    连续时间扩散扩展
    
    将离散扩散过程推广到连续时间
    d x(t) = f(t) x(t) dt + g(t) dW(t)
    
    其中 f(t) = -0.5 * beta(t), g(t) = sqrt(beta(t))
    """
    
    def __init__(self, beta_func: Callable):
        """
        参数:
            beta_func: 连续的beta函数 beta(t)
        """
        self.beta_func = beta_func
    
    def sample_at_time(self, x_0: np.ndarray, t: float) -> np.ndarray:
        """
        连续时间采样
        
        参数:
            x_0: 原始图像
            t: 连续时间 (0 <= t <= 1)
            
        返回:
            x(t)
        """
        # 数值积分计算bar_alpha(t)
        from scipy.integrate import quad
        
        def integrand(s):
            return self.beta_func(s)
        
        integral, _ = quad(integrand, 0, t)
        bar_alpha_t = np.exp(-integral)
        
        alpha_t = np.exp(-self.beta_func(t))
        
        epsilon = np.random.randn(*x_0.shape)
        x_t = np.sqrt(bar_alpha_t) * x_0 + np.sqrt(1 - bar_alpha_t) * epsilon
        
        return x_t


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DDPM前向过程测试")
    print("=" * 60)
    
    # 测试1：不同调度策略
    print("\n1. 不同噪声调度策略:")
    
    for schedule_type in ['linear', 'cosine', 'sqrt']:
        schedule = DiffusionSchedule(T=100, beta_start=1e-4, 
                                    beta_end=0.02, schedule_type=schedule_type)
        print(f"   {schedule_type}: beta_0={schedule.betas[0]:.6f}, "
              f"beta_T={schedule.betas[-1]:.6f}")
    
    # 测试2：前向过程
    print("\n2. 前向过程单步加噪:")
    
    schedule = DiffusionSchedule(T=1000)
    fp = ForwardProcess(schedule)
    
    # 模拟图像
    x_0 = np.random.rand(1, 3, 32, 32)
    
    # 渐进加噪
    steps_to_show = [0, 100, 500, 999]
    for t in steps_to_show:
        x_t, _ = fp.step_with_noise(x_0, t)
        mean_val = np.mean(x_t)
        var_val = np.var(x_t)
        print(f"   t={t}: 均值={mean_val:.4f}, 方差={var_val:.4f}")
    
    # 测试3：闭式采样
    print("\n3. 任意时间步闭式采样:")
    
    x_0_test = np.random.rand(3, 3, 8, 8)
    for t in [0, 50, 500, 999]:
        x_t = fp.sample_at_arbitrary_t(x_0_test, t)
        print(f"   t={t}: x_t形状={x_t.shape}, "
              f"与x_0相关性≈{np.corrcoef(x_0_test.flatten(), x_t.flatten())[0,1]:.4f}")
    
    # 测试4：批量采样
    print("\n4. 批量前向过程采样:")
    
    batch_fp = ForwardProcessBatch(schedule, image_size=8, channels=3)
    
    x_0_batch = np.random.rand(64, 3, 8, 8)
    x_t, t, epsilon = batch_fp.sample(x_0_batch, batch_size=32)
    
    print(f"   x_t形状: {x_t.shape}")
    print(f"   t范围: [{t.min()}, {t.max()}]")
    print(f"   epsilon形状: {epsilon.shape}")
    
    # 测试5：连续时间扩展
    print("\n5. 连续时间扩散:")
    
    # 线性beta函数
    def linear_beta(t):
        return 0.02 * t + 1e-4
    
    cont_fp = ContinuousTimeExtension(linear_beta)
    
    x_0_cont = np.random.rand(1, 3, 8, 8)
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x_t = cont_fp.sample_at_time(x_0_cont, t)
        var = np.var(x_t)
        print(f"   t={t:.2f}: x_t方差={var:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
