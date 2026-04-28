"""
噪声调度：余弦调度与线性调度
Noise Schedule: Cosine and Linear Scheduling

噪声调度决定了扩散模型中噪声如何随时间添加/去除。
好的调度可以显著提高采样质量和速度。
"""

import numpy as np
from typing import Callable, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass


class NoiseSchedule(ABC):
    """
    噪声调度基类
    
    参数:
        T: 总时间步数
    """
    
    def __init__(self, T: int = 1000):
        self.T = T
        self._compute_schedule()
    
    @abstractmethod
    def _compute_schedule(self):
        """计算调度参数"""
        pass
    
    @abstractmethod
    def beta(self, t: int) -> float:
        """获取时间步t的beta"""
        pass
    
    @abstractmethod
    def alpha(self, t: int) -> float:
        """获取时间步t的alpha"""
        pass
    
    @abstractmethod
    def alpha_bar(self, t: int) -> float:
        """获取累积alpha"""
        pass
    
    def get_all_betas(self) -> np.ndarray:
        """获取所有beta值"""
        return np.array([self.beta(t) for t in range(self.T)])
    
    def get_all_alphas(self) -> np.ndarray:
        """获取所有alpha值"""
        return np.array([self.alpha(t) for t in range(self.T)])
    
    def get_all_alpha_bars(self) -> np.ndarray:
        """获取所有累积alpha值"""
        return np.array([self.alpha_bar(t) for t in range(self.T)])


class LinearSchedule(NoiseSchedule):
    """
    线性噪声调度
    
    beta_t 从 beta_0 线性增长到 beta_T
    
    参数:
        T: 总步数
        beta_start: 起始beta值
        beta_end: 结束beta值
    """
    
    def __init__(self, T: int = 1000, beta_start: float = 1e-4, 
                 beta_end: float = 0.02):
        self.beta_start = beta_start
        self.beta_end = beta_end
        super().__init__(T)
    
    def _compute_schedule(self):
        """计算线性调度的参数"""
        self._betas = np.linspace(self.beta_start, self.beta_end, self.T)
        self._alphas = 1 - self._betas
        self._alpha_bars = np.cumprod(self._alphas)
    
    def beta(self, t: int) -> float:
        return self._betas[t]
    
    def alpha(self, t: int) -> float:
        return self._alphas[t]
    
    def alpha_bar(self, t: int) -> float:
        return self._alpha_bars[t]


class CosineSchedule(NoiseSchedule):
    """
    余弦噪声调度
    
    基于 cosine 衰减，采样更平滑
    
    参数:
        T: 总步数
        s: 偏移参数 (通常 0.008)
    """
    
    def __init__(self, T: int = 1000, s: float = 0.008):
        self.s = s
        super().__init__(T)
    
    def _compute_schedule(self):
        """计算余弦调度的参数"""
        # 计算 alpha_bar(t)
        steps = np.arange(self.T + 1)
        
        # cosine 公式
        f_t = np.cos((steps / self.T + self.s) / (1 + self.s) * np.pi / 2) ** 2
        f_0 = f_t[0]
        
        # alpha_bar_t = f_t / f_0
        alpha_bars = f_t / f_0
        
        # beta_t = 1 - alpha_t = 1 - alpha_bar_t / alpha_bar_{t-1}
        alphas = alpha_bars[1:] / alpha_bars[:-1]
        alphas = np.clip(alphas, 0, 1)
        
        betas = 1 - alphas
        
        self._alpha_bars = alpha_bars[1:]  # 从 t=1 开始的累积
        self._alphas = alphas
        self._betas = betas
    
    def beta(self, t: int) -> float:
        return self._betas[t]
    
    def alpha(self, t: int) -> float:
        return self._alphas[t]
    
    def alpha_bar(self, t: int) -> float:
        return self._alpha_bars[t]


