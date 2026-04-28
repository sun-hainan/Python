"""
偏微分方程(PDE)有限差分法
===========================
本模块用有限差分法求解两类经典PDE：
1. 热传导方程（抛物型）：∂u/∂t = α ∇²u
2. 波动方程（双曲型）：∂²u/∂t² = c² ∇²u

包含显式和隐式（Crank-Nicolson）格式。

Author: 算法库
"""

import numpy as np
from typing import Callable, Tuple


def heat_equation_explicit(
    u0: np.ndarray,
    dx: float,
    dt: float,
    alpha: float,
    n_steps: int
) -> np.ndarray:
    """
    热传导方程显式差分格式
    
    方程: ∂u/∂t = α ∂²u/∂x²
    显式格式: u_i^{n+1} = u_i^n + r*(u_{i+1}^n - 2*u_i^n + u_{i-1}^n)
    其中 r = α*dt/dx^2
    
    稳定性条件: r <= 0.5
    
    参数:
        u0: 初始条件 (n,)
        dx: 空间步长
        dt: 时间步长
        alpha: 热扩散系数
        n_steps: 时间步数
    
    返回:
        u: 最终时刻的解
    """
    n = len(u0)
    u = u0.copy()
    r = alpha * dt / (dx ** 2)
    
    if r > 0.5:
        print(f"警告: r={r:.3f} > 0.5, 显式格式可能不稳定")
    
    for _ in range(n_steps):
        u_new = u.copy()
        # 内部点
        u_new[1:-1] = u[1:-1] + r * (u[2:] - 2 * u[1:-1] + u[:-2])
        u = u_new
    
    return u


def heat_equation_implicit(
    u0: np.ndarray,
    dx: float,
    dt: float,
    alpha: float,
    n_steps: int,
    bc_left: float = 0.0,
    bc_right: float = 0.0
) -> np.ndarray:
    """
    热传导方程隐式差分格式（向后Euler）
    
    方程: ∂u/∂t = α ∂²u/∂x²
    隐式格式: -r*u_{i-1}^{n+1} + (1+2r)*u_i^{n+1} - r*u_{i+1}^{n+1} = u_i^n
    
    优点: 无条件稳定
    缺点: 每步需解线性系统
    
    参数:
        u0: 初始条件
        dx, dt: 空间和时间步长
        alpha: 扩散系数
        n_steps: 时间步数
        bc_left, bc_right: 边界条件
    
    返回:
        u: 最终时刻的解
    """
    n = len(u0)
    u = u0.copy()
    r = alpha * dt / (dx ** 2)
    
    # 构建三对角矩阵 A
    diag = np.ones(n) * (1 + 2 * r)
    off_diag = np.ones(n - 1) * (-r)
    
    # 应用边界条件
    diag[0] = 1.0
    off_diag[0] = 0.0
    diag[-1] = 1.0
    
    # 使用Thomas算法求解三对角系统
    for _ in range(n_steps):
        # 右端向量
        b = u.copy()
        b[0] = bc_left
        b[-1] = bc_right
        
        # Thomas算法
        c_prime = np.zeros(n - 1)
        d_prime = np.zeros(n)
        
        # 前向消元
        c_prime[0] = off_diag[0] / diag[0]
        d_prime[0] = b[0] / diag[0]
        
        for i in range(1, n):
            if i < n - 1:
                denom = diag[i] - off_diag[i - 1] * c_prime[i - 1]
                c_prime[i] = off_diag[i] / denom if i < n - 1 else 0
            else:
                denom = diag[i] - off_diag[i - 1] * c_prime[i - 1]
            d_prime[i] = (b[i] - off_diag[i - 1] * d_prime[i - 1]) / denom
        
        # 后向回代
        u[-1] = d_prime[-1]
        for i in range(n - 2, -1, -1):
            u[i] = d_prime[i] - c_prime[i] * u[i + 1]
    
    return u


def heat_equation_crank_nicolson(
    u0: np.ndarray,
    dx: float,
    dt: float,
    alpha: float,
    n_steps: int,
    bc_left: Callable[[float], float] = None,
    bc_right: Callable[[float], float] = None
) -> np.ndarray:
    """
    Crank-Nicolson格式（隐式）
    
    半隐式格式：时间和空间的平均
    (u_i^{n+1} - u_i^n)/dt = (α/2dx²) * [(u_{i+1}^{n+1} - 2u_i^{n+1} + u_{i-1}^{n+1})
                                       + (u_{i+1}^n - 2u_i^n + u_{i-1}^n)]
    
    精度: O(dt², dx²)，无条件稳定
    
    参数:
        u0: 初始条件
        dx, dt: 步长
        alpha: 扩散系数
        n_steps: 时间步数
        bc_left, bc_right: 边界条件函数
    
    返回:
        u: 解数组 (n_steps+1, n)
    """
    n = len(u0)
    u = np.zeros((n_steps + 1, n))
    u[0] = u0.copy()
    
    r = alpha * dt / (2 * dx ** 2)  # CN格式系数
    
    # 构建矩阵 A (左端) 和 B (右端)
    diag_A = np.ones(n) * (1 + 2 * r)
    off_diag_A = np.ones(n - 1) * (-r)
    
    diag_B = np.ones(n) * (1 - 2 * r)
    off_diag_B = np.ones(n - 1) * r
    
    # Thomas算法参数
    def thomas_solve(diag, off_diag, b):
        n = len(b)
        c_prime = np.zeros(n - 1)
        d_prime = np.zeros(n)
        
        c_prime[0] = off_diag[0] / diag[0]
        d_prime[0] = b[0] / diag[0]
        
        for i in range(1, n):
            denom = diag[i] - off_diag[i - 1] * c_prime[i - 1]
            if i < n - 1:
                c_prime[i] = off_diag[i] / denom
            d_prime[i] = (b[i] - off_diag[i - 1] * d_prime[i - 1]) / denom
        
        x = np.zeros(n)
        x[-1] = d_prime[-1]
        for i in range(n - 2, -1, -1):
            x[i] = d_prime[i] - c_prime[i] * x[i + 1]
        
        return x
    
    for step in range(n_steps):
        # 计算右端向量 B @ u^n
        b = np.zeros(n)
        b[1:-1] = (1 - 2 * r) * u[step, 1:-1] + r * u[step, 2:] + r * u[step, :-2]
        b[0] = 0.0
        b[-1] = 0.0
        
        if bc_left:
            b[0] = r * bc_left(step * dt)
            b[1] += r * bc_left(step * dt)
        if bc_right:
            b[-1] = r * bc_right(step * dt)
            b[-2] += r * bc_right(step * dt)
        
        # 求解
        u[step + 1] = thomas_solve(diag_A, off_diag_A, b)
    
    return u


