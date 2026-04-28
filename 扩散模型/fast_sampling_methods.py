"""
快速采样方法：PNDM/EDM/UniPC
Fast Sampling Methods: PNDM, EDM, UniPC

快速采样方法通过减少采样步数来加速扩散模型推理。
PNDM使用伪线性多步方法，EDM使用随机微分方程框架的优化，UniPC使用预测-校正框架。
"""

import numpy as np
from typing import Callable, Tuple, Optional
from abc import ABC, abstractmethod


class DiffusionSampler(ABC):
    """
    扩散模型采样器基类
    
    参数:
        model: 去噪模型
        betas: beta调度
        T: 总步数
    """
    
    def __init__(self, model: Callable, betas: np.ndarray):
        self.model = model
        self.betas = betas
        self.alphas = 1 - betas
        self.alpha_bars = np.cumprod(self.alphas)
        self.T = len(betas)
    
    @abstractmethod
    def sample(self, shape: Tuple, **kwargs) -> np.ndarray:
        """采样方法"""
        pass


class EulerSampler(DiffusionSampler):
    """
    Euler采样器（基础方法）
    
    最简单的采样器，Euler-Maruyama方法
    """
    
    def sample(self, shape: Tuple, n_steps: int = 50) -> np.ndarray:
        """
        Euler采样
        
        参数:
            shape: 采样形状
            n_steps: 采样步数
        """
        x = np.random.randn(*shape)
        dt = 1.0 / n_steps
        
        for i in range(n_steps):
            t = 1.0 - i * dt
            t_idx = min(int((1 - t) * self.T), self.T - 1)
            
            # 预测噪声
            noise_pred = self.model(x, t_idx)
            
            # Euler更新
            x = x - noise_pred * dt
        
        return x


class HeunSampler(DiffusionSampler):
    """
    Heun二阶采样器
    
    比Euler更精确，使用两步预测
    
    参数:
        model: 去噪模型
        betas: beta调度
    """
    
    def sample(self, shape: Tuple, n_steps: int = 50) -> np.ndarray:
        """
        Heun采样
        
        参数:
            shape: 采样形状
            n_steps: 采样步数
        """
        x = np.random.randn(*shape)
        dt = 1.0 / n_steps
        
        for i in range(n_steps):
            t = 1.0 - i * dt
            t_idx = min(int((1 - t) * self.T), self.T - 1)
            
            # 第一步预测
            noise_pred_1 = self.model(x, t_idx)
            x_temp = x - noise_pred_1 * dt
            
            # 第二步预测
            noise_pred_2 = self.model(x_temp, t_idx - 1 if t_idx > 0 else 0)
            
            # Heun校正
            x = x - 0.5 * (noise_pred_1 + noise_pred_2) * dt
        
        return x


class PNDMSampler(DiffusionSampler):
    """
    伪线性多步扩散采样器 (PNDM)
    
    通过外推历史预测来提高采样质量
    可以用更少的步数达到好的效果
    
    参数:
        model: 去噪模型
        betas: beta调度
    """
    
    def __init__(self, model: Callable, betas: np.ndarray):
        super().__init__(model, betas)
        self.history = []  # 历史预测
    
    def sample(self, shape: Tuple, n_steps: int = 50, 
               corrector_steps: int = 1) -> np.ndarray:
        """
        PNDM采样
        
        参数:
            shape: 采样形状
            n_steps: 采样步数
            corrector_steps: 校正器步数
        """
        x = np.random.randn(*shape)
        self.history = []
        
        dt = 1.0 / n_steps
        
        for i in range(n_steps):
            t = 1.0 - i * dt
            t_idx = min(int((1 - t) * self.T), self.T - 1)
            
            # 预测当前噪声
            noise_pred = self.model(x, t_idx)
            
            # PNDM外推
            if len(self.history) >= 4:
                # 使用历史预测的外推
                noise_pred = self._pn_extrapolate(noise_pred)
            
            # 更新
            x = x - noise_pred * dt
            
            # 存储历史
            self.history.append(noise_pred)
            if len(self.history) > 4:
                self.history.pop(0)
        
        return x
    
    def _pn_extrapolate(self, noise_pred: np.ndarray) -> np.ndarray:
        """
        PNDM外推公式
        
        参数:
            noise_pred: 当前预测
            
        返回:
            外推后的预测
        """
        # PNDM系数（基于Taylor展开）
        if len(self.history) == 4:
            # 4阶PNDM
            extrapolated = (
                1.5 * self.history[-1] - 
                0.6 * self.history[-2] + 
                0.1 * self.history[-3]
            )
        else:
            extrapolated = noise_pred
        
        return extrapolated


