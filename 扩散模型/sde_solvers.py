"""
SDE求解器
SDE (Stochastic Differential Equation) Solvers

扩散模型可以表示为SDE，解SDE的数值方法决定采样质量。
包括Euler-Maruyama、Milstein、随机Runge-Kutta等。
"""

import numpy as np
from typing import Callable, Tuple, Optional
from abc import ABC, abstractmethod


class SDESolver(ABC):
    """
    SDE求解器基类
    
    SDE形式: dx = f(x,t)dt + g(t)dW
    
    参数:
        drift: 漂移函数 f(x,t)
        diffusion: 扩散函数 g(t)
        T: 终端时间
        dt: 时间步长
    """
    
    def __init__(self, drift: Callable, diffusion: Callable, 
                 T: float = 1.0, dt: float = 0.001):
        self.drift = drift
        self.diffusion = diffusion
        self.T = T
        self.dt = dt
        self.n_steps = int(T / dt)
    
    @abstractmethod
    def step(self, x: np.ndarray, t: float, dW: np.ndarray) -> np.ndarray:
        """单步求解"""
        pass
    
    def solve(self, x0: np.ndarray, n_steps: Optional[int] = None,
              return_trajectory: bool = True) -> np.ndarray:
        """
        求解SDE
        
        参数:
            x0: 初始条件
            n_steps: 步数（默认使用self.n_steps）
            return_trajectory: 是否返回完整轨迹
            
        返回:
            轨迹或最终状态
        """
        if n_steps is None:
            n_steps = self.n_steps
        
        dt = self.T / n_steps
        
        if return_trajectory:
            trajectory = [x0.copy()]
            x = x0.copy()
            
            for i in range(n_steps):
                t = i * dt
                dW = np.random.randn(*x.shape) * np.sqrt(dt)
                x = self.step(x, t, dW)
                trajectory.append(x.copy())
            
            return np.array(trajectory)
        else:
            x = x0.copy()
            for i in range(n_steps):
                t = i * dt
                dW = np.random.randn(*x.shape) * np.sqrt(dt)
                x = self.step(x, t, dW)
            return x


class EulerMaruyama(SDESolver):
    """
    Euler-Maruyama方法（一阶强收敛）
    
    x_{n+1} = x_n + f(x_n, t_n) * dt + g(t_n) * dW
    
    参数:
        drift: 漂移函数
        diffusion: 扩散函数
        T: 终端时间
        dt: 时间步长
    """
    
    def step(self, x: np.ndarray, t: float, dW: np.ndarray) -> np.ndarray:
        """
        单步Euler-Maruyama
        
        参数:
            x: 当前状态
            t: 当前时间
            dW: 维纳过程增量
        """
        f = self.drift(x, t)
        g = self.diffusion(t)
        
        return x + f * self.dt + g * dW


class Milstein(SDESolver):
    """
    Milstein方法（一阶强收敛，含伊藤校正）
    
    x_{n+1} = x_n + f*dt + g*dW + 0.5*g*g'*(dW^2 - dt)
    
    参数:
        drift: 漂移函数
        diffusion: 扩散函数
        diffusion_grad: 扩散函数的导数 g'
    """
    
    def __init__(self, drift: Callable, diffusion: Callable,
                 diffusion_grad: Callable = None,
                 T: float = 1.0, dt: float = 0.001):
        super().__init__(drift, diffusion, T, dt)
        self.diffusion_grad = diffusion_grad or (lambda t: 0.0)
    
    def step(self, x: np.ndarray, t: float, dW: np.ndarray) -> np.ndarray:
        """单步Milstein"""
        f = self.drift(x, t)
        g = self.diffusion(t)
        g_prime = self.diffusion_grad(t)
        
        # 伊藤校正项
        correction = 0.5 * g * g_prime * (dW**2 - self.dt)
        
        return x + f * self.dt + g * dW + correction