def wave_equation_explicit(
    u0: np.ndarray,
    v0: np.ndarray,
    dx: float,
    dt: float,
    c: float,
    n_steps: int
) -> np.ndarray:
    """
    波动方程显式差分格式
    
    方程: ∂²u/∂t² = c² ∂²u/∂x²
    显式格式: u_i^{n+1} = 2*u_i^n - u_i^{n-1} + r²*(u_{i+1}^n - 2*u_i^n + u_{i-1}^n)
    其中 r = c*dt/dx
    
    稳定性条件: r <= 1 (CFL条件)
    
    参数:
        u0: 初始位移
        v0: 初始速度
        dx, dt: 步长
        c: 波速
        n_steps: 时间步数
    
    返回:
        u: 解数组
    """
    n = len(u0)
    u = np.zeros((n_steps + 1, n))
    u[0] = u0.copy()
    
    r = c * dt / dx
    
    if r > 1:
        print(f"警告: r={r:.3f} > 1, 格式不稳定!")
    
    # 第二步：使用Taylor展开
    u[1, 1:-1] = u[0, 1:-1] + dt * v0[1:-1] + (r ** 2 / 2) * (u[0, 2:] - 2 * u[0, 1:-1] + u[0, :-2])
    
    # 时间迭代
    for step in range(1, n_steps):
        u[step + 1, 1:-1] = 2 * u[step, 1:-1] - u[step - 1, 1:-1] + \
                            r ** 2 * (u[step, 2:] - 2 * u[step, 1:-1] + u[step, :-2])
    
    return u


if __name__ == "__main__":
    print("=" * 55)
    print("PDE有限差分法测试")
    print("=" * 55)
    
    # ========== 热传导方程测试 ==========
    print("\n--- 热传导方程: ∂u/∂t = 0.01 ∂²u/∂x² ---")
    
    nx = 50  # 空间点数
    L = 1.0  # 区间长度
    dx = L / (nx - 1)
    x = np.linspace(0, L, nx)
    
    # 初始条件：高斯分布
    u0_heat = np.exp(-100 * (x - 0.5) ** 2)
    
    # 参数
    alpha = 0.01
    dt_explicit = 0.0002  # 满足稳定性 r < 0.5
    dt_implicit = 0.01    # 隐式格式不受限制
    
    # 显式格式
    u_exp = heat_equation_explicit(u0_heat.copy(), dx, dt_explicit, alpha, 500)
    
    # 隐式格式
    u_imp = heat_equation_implicit(u0_heat.copy(), dx, dt_implicit, alpha, 10)
    
    print(f"显式解范围: [{u_exp.min():.4f}, {u_exp.max():.4f}]")
    print(f"隐式解范围: [{u_imp.min():.4f}, {u_imp.max():.4f}]")
    
    # ========== 波动方程测试 ==========
    print("\n--- 波动方程: ∂²u/∂t² = c² ∂²u/∂x², c=1 ---")
    
    nx = 100
    L = 1.0
    dx = L / (nx - 1)
    x = np.linspace(0, L, nx)
    
    # 初始条件：正弦波
    k = np.pi / L
    u0_wave = np.sin(k * x)
    v0_wave = np.zeros(nx)  # 初始静止
    
    c = 1.0
    dt = 0.005
    r = c * dt / dx
    print(f"CFL数 r = {r:.4f}")
    
    # 计算若干时刻
    u_wave = wave_equation_explicit(u0_wave.copy(), v0_wave.copy(), dx, dt, c, 100)
    
    print(f"初始时刻解范围: [{u_wave[0].min():.4f}, {u_wave[0].max():.4f}]")
    print(f"第50步解范围: [{u_wave[50].min():.4f}, {u_wave[50].max():.4f}]")
    print(f"第100步解范围: [{u_wave[100].min():.4f}, {u_wave[100].max():.4f}]")
    
    print("\n测试通过！PDE有限差分法工作正常。")
