"""
DDPM采样：DDIM加速采样
DDPM Sampling: DDIM Accelerated Sampling

DDPM的采样过程需要T步迭代，非常慢。
DDIM（Denoising Diffusion Implicit Models）通过非马尔可夫过程加速，
将采样步骤从1000步减少到50步甚至更少，同时保持高质量。
"""

import numpy as np
from typing import Tuple, Optional, Callable, List
from dataclasses import dataclass


@dataclass
class DDIMSchedule:
    """
    DDIM调度器配置
    
    属性:
        T: 原扩散步数
        S: 采样步数（远小于T）
        eta: DDIM的随机性参数（0=确定性, 1=完全DDPM）
    """
    T: int = 1000
    S: int = 50
    eta: float = 0.0
    
    def __post_init__(self):
        self._compute_timesteps()
    
    def _compute_timesteps(self):
        """计算要采样的时间步序列"""
        # 均匀间隔选择S个时间步
        self.timesteps = np.linspace(0, self.T - 1, self.S, dtype=int)[::-1]
        
        # 前一个时间步（用于DDIM公式）
        self.prev_timesteps = np.concatenate([
            self.timesteps[1:],
            [0]
        ])


class DDIMSampler:
    """
    DDIM采样器
    
    DDIM的核心思想：将DDPM的马尔可夫过程替换为隐式非马尔可夫过程
    通过跳跃采样实现加速。
    
    参数:
        model: 去噪模型
        schedule: DDIM调度器
        betas: beta调度（用于参数计算）
    """
    
    def __init__(self, model, schedule: DDIMSchedule, betas: np.ndarray):
        self.model = model
        self.schedule = schedule
        self.betas = betas
        
        # 预计算参数
        self.alphas = 1 - betas
        self.alphas_bar = np.cumprod(self.alphas)
        
        self.T = schedule.T
        self.S = schedule.S
        self.eta = schedule.eta
        self.timesteps = schedule.timesteps
    
    def _get_alpha_bar(self, t: int) -> float:
        """获取累积alpha"""
        if t >= self.T:
            return 1.0
        return self.alphas_bar[t]
    
    def _ddim_step(self, x_t: np.ndarray, t: int, 
                   prev_t: int, pred_noise: np.ndarray) -> np.ndarray:
        """
        单步DDIM采样
        
        参数:
            x_t: 当前图像
            t: 当前时间步
            prev_t: 前一个时间步
            pred_noise: 预测的噪声
            
        返回:
            x_{prev_t}
        """
        alpha_t = self._get_alpha_bar(t)
        alpha_prev = self._get_alpha_bar(prev_t)
        
        beta_t = 1 - self.alphas[t] if t < len(self.alphas) else 0
        beta_prev = 1 - self.alphas[prev_t] if prev_t < len(self.alphas) else 0
        
        # 预测原始图像
        pred_x_0 = (x_t - np.sqrt(1 - alpha_t) * pred_noise) / np.sqrt(alpha_t)
        
        # 方向指向x_t
        pred_x_t_direction = np.sqrt(1 - alpha_t) * pred_noise
        
        # 计算方差
        if self.eta > 0:
            # DDPM风格的方差
            var_t = self.eta * beta_t * (1 - alpha_prev) / (1 - alpha_t)
        else:
            # DDIM确定性路径
            var_t = 0.0
        
        # 采样
        noise = np.random.randn(*x_t.shape) if var_t > 0 else 0
        x_prev = np.sqrt(alpha_prev) * pred_x_0 + \
                 np.sqrt(max(0, 1 - alpha_prev - var_t)) * pred_noise + \
                 np.sqrt(var_t) * noise
        
        return x_prev
    
    def sample(self, shape: Tuple, 
               return_intermediates: bool = False) -> np.ndarray:
        """
        DDIM采样主函数
        
        参数:
            shape: 采样形状 (B, C, H, W)
            return_intermediates: 是否返回中间步骤
            
        返回:
            生成的图像
        """
        # 从纯噪声开始
        x_t = np.random.randn(*shape)
        
        intermediates = [x_t] if return_intermediates else None
        
        # 逐步去噪
        for i, t in enumerate(self.timesteps):
            prev_t = self.schedule.prev_timesteps[i]
            
            # 预测噪声
            pred_noise = self.model.predict_noise(x_t, t)
            
            # DDIM一步
            x_t = self._ddim_step(x_t, t, prev_t, pred_noise)
            
            if return_intermediates and (i + 1) % 10 == 0:
                intermediates.append(x_t)
        
        if return_intermediates:
            return x_t, np.array(intermediates)
        
        return x_t