class SqrtSchedule(NoiseSchedule):
    """
    平方根噪声调度
    
    beta_t ∝ sqrt(t)
    
    参数:
        T: 总步数
        beta_start: 起始beta
        beta_end: 结束beta
    """
    
    def __init__(self, T: int = 1000, beta_start: float = 1e-4, 
                 beta_end: float = 0.02):
        self.beta_start = beta_start
        self.beta_end = beta_end
        super().__init__(T)
    
    def _compute_schedule(self):
        """计算平方根调度"""
        t = np.arange(self.T)
        
        # beta(t) = (sqrt(t+1) - sqrt(t)) * scale
        sqrt_t = np.sqrt(t + 1) - np.sqrt(t)
        
        # 归一化到目标范围
        scale = (self.beta_end - self.beta_start) / (sqrt_t[-1] - sqrt_t[0])
        
        self._betas = self.beta_start + (sqrt_t - sqrt_t[0]) * scale
        self._betas = np.clip(self._betas, 0, 0.999)
        
        self._alphas = 1 - self._betas
        self._alpha_bars = np.cumprod(self._alphas)
    
    def beta(self, t: int) -> float:
        return self._betas[t]
    
    def alpha(self, t: int) -> float:
        return self._alphas[t]
    
    def alpha_bar(self, t: int) -> float:
        return self._alpha_bars[t]


class ExponentialSchedule(NoiseSchedule):
    """
    指数噪声调度
    
    alpha_bar_t = exp(-gamma * t)
    
    参数:
        T: 总步数
        gamma: 衰减率
    """
    
    def __init__(self, T: int = 1000, gamma: float = 0.0001):
        self.gamma = gamma
        super().__init__(T)
    
    def _compute_schedule(self):
        """计算指数调度"""
        t = np.arange(self.T)
        
        # alpha_bar_t = exp(-gamma * t)
        self._alpha_bars = np.exp(-self.gamma * t)
        
        # 反推 alpha 和 beta
        alphas = np.zeros(self.T)
        alphas[0] = self._alpha_bars[0]
        for t in range(1, self.T):
            alphas[t] = self._alpha_bars[t] / self._alpha_bars[t - 1]
        
        self._alphas = alphas
        self._betas = 1 - alphas
    
    def beta(self, t: int) -> float:
        return self._betas[t]
    
    def alpha(self, t: int) -> float:
        return self._alphas[t]
    
    def alpha_bar(self, t: int) -> float:
        return self._alpha_bars[t]


class PolynomialSchedule(NoiseSchedule):
    """
    多项式噪声调度
    
    alpha_bar_t = (1 - (t/T)^p) / (1 - (T/T)^p) = (1 - (t/T)^p) / (1 - 1^p) ... 
    简化为: alpha_bar_t = (1 - t/T)^p
    
    参数:
        T: 总步数
        p: 多项式阶数
    """
    
    def __init__(self, T: int = 1000, p: float = 2.0):
        self.p = p
        super().__init__(T)
    
    def _compute_schedule(self):
        """计算多项式调度"""
        t = np.arange(self.T)
        
        # alpha_bar_t = (1 - t/T)^p
        self._alpha_bars = (1 - t / self.T) ** self.p
        
        # 反推
        alphas = np.zeros(self.T)
        alphas[0] = self._alpha_bars[0]
        for t in range(1, self.T):
            alphas[t] = self._alpha_bars[t] / max(self._alpha_bars[t - 1], 1e-10)
        
        self._alphas = np.clip(alphas, 0, 1)
        self._betas = 1 - self._alphas
    
    def beta(self, t: int) -> float:
        return self._betas[t]
    
    def alpha(self, t: int) -> float:
        return self._alphas[t]
    
    def alpha_bar(self, t: int) -> float:
        return self._alpha_bars[t]


class LearnedSchedule:
    """
    可学习的噪声调度
    
    参数用神经网络学习
    """
    
    def __init__(self, T: int = 1000):
        self.T = T
        
        # 可学习的参数
        self.log_betas = np.random.randn(T) * 0.01
    
    def beta(self, t: int) -> float:
        return np.exp(self.log_betas[t])
    
    def set_beta(self, t: int, value: float):
        """设置beta值"""
        self.log_betas[t] = np.log(value + 1e-8)
    
    def clip_betas(self, min_val: float = 1e-4, max_val: float = 0.99):
        """裁剪beta值"""
        self.log_betas = np.clip(self.log_betas, np.log(min_val), np.log(max_val))
    
    def compute_alphas(self):
        """计算alpha和alpha_bar"""
        betas = np.exp(self.log_betas)
        alphas = 1 - betas
        alpha_bars = np.cumprod(alphas)
        
        return alphas, alpha_bars