class StochasticRungeKutta(SDESolver):
    """
    随机Runge-Kutta方法（SRK）
    
    更稳定的数值方法
    
    参数:
        drift: 漂移函数
        diffusion: 扩散函数
        T: 终端时间
        dt: 时间步长
    """
    
    def step(self, x: np.ndarray, t: float, dW: np.ndarray) -> np.ndarray:
        """单步SRK"""
        dt = self.dt
        sqrt_dt = np.sqrt(dt)
        
        # _stage 1
        K1 = self.drift(x, t) * dt + self.diffusion(t) * dW
        
        # _stage 2
        x2 = x + 0.5 * K1
        K2 = self.drift(x2, t + 0.5 * dt) * dt + self.diffusion(t + 0.5 * dt) * dW
        
        return x + K2


class ReverseEM(SDESolver):
    """
    逆向Euler-Maruyama（用于SDE的逆向采样）
    
    x_{n} = x_{n+1} - f(x_{n+1}, t_{n+1}) * dt + g(t_{n+1}) * dW
    
    参数:
        drift: 漂移函数
        diffusion: 扩散函数
        score_fn: score函数（用于逆向SDE）
    """
    
    def __init__(self, drift: Callable, diffusion: Callable,
                 score_fn: Callable, T: float = 1.0, dt: float = 0.001):
        super().__init__(drift, diffusion, T, dt)
        self.score_fn = score_fn
    
    def reverse_step(self, x: np.ndarray, t: float, dt: float) -> np.ndarray:
        """
        逆向单步
        
        参数:
            x: 当前状态（逆向时间）
            t: 逆向时间
        """
        # 漂移修正
        f = self.drift(x, t)
        g = self.diffusion(t)
        
        # score修正
        score = self.score_fn(x, t)
        
        # 修正后的漂移
        f_rev = f - g * score
        
        # 逆向更新
        dW = np.random.randn(*x.shape) * np.sqrt(dt)
        
        return x + f_rev * dt + g * dW
    
    def solve(self, x0: np.ndarray, n_steps: Optional[int] = None,
              return_trajectory: bool = True) -> np.ndarray:
        """逆向求解"""
        if n_steps is None:
            n_steps = self.n_steps
        
        dt = self.T / n_steps
        
        if return_trajectory:
            trajectory = [x0.copy()]
            x = x0.copy()
            
            for i in range(n_steps):
                t = self.T - i * dt  # 逆向时间
                x = self.reverse_step(x, t, dt)
                trajectory.append(x.copy())
            
            return np.array(trajectory[::-1])  # 反转得到正向时间顺序
        else:
            x = x0.copy()
            for i in range(n_steps):
                t = self.T - i * dt
                x = self.reverse_step(x, t, dt)
            return x