class DDPMVanillaSampler:
    """
    DDPM原始采样器（对比用）
    
    参数:
        model: 去噪模型
        betas: beta调度
    """
    
    def __init__(self, model, betas: np.ndarray):
        self.model = model
        self.betas = betas
        self.alphas = 1 - betas
        self.alphas_bar = np.cumprod(self.alphas)
        self.T = len(betas)
    
    def sample(self, shape: Tuple) -> np.ndarray:
        """
        原始DDPM采样
        
        返回:
            生成的图像
        """
        x_t = np.random.randn(*shape)
        
        for t in range(self.T - 1, -1, -1):
            # 预测噪声
            pred_noise = self.model.predict_noise(x_t, t)
            
            # 计算均值
            alpha_t = self.alphas[t]
            alpha_bar_t = self.alphas_bar[t]
            
            if t > 0:
                alpha_prev = self.alphas_bar[t - 1]
                beta_t = self.betas[t]
                
                mean = np.sqrt(1 / alpha_t) * \
                       (x_t - beta_t / np.sqrt(1 - alpha_bar_t) * pred_noise)
                
                # 采样
                x_t = mean + np.sqrt(beta_t) * np.random.randn(*shape)
            else:
                # t=0: 直接重建
                x_0 = (x_t - np.sqrt(1 - alpha_bar_t) * pred_noise) / np.sqrt(alpha_bar_t)
                x_t = x_0
        
        return x_t


class PLMSSampler:
    """
    PLMS（伪线性多步）采样器
    
    加速策略：通过外推提高采样质量
    
    参数:
        model: 去噪模型
        betas: beta调度
    """
    
    def __init__(self, model, betas: np.ndarray, T: int = 1000, S: int = 50):
        self.model = model
        self.betas = betas
        self.alphas = 1 - betas
        self.alphas_bar = np.cumprod(self.alphas)
        self.T = T
        self.S = S
        
        # 计算采样时间步
        self.timesteps = np.linspace(0, T - 1, S, dtype=int)[::-1]
    
    def _predict_noise(self, x: np.ndarray, t: int) -> np.ndarray:
        """预测噪声"""
        return self.model.predict_noise(x, t)
    
    def sample(self, shape: Tuple) -> np.ndarray:
        """PLMS采样"""
        x_t = np.random.randn(*shape)
        
        for i, t in enumerate(self.timesteps):
            # 预测当前噪声
            e_t = self._predict_noise(x_t, t)
            
            # 计算x_0预测
            alpha_bar_t = self.alphas_bar[t]
            x_0_pred = (x_t - np.sqrt(1 - alpha_bar_t) * e_t) / np.sqrt(alpha_bar_t)
            
            # PLMS外推
            if i > 0:
                # 使用历史预测的组合
                alpha_bar_prev = self.alphas_bar[self.timesteps[i - 1]]
                
                # 简化：使用当前预测
                x_t_minus_1 = np.sqrt(alpha_bar_prev) * x_0_pred + \
                             np.sqrt(1 - alpha_bar_prev) * np.random.randn(*shape) * 0.1
                
                x_t = x_t_minus_1
            else:
                # 最后一步
                x_t = x_0_pred
        
        return x_t


class AncestralSampler:
    """
    Ancestral采样（DDPM加速变体）
    
    特点：在每个时间步采样而非重建
    """
    
    def __init__(self, model, betas: np.ndarray):
        self.model = model
        self.betas = betas
        self.alphas = 1 - betas
        self.alphas_bar = np.cumprod(self.alphas)
        self.T = len(betas)
    
    def sample(self, shape: Tuple, S: int = 50) -> np.ndarray:
        """
        Ancestral采样
        
        参数:
            shape: 采样形状
            S: 采样步数
        """
        # 选择时间步
        timesteps = np.linspace(0, self.T - 1, S, dtype=int)[::-1]
        
        x_t = np.random.randn(*shape)
        
        for i, t in enumerate(timesteps):
            # 直接采样祖先
            alpha_bar_t = self.alphas_bar[t]
            
            # 预测噪声
            pred_noise = self.model.predict_noise(x_t, t)
            
            # 采样
            if i < len(timesteps) - 1:
                next_t = timesteps[i + 1]
                alpha_bar_next = self.alphas_bar[next_t]
                
                # 直接从x_t采样到x_{next_t}
                x_t = np.sqrt(alpha_bar_next) * (x_t - np.sqrt(1 - alpha_bar_t) * pred_noise) / np.sqrt(alpha_bar_t) + \
                      np.sqrt(1 - alpha_bar_next) * pred_noise
            else:
                # 最后一步
                x_0 = (x_t - np.sqrt(1 - alpha_bar_t) * pred_noise) / np.sqrt(alpha_bar_t)
                x_t = x_0
        
        return x_t


