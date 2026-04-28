"""
SDE框架：VP/VE SDE
SDE Framework: Variance Preserving and Variance Exploding SDE

随机微分方程框架统一了DDPM和Score-Based模型。
两种主要形式：
1. VP-SDE (Variance Preserving): 保持方差接近常数
2. VE-SDE (Variance Exploding): 方差随时间爆炸式增长
"""

import numpy as np
from typing import Callable, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class SDESchedule:
    """
    SDE调度配置
    
    属性:
        T: 终端时间
        dt: 时间步长
        schedule_type: 'linear', 'cosine', 'exponential'
    """
    T: float = 1.0
    dt: float = 0.001
    schedule_type: str = 'linear'
    
    def __post_init__(self):
        self.time_points = np.arange(0, self.T + self.dt, self.dt)
        self.N = len(self.time_points)


class SDE(ABC):
    """
    随机微分方程基类
    
    形式：dx = f(x, t)dt + g(t)dW
    
    其中：
    - f(x, t): 漂移项（drift）
    - g(t): 扩散项（diffusion）
    - dW: 维纳过程增量
    """
    
    def __init__(self, T: float = 1.0):
        self.T = T
    
    @abstractmethod
    def drift(self, x: np.ndarray, t: float) -> np.ndarray:
        """漂移项 f(x, t)"""
        pass
    
    @abstractmethod
    def diffusion(self, x: np.ndarray, t: float) -> np.ndarray:
        """扩散项 g(t)"""
        pass
    
    @abstractmethod
    def marginal_prob(self, x0: np.ndarray, t: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        边缘分布的均值和标准差
        
        返回:
            (mu_t, sigma_t)
        """
        pass
    
    @abstractmethod
    def reverse_drift(self, x: np.ndarray, t: float, 
                     score_fn: Callable) -> np.ndarray:
        """
        逆向SDE的漂移项
        
        返回:
            f_rev(x, t)
        """
        pass
    
    def euler_maruyama(self, x0: np.ndarray, n_steps: int = 100,
                       score_fn: Optional[Callable] = None,
                       reverse: bool = False) -> np.ndarray:
        """
        Euler-Maruyama数值求解
        
        参数:
            x0: 初始状态
            n_steps: 步数
            score_fn: Score函数（用于逆向采样）
            reverse: 是否逆向求解
            
        返回:
            轨迹
        """
        dt = self.T / n_steps
        x = x0.copy()
        trajectory = [x]
        
        for i in range(n_steps):
            t = self.T - i * dt if reverse else i * dt
            
            # 漂移
            f = self.drift(x, t)
            
            # 扩散
            g = self.diffusion(x, t)
            
            # 如果是逆向SDE
            if reverse and score_fn is not None:
                f = self.reverse_drift(x, t, score_fn)
            
            # 随机项
            dW = np.random.randn(*x.shape) * np.sqrt(dt)
            
            # 更新
            x = x + f * dt + g * dW
            
            trajectory.append(x)
        
        return np.array(trajectory)


class VPSDE(SDE):
    """
    方差保持SDE (Variance Preserving SDE)
    
    来自Score SDE论文:
    dx = -0.5 * beta(t) * x * dt + sqrt(beta(t)) * dW
    
    特点：x_t的方差始终接近1
    
    参数:
        beta_min: beta最小值
        beta_max: beta最大值
    """
    
    def __init__(self, T: float = 1.0, beta_min: float = 0.1, beta_max: float = 20.0):
        super().__init__(T)
        self.beta_min = beta_min
        self.beta_max = beta_max
        
        # beta(t)调度
        self._compute_beta_schedule()
    
    def _compute_beta_schedule(self):
        """计算beta(t)调度"""
        # 线性调度
        self.beta_t = lambda t: self.beta_min + (self.beta_max - self.beta_min) * t
    
    def beta(self, t: float) -> float:
        """获取beta(t)"""
        if callable(self.beta_t):
            return self.beta_t(t)
        return self.beta_t
    
    def drift(self, x: np.ndarray, t: float) -> np.ndarray:
        """漂移项：-0.5 * beta(t) * x"""
        beta = self.beta(t)
        return -0.5 * beta * x
    
    def diffusion(self, x: np.ndarray, t: float) -> np.ndarray:
        """扩散项：sqrt(beta(t))"""
        beta = self.beta(t)
        return np.sqrt(beta)
    
    def marginal_prob(self, x0: np.ndarray, t: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        边缘分布均值和标准差
        
        x(t) | x(0) ~ N(mu_t, sigma_t^2)
        
        mu_t = x0 * exp(-0.5 * integral(beta(s)ds))
        sigma_t^2 = 1 - exp(-integral(beta(s)ds))
        """
        # 积分 beta(s) from 0 to t
        beta_avg = 0.5 * (self.beta_min + self.beta_max)
        integral_beta = beta_avg * t
        
        # 使用线性近似的解析解
        exp_factor = np.exp(-0.5 * integral_beta)
        
        mu_t = x0 * exp_factor
        sigma_t = np.sqrt(1 - exp_factor**2 + 1e-6)
        
        return mu_t, sigma_t
    
    def reverse_drift(self, x: np.ndarray, t: float, 
                     score_fn: Callable) -> np.ndarray:
        """
        逆向SDE漂移项
        
        f_rev = 0.5 * beta(t) * x + beta(t) * s_theta(x, t)
        """
        beta = self.beta(t)
        score = score_fn(x, t)
        
        return 0.5 * beta * x + beta * score
    
    def reverse_diffusion(self, x: np.ndarray, t: float) -> np.ndarray:
        """逆向扩散项"""
        beta = self.beta(t)
        return np.sqrt(beta)


class VESDE(SDE):
    """
    方差爆炸SDE (Variance Exploding SDE)
    
    dx = sqrt(d sigma^2/dt) * dW
    
    特点：方差随时间增长到无穷
    
    参数:
        sigma_min: 最小sigma
        sigma_max: 最大sigma
    """
    
    def __init__(self, T: float = 1.0, sigma_min: float = 0.01, sigma_max: float = 50.0):
        super().__init__(T)
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        
        self._compute_sigma_schedule()
    
    def _compute_sigma_schedule(self):
        """计算sigma(t)调度"""
        # 指数调度
        log_sigma_min = np.log(self.sigma_min)
        log_sigma_max = np.log(self.sigma_max)
        
        self.log_sigma_t = lambda t: log_sigma_min + (log_sigma_max - log_sigma_min) * t**2
    
    def sigma(self, t: float) -> float:
        """获取sigma(t)"""
        if callable(self.log_sigma_t):
            return np.exp(self.log_sigma_t(t))
        return self.sigma_min
    
    def drift(self, x: np.ndarray, t: float) -> np.ndarray:
        """漂移项：0"""
        return np.zeros_like(x)
    
    def diffusion(self, x: np.ndarray, t: float) -> np.ndarray:
        """扩散项：sigma'(t)"""
        # d(sigma^2)/dt
        log_sigma_min = np.log(self.sigma_min)
        log_sigma_max = np.log(self.sigma_max)
        d_sigma_sq_dt = 2 * (log_sigma_max - log_sigma_min) * t * self.sigma(t)**2
        
        return np.sqrt(d_sigma_sq_dt + 1e-6)
    
    def marginal_prob(self, x0: np.ndarray, t: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        边缘分布
        
        x(t) | x(0) ~ N(x0, sigma(t)^2 - sigma_min^2)
        """
        sigma_t = self.sigma(t)
        
        mu_t = x0
        sigma_t_out = np.sqrt(sigma_t**2 - self.sigma_min**2 + 1e-6)
        
        return mu_t, sigma_t_out
    
    def reverse_drift(self, x: np.ndarray, t: float, 
                     score_fn: Callable) -> np.ndarray:
        """
        逆向SDE漂移项
        
        f_rev = sigma'(t) * s_theta(x, t)
        """
        sigma_t = self.sigma(t)
        
        # d sigma / dt
        d_sigma_dt = 2 * (np.log(self.sigma_max) - np.log(self.sigma_min)) * t * sigma_t
        
        score = score_fn(x, t)
        
        return d_sigma_dt * score
    
    def reverse_diffusion(self, x: np.ndarray, t: float) -> np.ndarray:
        """逆向扩散项"""
        return self.diffusion(x, t)


class SubVPSDE(SDE):
    """
    Sub-VP SDE (介于VP和VE之间)
    
    dx = -0.5 * beta(t) * x * dt + sqrt(beta(t) * (1 - exp(-2 integral beta))) * dW
    """
    
    def __init__(self, T: float = 1.0, beta_min: float = 0.1, beta_max: float = 20.0):
        super().__init__(T)
        self.beta_min = beta_min
        self.beta_max = beta_max
    
    def beta(self, t: float) -> float:
        return self.beta_min + (self.beta_max - self.beta_min) * t
    
    def drift(self, x: np.ndarray, t: float) -> np.ndarray:
        beta = self.beta(t)
        return -0.5 * beta * x
    
    def diffusion(self, x: np.ndarray, t: float) -> np.ndarray:
        beta = self.beta(t)
        integral_beta = 0.5 * (self.beta_min + self.beta_max) * t**2
        return np.sqrt(beta * (1 - np.exp(-2 * integral_beta)) + 1e-6)


class SDESampler:
    """
    SDE采样器
    
    参数:
        sde: SDE实例
    """
    
    def __init__(self, sde: SDE):
        self.sde = sde
    
    def pc_sampler(self, score_fn: Callable, x0_shape: Tuple,
                   n_steps: int = 100, predictor: str = 'euler',
                   corrector: str = 'langevin', 
                   corrector_steps: int = 1) -> np.ndarray:
        """
        预测-校正采样
        
        预测器：Euler-Maruyama, Reverse Euler, etc.
        校正器：Langevin, MALA
        
        参数:
            score_fn: Score函数
            x0_shape: 初始形状
            n_steps: 预测器步数
            predictor: 预测器类型
            corrector: 校正器类型
            
        返回:
            采样结果
        """
        dt = self.sde.T / n_steps
        
        # 从先验采样
        x = np.random.randn(*x0_shape)
        
        for i in range(n_steps):
            t = self.sde.T - i * dt
            
            # 预测步骤
            x = self._predictor_step(x, t, dt, score_fn, predictor)
            
            # 校正步骤
            for _ in range(corrector_steps):
                x = self._corrector_step(x, t, score_fn, corrector)
        
        return x
    
    def _predictor_step(self, x: np.ndarray, t: float, dt: float,
                        score_fn: Callable, method: str) -> np.ndarray:
        """预测步骤"""
        if method == 'euler':
            f = self.sde.reverse_drift(x, t, score_fn)
            g = self.sde.reverse_diffusion(x, t)
            
            dW = np.random.randn(*x.shape) * np.sqrt(dt)
            x = x + f * dt + g * dW
        
        return x
    
    def _corrector_step(self, x: np.ndarray, t: float,
                       score_fn: Callable, method: str) -> np.ndarray:
        """校正步骤"""
        if method == 'langevin':
            score = score_fn(x, t)
            
            # Langevin校正
            gamma = 0.01  # 步长
            
            dW = np.random.randn(*x.shape)
            x = x + gamma * score + np.sqrt(2 * gamma) * dW
        
        return x


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SDE框架测试 (VP/VE SDE)")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：VP-SDE边缘分布
    print("\n1. VP-SDE边缘分布:")
    
    vp_sde = VPSDE(T=1.0, beta_min=0.1, beta_max=20.0)
    
    x0 = np.array([1.0, 2.0])
    
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        mu, sigma = vp_sde.marginal_prob(x0, t)
        print(f"   t={t:.2f}: mu={mu}, sigma={sigma:.4f}")
    
    # 测试2：VE-SDE边缘分布
    print("\n2. VE-SDE边缘分布:")
    
    ve_sde = VESDE(T=1.0, sigma_min=0.01, sigma_max=50.0)
    
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        mu, sigma = ve_sde.marginal_prob(x0, t)
        print(f"   t={t:.2f}: mu={mu}, sigma={sigma:.4f}")
    
    # 测试3：漂移和扩散项
    print("\n3. VP-SDE漂移和扩散项:")
    
    x = np.array([1.0, 2.0])
    
    for t in [0.0, 0.5, 1.0]:
        beta = vp_sde.beta(t)
        drift = vp_sde.drift(x, t)
        diff = vp_sde.diffusion(x, t)
        print(f"   t={t:.2f}: beta={beta:.2f}, drift={drift}, diffusion={diff:.4f}")
    
    # 测试4：逆向SDE
    print("\n4. VP-SDE逆向漂移:")
    
    def mock_score(x, t):
        return -x * 0.5
    
    x = np.array([0.5, 1.0])
    t = 0.5
    
    reverse_drift = vp_sde.reverse_drift(x, t, mock_score)
    print(f"   t={t}: 逆向漂移={reverse_drift}")
    
    # 测试5：Euler-Maruyama求解
    print("\n5. VP-SDE Euler-Maruyama轨迹:")
    
    x0 = np.array([1.0])
    n_steps = 10
    
    trajectory = vp_sde.euler_maruyama(x0, n_steps=n_steps, reverse=False)
    print(f"   轨迹形状: {trajectory.shape}")
    print(f"   起始点: {trajectory[0]}")
    print(f"   终点: {trajectory[-1]}")
    
    # 测试6：SDE采样器
    print("\n6. SDE采样器:")
    
    class MockScoreFn:
        def __call__(self, x, t):
            return -x * 0.1
    
    sampler = SDESampler(vp_sde)
    
    shape = (4, 2)
    result = sampler.pc_sampler(MockScoreFn(), shape, n_steps=5)
    print(f"   采样结果形状: {result.shape}")
    
    # 测试7：Sub-VP SDE
    print("\n7. Sub-VP SDE:")
    
    subvp = SubVPSDE(T=1.0, beta_min=0.1, beta_max=20.0)
    
    for t in [0.0, 0.5, 1.0]:
        drift = subvp.drift(x, t)
        diff = subvp.diffusion(x, t)
        print(f"   t={t:.2f}: drift={drift}, diffusion={diff:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