class PredictorCorrector:
    """
    预测-校正方法
    
    结合ODE求解器和蒙特卡洛校正
    
    参数:
        predictor: 预测器（如Euler）
        corrector: 校正器（如Langevin）
        n_corrector_steps: 校正步数
    """
    
    def __init__(self, predictor: SDESolver, corrector: Callable,
                 n_corrector_steps: int = 1):
        self.predictor = predictor
        self.corrector = corrector
        self.n_corrector_steps = n_corrector_steps
    
    def solve(self, x0: np.ndarray, score_fn: Callable = None) -> np.ndarray:
        """
        预测-校正求解
        
        参数:
            x0: 初始条件
            score_fn: score函数（用于校正）
        """
        # 预测步骤
        x = self.predictor.solve(x0, return_trajectory=False)
        
        # 校正步骤
        if score_fn is not None:
            for _ in range(self.n_corrector_steps):
                score = score_fn(x)
                x = x + self.corrector(x, score)
        
        return x


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SDE求解器测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # Ornstein-Uhlenbeck过程
    # dx = -theta * x * dt + sigma * dW
    theta = 1.0
    sigma = 0.5
    
    def ou_drift(x, t):
        return -theta * x
    
    def ou_diffusion(t):
        return sigma
    
    # 测试1：Euler-Maruyama
    print("\n1. Euler-Maruyama求解:")
    
    em = EulerMaruyama(ou_drift, ou_diffusion, T=1.0, dt=0.01)
    
    x0 = np.array([1.0])
    trajectory = em.solve(x0, n_steps=100, return_trajectory=True)
    
    print(f"   轨迹形状: {trajectory.shape}")
    print(f"   最终状态: {trajectory[-1][0]:.4f}")
    print(f"   理论均值(渐进): 0.0")
    
    # 测试2：Milstein方法
    print("\n2. Milstein方法:")
    
    # OU过程的g' = 0
    milstein = Milstein(ou_drift, ou_diffusion, lambda t: 0.0, T=1.0, dt=0.01)
    
    trajectory_m = milstein.solve(x0, n_steps=100, return_trajectory=True)
    
    print(f"   最终状态: {trajectory_m[-1][0]:.4f}")
    
    # 测试3：随机Runge-Kutta
    print("\n3. 随机Runge-Kutta:")
    
    srk = StochasticRungeKutta(ou_drift, ou_diffusion, T=1.0, dt=0.01)
    
    trajectory_srk = srk.solve(x0, n_steps=100, return_trajectory=True)
    
    print(f"   最终状态: {trajectory_srk[-1][0]:.4f}")
    
    # 测试4：收敛性比较
    print("\n4. 收敛性比较（不同步长）:")
    
    final_states = {}
    
    for method_name, solver in [
        ('Euler-Maruyama', EulerMaruyama(ou_drift, ou_diffusion, T=1.0, dt=0.01)),
        ('Milstein', Milstein(ou_drift, ou_diffusion, lambda t: 0.0, T=1.0, dt=0.01)),
        ('SRK', StochasticRungeKutta(ou_drift, ou_diffusion, T=1.0, dt=0.01)),
    ]:
        states = []
        for _ in range(10):
            x_final = solver.solve(x0, n_steps=100, return_trajectory=False)
            states.append(x_final[0])
        final_states[method_name] = np.mean(states)
        print(f"   {method_name}: 均值={np.mean(states):.4f}, 方差={np.var(states):.4f}")
    
    # 测试5：逆向SDE（用于扩散模型采样）
    print("\n5. 逆向SDE采样:")
    
    def mock_score(x, t):
        # 简化的score
        return -x * 0.1
    
    # 模拟扩散模型采样
    reverse_em = ReverseEM(
        drift=lambda x, t: 0.0,
        diffusion=lambda t: np.sqrt(2 * (1 - t)),  # 简化的扩散
        score_fn=mock_score,
        T=1.0,
        dt=0.01
    )
    
    x0 = np.array([0.0])  # 从纯噪声开始
    samples = reverse_em.solve(x0, n_steps=100, return_trajectory=False)
    
    print(f"   起始状态: 0.0")
    print(f"   最终状态: {samples[0]:.4f}")
    
    # 测试6：预测-校正方法
    print("\n6. 预测-校正方法:")
    
    predictor = EulerMaruyama(ou_drift, ou_diffusion, T=1.0, dt=0.01)
    corrector = lambda x, score: score * 0.01  # 简化的Langevin校正
    
    pc = PredictorCorrector(predictor, corrector, n_corrector_steps=5)
    
    result = pc.solve(x0, score_fn=mock_score)
    print(f"   预测-校正结果: {result[0]:.4f}")
    
    # 测试7：统计量验证
    print("\n7. OU过程统计量验证:")
    
    n_trajectories = 100
    final_values = []
    
    solver = EulerMaruyama(ou_drift, ou_diffusion, T=1.0, dt=0.01)
    
    for _ in range(n_trajectories):
        final = solver.solve(x0, n_steps=100, return_trajectory=False)
        final_values.append(final[0])
    
    print(f"   模拟均值: {np.mean(final_values):.4f}")
    print(f"   模拟方差: {np.var(final_values):.4f}")
    
    # OU过程的解析方差: sigma^2 / (2*theta) * (1 - exp(-2*theta*T))
    analytical_var = sigma**2 / (2 * theta) * (1 - np.exp(-2 * theta * 1.0))
    print(f"   解析方差: {analytical_var:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