class EDMSampler(DiffusionSampler):
    """
    EDM (Elucidating the Design Space of Diffusion Models) 采样器
    
    使用SDE框架的统一采样方法
    
    参数:
        model: 去噪模型
        sigma_min: 最小sigma
        sigma_max: 最大sigma
    """
    
    def __init__(self, model: Callable, betas: np.ndarray,
                 sigma_min: float = 0.002, sigma_max: float = 80.0):
        super().__init__(model, betas)
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
    
    def sample(self, shape: Tuple, n_steps: int = 50,
               rho: float = 7.0) -> np.ndarray:
        """
        EDM采样
        
        参数:
            shape: 采样形状
            n_steps: 采样步数
            rho: 调度指数
        """
        # EDM风格的调度
        step_indices = np.arange(n_steps)
        
        # 时间步
        t_steps = (self.sigma_max ** (1/rho) + 
                   step_indices / (n_steps - 1) * 
                   (self.sigma_min ** (1/rho) - self.sigma_max ** (1/rho))) ** rho
        
        # 从高sigma开始
        x = np.random.randn(*shape) * self.sigma_max
        
        for i, t_curr in enumerate(t_steps):
            t_next = t_steps[i + 1] if i < len(t_steps) - 1 else 0.0
            
            # EDM去噪
            x = self._edm_step(x, t_curr, t_next)
        
        return x
    
    def _edm_step(self, x: np.ndarray, 
                 t_curr: float, t_next: float) -> np.ndarray:
        """
        单步EDM更新
        
        参数:
            x: 当前状态
            t_curr: 当前时间
            t_next: 下一时间
        """
        # 预测噪声
        t_idx = min(int(t_curr * self.T), self.T - 1)
        noise_pred = self.model(x, t_idx)
        
        # EDM更新
        d = (x - noise_pred) / t_curr
        
        # 第二阶校正
        dt = t_next - t_curr
        
        x_next = x + d * dt
        
        # 可选的随机性
        if t_next > 0:
            x_next = x_next + np.random.randn(*x.shape) * np.sqrt(dt) * 0.1
        
        return x_next


class UniPCSampler(DiffusionSampler):
    """
    UniPC (Unified Predictor-Corrector) 采样器
    
    结合预测器和校正器的统一框架
    
    参数:
        model: 去噪模型
        betas: beta调度
    """
    
    def __init__(self, model: Callable, betas: np.ndarray):
        super().__init__(model, betas)
    
    def sample(self, shape: Tuple, n_steps: int = 50) -> np.ndarray:
        """
        UniPC采样
        
        参数:
            shape: 采样形状
            n_steps: 采样步数
        """
        x = np.random.randn(*shape)
        
        # 时间步（使用余弦调度）
        timesteps = self._cosine_schedule(n_steps)
        
        for i in range(n_steps):
            t = timesteps[i]
            t_next = timesteps[i + 1] if i < n_steps - 1 else 0
            
            # 预测器
            x = self._predictor_step(x, t, t_next)
            
            # 校正器
            x = self._corrector_step(x, t, t_next)
        
        return x
    
    def _cosine_schedule(self, n_steps: int) -> np.ndarray:
        """余弦时间调度"""
        s = 0.008
        steps = np.arange(n_steps + 1)
        f = np.cos((steps / n_steps + s) / (1 + s) * np.pi / 2) ** 2
        return f / f[0]
    
    def _predictor_step(self, x: np.ndarray, 
                       t: float, t_next: float) -> np.ndarray:
        """UniPC预测器"""
        # 获取模型预测
        t_idx = min(int(t * self.T), self.T - 1)
        noise_pred = self.model(x, t_idx)
        
        # 简化的预测器更新
        alpha_t = self.alpha_bars[t_idx] if t_idx < len(self.alpha_bars) else 0
        alpha_next = self.alpha_bars[t_idx - 1] if t_idx > 0 else 1.0
        
        x_0_pred = (x - np.sqrt(1 - alpha_t) * noise_pred) / np.sqrt(alpha_t + 1e-6)
        
        # 一阶近似
        x = np.sqrt(alpha_next) * x_0_pred + np.sqrt(1 - alpha_next) * noise_pred
        
        return x
    
    def _corrector_step(self, x: np.ndarray, 
                       t: float, t_next: float) -> np.ndarray:
        """UniPC校正器"""
        # 简化的校正器
        t_idx = min(int(t * self.T), self.T - 1)
        noise_pred = self.model(x, t_idx)
        
        # 小的校正
        x = x - 0.1 * noise_pred * (t - t_next)
        
        return x


