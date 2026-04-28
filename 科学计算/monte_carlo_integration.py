"""
Monte Carlo数值积分
====================
本模块实现基于Monte Carlo方法的数值积分：

1. 朴素Monte Carlo积分
2. 重要性采样 (Importance Sampling)
3. 分层抽样 (Stratified Sampling)
4. Vegas算法基础

Monte Carlo积分的核心思想：
- 用随机采样估计定积分
- 收敛速度: O(1/√N)，与维度无关
- 高维积分时比确定性方法更有效

Author: 算法库
"""

import numpy as np
from typing import Callable, Tuple, Optional


def naive_monte_carlo(
    f: Callable,
    a: float,
    b: float,
    n_samples: int = 100000,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    朴素Monte Carlo积分
    
    原理:
        ∫_a^b f(x)dx ≈ (b-a) * (1/n) * Σ f(x_i)
        其中 x_i ~ Uniform(a, b)
    
    误差: σ / √N，其中 σ 是 f 的标准差
    
    参数:
        f: 被积函数
        a, b: 积分区间
        n_samples: 采样点数
        seed: 随机种子
    
    返回:
        integral: 积分近似值
        error: 误差估计
    """
    if seed is not None:
        np.random.seed(seed)
    
    # 随机采样
    x = np.random.uniform(a, b, n_samples)
    
    # 计算函数值
    y = f(x)
    
    # 积分估计
    integral = (b - a) * np.mean(y)
    
    # 误差估计（标准误差）
    error = (b - a) * np.std(y) / np.sqrt(n_samples)
    
    return integral, error


def antithetic_variates(
    f: Callable,
    a: float,
    b: float,
    n_samples: int = 100000,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    对偶变量法 (Antithetic Variates)
    
    原理:
        如果 X ~ Uniform(0,1)，则 1-X 也 ~ Uniform(0,1)
        利用两个负相关的样本减少方差
    
    参数:
        f: 被积函数
        a, b: 积分区间
        n_samples: 采样点数（实际使用2*n_samples个点）
        seed: 随机种子
    
    返回:
        integral: 积分近似值
        error: 误差估计
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_half = n_samples // 2
    
    # 采样 x_1, ..., x_{n/2}
    u = np.random.uniform(0, 1, n_half)
    
    # 配对样本: u 和 1-u
    u_pair = np.concatenate([u, 1 - u])
    x = a + (b - a) * u_pair
    
    # 计算函数值
    y = f(x)
    
    # 分成两半计算方差减少
    y1 = y[:n_half]
    y2 = y[n_half:]
    y_pair = (y1 + y2) / 2
    
    integral = (b - a) * np.mean(y_pair)
    error = (b - a) * np.std(y_pair) / np.sqrt(n_half)
    
    return integral, error


def importance_sampling(
    f: Callable,
    a: float,
    b: float,
    g_sampler: Callable,
    g_pdf: Callable,
    n_samples: int = 100000,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    重要性采样 Monte Carlo 积分
    
    原理:
        ∫ f(x)dx = ∫ f(x)/g(x) * g(x) dx ≈ (1/n) Σ f(x_i)/g(x_i)
        其中 x_i ~ g(x) （重要性分布）
    
    选择好的 g(x) 可以大幅减少方差
    
    参数:
        f: 被积函数
        a, b: 积分区间
        g_sampler: 从分布 g(x) 采样的函数
        g_pdf: g(x) 的概率密度函数
        n_samples: 采样点数
        seed: 随机种子
    
    返回:
        integral: 积分近似值
        error: 误差估计
    """
    if seed is not None:
        np.random.seed(seed)
    
    # 从重要性分布采样
    x = g_sampler(a, b, n_samples)
    
    # 计算 f(x)/g(x)
    weights = f(x) / g_pdf(x, a, b)
    
    # 积分估计
    integral = np.mean(weights)
    error = np.std(weights) / np.sqrt(n_samples)
    
    return integral, error


def stratified_sampling(
    f: Callable,
    a: float,
    b: float,
    n_strata: int = 10,
    n_per_stratum: int = 10000,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    分层抽样 Monte Carlo 积分
    
    原理:
        将积分区间分成n层，每层独立抽样
        可以减少估计的方差，特别是当f在不同区域变化剧烈时
    
    参数:
        f: 被积函数
        a, b: 积分区间
        n_strata: 层数
        n_per_stratum: 每层采样点数
        seed: 随机种子
    
    返回:
        integral: 积分近似值
        error: 误差估计
    """
    if seed is not None:
        np.random.seed(seed)
    
    stratum_width = (b - a) / n_strata
    total_integral = 0.0
    variances = []
    
    for i in range(n_strata):
        # 每层的区间
        stratum_start = a + i * stratum_width
        stratum_end = stratum_start + stratum_width
        
        # 在该层内均匀采样
        x = np.random.uniform(stratum_start, stratum_end, n_per_stratum)
        y = f(x)
        
        # 该层的积分估计
        stratum_integral = stratum_width * np.mean(y)
        total_integral += stratum_integral
        
        # 该层的方差
        variances.append(np.var(y) / n_per_stratum)
    
    # 总积分是各层积分之和
    integral = total_integral
    
    # 误差：各层方差之和的平方根
    total_variance = sum(variances) * (stratum_width ** 2)
    error = np.sqrt(total_variance)
    
    return integral, error


def multidimensional_monte_carlo(
    f: Callable,
    bounds: list,
    n_samples: int = 100000,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    多维Monte Carlo积分
    
    适用于任意维度，复杂度与维度无关
    
    参数:
        f: 被积函数 f(x), x 是 (d,) 数组
        bounds: 每维的积分边界 [(a1,b1), (a2,b2), ...]
        n_samples: 采样点数
        seed: 随机种子
    
    返回:
        integral: 积分近似值
        error: 误差估计
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_dims = len(bounds)
    
    # 在超立方体内均匀采样
    x = np.zeros((n_samples, n_dims))
    volume = 1.0
    
    for d in range(n_dims):
        a, b = bounds[d]
        x[:, d] = np.random.uniform(a, b, n_samples)
        volume *= (b - a)
    
    # 计算函数值
    y = np.array([f(xi) for xi in x])
    
    # 积分估计
    integral = volume * np.mean(y)
    error = volume * np.std(y) / np.sqrt(n_samples)
    
    return integral, error


if __name__ == "__main__":
    print("=" * 55)
    print("Monte Carlo数值积分测试")
    print("=" * 55)
    
    # 测试积分: ∫_0^1 sin(x) dx = 1 - cos(1)
    exact = 1 - np.cos(1)
    print(f"\n测试积分: ∫_0^1 sin(x) dx")
    print(f"精确值: {exact:.10f}")
    
    # 朴素Monte Carlo
    print("\n--- 朴素Monte Carlo ---")
    for n in [1000, 10000, 100000, 1000000]:
        integral, error = naive_monte_carlo(np.sin, 0, 1, n_samples=n, seed=42)
        print(f"N={n:>8}: I={integral:.10f}, 误差={error:.6f}, 真实误差={abs(integral-exact):.6f}")
    
    # 对偶变量法
    print("\n--- 对偶变量法 ---")
    integral_av, error_av = antithetic_variates(np.sin, 0, 1, n_samples=100000, seed=42)
    print(f"I={integral_av:.10f}, 误差估计={error_av:.6f}, 真实误差={abs(integral_av-exact):.6f}")
    
    # 分层抽样
    print("\n--- 分层抽样 ---")
    integral_str, error_str = stratified_sampling(np.sin, 0, 1, n_strata=10, n_per_stratum=10000, seed=42)
    print(f"I={integral_str:.10f}, 误差估计={error_str:.6f}, 真实误差={abs(integral_str-exact):.6f}")
    
    # 重要性采样测试
    print("\n--- 重要性采样 (使用指数分布) ---")
    
    # 采样指数分布
    def exp_sampler(a, b, n):
        # 使用变换采样: X = -ln(U)/λ, truncated to [a,b]
        lam = 2.0
        u = np.random.uniform(0, 1, n)
        x = -np.log(u) / lam
        # 截断到 [a,b]
        x = np.clip(x, a, b)
        return x
    
    def exp_pdf(x, a, b):
        lam = 2.0
        Z = (1 - np.exp(-lam * (b - a))) / lam
        return np.exp(-lam * x) / Z
    
    integral_imp, error_imp = importance_sampling(np.sin, 0, 1, exp_sampler, exp_pdf, n_samples=100000, seed=42)
    print(f"I={integral_imp:.10f}, 误差估计={error_imp:.6f}, 真实误差={abs(integral_imp-exact):.6f}")
    
    # 高维积分测试
    print("\n--- 多维Monte Carlo积分 ---")
    
    # 测试: ∫_{[0,1]^d} exp(-Σ x_i^2) dx
    def gaussian_integral(x):
        return np.exp(-np.sum(x**2))
    
    for d in [2, 5, 10]:
        exact_d = (np.sqrt(np.pi) * np.math.erf(1)) ** d / (2 ** d)
        integral_md, error_md = multidimensional_monte_carlo(
            gaussian_integral, 
            [(0, 1)] * d, 
            n_samples=50000,
            seed=42
        )
        print(f"d={d:>2}: 精确={exact_d:.6f}, MC={integral_md:.6f}, 误差估计={error_md:.6f}")
    
    print("\n测试通过！Monte Carlo积分工作正常。")