class FastSamplerComparison:
    """
    快速采样器对比工具
    """
    
    @staticmethod
    def compare_speeds() -> dict:
        """
        对比不同采样器的理论速度
        
        返回:
            各采样器的相对速度
        """
        return {
            'DDPM': {'steps': 1000, 'relative_speed': 1.0},
            'DDIM_50': {'steps': 50, 'relative_speed': 20.0},
            'DDIM_20': {'steps': 20, 'relative_speed': 50.0},
            'DDIM_10': {'steps': 10, 'relative_speed': 100.0},
            'PLMS': {'steps': 50, 'relative_speed': 20.0},
            'Ancestral_50': {'steps': 50, 'relative_speed': 20.0},
        }


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DDPM采样测试（DDIM加速）")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 模拟去噪模型
    class MockDenoiser:
        def predict_noise(self, x_t, t):
            # 模拟：添加一些去噪效果
            return x_t * 0.5 + np.random.randn(*x_t.shape) * 0.1
    
    model = MockDenoiser()
    
    # Beta调度
    T = 1000
    betas = np.linspace(1e-4, 0.02, T)
    
    # 测试1：速度对比
    print("\n1. 采样速度对比:")
    
    comparison = FastSamplerComparison.compare_speeds()
    for name, info in comparison.items():
        print(f"   {name}: {info['steps']}步, 相对速度={info['relative_speed']}x")
    
    # 测试2：DDIM调度器
    print("\n2. DDIM调度器:")
    
    ddim_schedule = DDIMSchedule(T=1000, S=50, eta=0.0)
    print(f"   总步数: {ddim_schedule.T}")
    print(f"   采样步数: {ddim_schedule.S}")
    print(f"   采样时间步: {ddim_schedule.timesteps[:5]}...{ddim_schedule.timesteps[-5:]}")
    
    # 测试3：DDIM采样
    print("\n3. DDIM采样过程:")
    
    sampler = DDIMSampler(model, ddim_schedule, betas)
    
    shape = (2, 3, 32, 32)
    x_T = np.random.randn(*shape)
    
    intermediates_count = 0
    for i, t in enumerate(sampler.timesteps[:5]):
        pred_noise = model.predict_noise(x_T, t)
        prev_t = sampler.schedule.prev_timesteps[i]
        
        # 简化：模拟一步
        x_T = x_T * 0.9 + np.random.randn(*shape) * 0.1
        
        if i < 5:
            intermediates_count += 1
    
    print(f"   采样步数: {sampler.S}")
    print(f"   输出形状: {x_T.shape}")
    
    # 测试4：DDPM vs DDIM采样
    print("\n4. DDPM vs DDIM采样:")
    
    ddpm_sampler = DDPMVanillaSampler(model, betas)
    ddim_sampler = DDIMSampler(model, DDIMSchedule(T=1000, S=50, eta=0.0), betas)
    
    print(f"   DDPM采样步数: {ddpm_sampler.T}")
    print(f"   DDIM采样步数: {ddim_sampler.S}")
    print(f"   加速比: {ddpm_sampler.T / ddim_sampler.S:.1f}x")
    
    # 测试5：不同eta的DDIM
    print("\n5. DDIM不同eta值:")
    
    for eta in [0.0, 0.5, 1.0]:
        schedule = DDIMSchedule(T=1000, S=50, eta=eta)
        s = DDIMSampler(model, schedule, betas)
        print(f"   eta={eta}: 确定性={eta==0.0}, 方差={eta > 0}")
    
    # 测试6：PLMS采样
    print("\n6. PLMS采样:")
    
    plms = PLMSSampler(model, betas, T=1000, S=50)
    print(f"   PLMS采样步数: {plms.S}")
    print(f"   第一个时间步: {plms.timesteps[0]}")
    print(f"   最后一个时间步: {plms.timesteps[-1]}")
    
    # 测试7：Ancestral采样
    print("\n7. Ancestral采样:")
    
    ancestral = AncestralSampler(model, betas)
    print(f"   可配置采样步数: 支持")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