class DPMPlusPlusarser(DiffusionSampler):
    """
    DPM++ (Diffusion Probabilistic Models++) 采样器
    
    参数:
        model: 去噪模型
        betas: beta调度
        order: 方法阶数 (1, 2)
    """
    
    def __init__(self, model: Callable, betas: np.ndarray, order: int = 2):
        super().__init__(model, betas)
        self.order = order
        self.noise_history = []
    
    def sample(self, shape: Tuple, n_steps: int = 50) -> np.ndarray:
        """
        DPM++采样
        """
        x = np.random.randn(*shape)
        self.noise_history = []
        
        dt = 1.0 / n_steps
        
        for i in range(n_steps):
            t = 1.0 - i * dt
            t_idx = min(int((1 - t) * self.T), self.T - 1)
            
            # 预测
            noise_pred = self.model(x, t_idx)
            
            # DPM++ 更新
            if self.order == 2 and len(self.noise_history) >= 1:
                # 二阶方法
                alpha = 0.5  # 简化的系数
                noise_pred = (1 + alpha) * noise_pred - alpha * self.noise_history[-1]
            
            self.noise_history.append(noise_pred)
            if len(self.noise_history) > 2:
                self.noise_history.pop(0)
            
            x = x - noise_pred * dt
        
        return x


class FastSamplerComparison:
    """
    快速采样器对比工具
    """
    
    @staticmethod
    def compare_speeds() -> dict:
        """对比各采样器的速度"""
        return {
            'DDPM': {'steps': 1000, 'speed': '1x', 'quality': 'high'},
            'DDIM': {'steps': 50, 'speed': '20x', 'quality': 'high'},
            'PNDM': {'steps': 50, 'speed': '20x', 'quality': 'very_high'},
            'EDM': {'steps': 50, 'speed': '20x', 'quality': 'very_high'},
            'UniPC': {'steps': 20, 'speed': '50x', 'quality': 'high'},
            'DPM++': {'steps': 20, 'speed': '50x', 'quality': 'very_high'},
            'Heun': {'steps': 30, 'speed': '33x', 'quality': 'high'},
        }


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("快速采样方法测试 (PNDM/EDM/UniPC)")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 模拟去噪模型
    class MockDenoiser:
        def __call__(self, x, t):
            # 简化的去噪：向原点靠近
            return x * 0.05 + np.random.randn(*x.shape) * 0.01
    
    model = MockDenoiser()
    
    # Beta调度
    T = 1000
    betas = np.linspace(1e-4, 0.02, T)
    
    # 测试1：速度对比
    print("\n1. 快速采样器速度对比:")
    
    comparison = FastSamplerComparison.compare_speeds()
    for name, info in comparison.items():
        print(f"   {name}: {info['steps']}步, 速度{info['speed']}, 质量{info['quality']}")
    
    # 测试2：Euler采样器
    print("\n2. Euler采样器:")
    
    euler = EulerSampler(model, betas)
    x = euler.sample(shape=(2, 3, 32, 32), n_steps=10)
    print(f"   输出形状: {x.shape}")
    print(f"   输出均值: {np.mean(x):.6f}")
    
    # 测试3：Heun采样器
    print("\n3. Heun二阶采样器:")
    
    heun = HeunSampler(model, betas)
    x = heun.sample(shape=(2, 3, 32, 32), n_steps=10)
    print(f"   输出形状: {x.shape}")
    print(f"   输出均值: {np.mean(x):.6f}")
    
    # 测试4：PNDM采样器
    print("\n4. PNDM采样器:")
    
    pndm = PNDMSampler(model, betas)
    x = pndm.sample(shape=(2, 3, 32, 32), n_steps=10)
    print(f"   输出形状: {x.shape}")
    print(f"   历史长度: {len(pndm.history)}")
    
    # 测试5：EDM采样器
    print("\n5. EDM采样器:")
    
    edm = EDMSampler(model, betas, sigma_min=0.002, sigma_max=80.0)
    x = edm.sample(shape=(2, 3, 32, 32), n_steps=10)
    print(f"   输出形状: {x.shape}")
    print(f"   输出范围: [{x.min():.4f}, {x.max():.4f}]")
    
    # 测试6：UniPC采样器
    print("\n6. UniPC采样器:")
    
    unipc = UniPCSampler(model, betas)
    x = unipc.sample(shape=(2, 3, 32, 32), n_steps=10)
    print(f"   输出形状: {x.shape}")
    print(f"   输出均值: {np.mean(x):.6f}")
    
    # 测试7：DPM++采样器
    print("\n7. DPM++采样器:")
    
    dpmpp = DPMPlusPlusarser(model, betas, order=2)
    x = dpmpp.sample(shape=(2, 3, 32, 32), n_steps=10)
    print(f"   输出形状: {x.shape}")
    print(f"   噪声历史长度: {len(dpmpp.noise_history)}")
    
    # 测试8：收敛性分析
    print("\n8. 收敛性分析:")
    
    initial_var = np.var(np.random.randn(100, 3, 32, 32))
    final_var = np.var(x)
    
    print(f"   初始方差: {initial_var:.4f}")
    print(f"   最终方差: {final_var:.4f}")
    print(f"   方差减少: {(1 - final_var/initial_var)*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