class ScheduleComparison:
    """
    调度对比工具
    """
    
    @staticmethod
    def compare_schedules(T: int = 1000) -> dict:
        """
        对比不同调度的特性
        
        返回:
            各调度的 alpha_bar 衰减曲线信息
        """
        schedules = {
            'linear': LinearSchedule(T),
            'cosine': CosineSchedule(T),
            'sqrt': SqrtSchedule(T),
            'polynomial_2': PolynomialSchedule(T, p=2),
            'polynomial_4': PolynomialSchedule(T, p=4),
        }
        
        results = {}
        
        for name, schedule in schedules.items():
            alpha_bars = schedule.get_all_alpha_bars()
            
            # 关键时间点
            t_50 = np.argmax(alpha_bars < 0.5)  # alpha_bar = 0.5 的时间
            t_10 = np.argmax(alpha_bars < 0.1)  # alpha_bar = 0.1 的时间
            
            results[name] = {
                'alpha_bar_0': alpha_bars[0],
                'alpha_bar_T': alpha_bars[-1],
                't_50': t_50 if t_50 > 0 else T,
                't_10': t_10 if t_10 > 0 else T,
                'decay_rate': 'constant' if name == 'linear' else 'adaptive'
            }
        
        return results


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("噪声调度测试")
    print("=" * 60)
    
    T = 100
    
    # 测试1：线性调度
    print("\n1. 线性调度:")
    
    linear = LinearSchedule(T=T, beta_start=1e-4, beta_end=0.02)
    
    for t in [0, T//4, T//2, 3*T//4, T-1]:
        beta = linear.beta(t)
        alpha = linear.alpha(t)
        alpha_bar = linear.alpha_bar(t)
        print(f"   t={t}: beta={beta:.6f}, alpha={alpha:.6f}, alpha_bar={alpha_bar:.6f}")
    
    # 测试2：余弦调度
    print("\n2. 余弦调度:")
    
    cosine = CosineSchedule(T=T, s=0.008)
    
    for t in [0, T//4, T//2, 3*T//4, T-1]:
        alpha_bar = cosine.alpha_bar(t)
        print(f"   t={t}: alpha_bar={alpha_bar:.6f}")
    
    # 测试3：平方根调度
    print("\n3. 平方根调度:")
    
    sqrt_sched = SqrtSchedule(T=T)
    
    for t in [0, T//4, T//2, 3*T//4, T-1]:
        alpha_bar = sqrt_sched.alpha_bar(t)
        print(f"   t={t}: alpha_bar={alpha_bar:.6f}")
    
    # 测试4：指数调度
    print("\n4. 指数调度:")
    
    exp_sched = ExponentialSchedule(T=T, gamma=0.005)
    
    for t in [0, T//4, T//2, 3*T//4, T-1]:
        alpha_bar = exp_sched.alpha_bar(t)
        print(f"   t={t}: alpha_bar={alpha_bar:.6f}")
    
    # 测试5：多项式调度
    print("\n5. 多项式调度:")
    
    for p in [1, 2, 4]:
        poly = PolynomialSchedule(T=T, p=float(p))
        print(f"   p={p}: alpha_bar[T/2]={poly.alpha_bar(T//2):.6f}")
    
    # 测试6：调度对比
    print("\n6. 调度对比:")
    
    comparison = ScheduleComparison.compare_schedules(T=1000)
    
    print("   调度\t\talpha_bar[0]\talpha_bar[T]\tt_50\tt_10")
    for name, info in comparison.items():
        print(f"   {name}\t\t{info['alpha_bar_0']:.4f}\t\t{info['alpha_bar_T']:.6f}"
              f"\t\t{info['t_50']}\t{info['t_10']}")
    
    # 测试7：alpha_bar衰减曲线
    print("\n7. alpha_bar衰减曲线:")
    
    schedules = [
        ('线性', LinearSchedule(T=100)),
        ('余弦', CosineSchedule(T=100)),
        ('平方根', SqrtSchedule(T=100)),
    ]
    
    for name, sched in schedules:
        bars = sched.get_all_alpha_bars()
        # 找到关键点
        t_50 = np.argmax(bars < 0.5)
        t_10 = np.argmax(bars < 0.1)
        print(f"   {name}: t_50={t_50}, t_10={t_10}, 最终alpha_bar={bars[-1]:.6f}")
    
    # 测试8：可学习调度
    print("\n8. 可学习调度:")
    
    learned = LearnedSchedule(T=10)
    print(f"   初始beta范围: [{np.exp(learned.log_betas.min()):.6f}, "
          f"{np.exp(learned.log_betas.max()):.6f}]")
    
    learned.set_beta(5, 0.1)
    print(f"   设置beta[5]=0.1后: {learned.beta(5):.6f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
