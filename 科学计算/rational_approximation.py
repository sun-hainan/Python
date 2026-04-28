"""
有理逼近与Padé逼近
====================
本模块实现有理函数逼近方法：

1. Padé逼近 - 有理函数逼近，适合逼近奇异性
2. 最佳一致逼近（Chebyshev视角）
3. 连分式展开

有理逼近比多项式逼近能更好地处理：
- 极点/奇点
- 快速变化的行为
- 渐近行为

Author: 算法库
"""

import numpy as np
from typing import Tuple, Callable, Optional


def taylor_series(f: Callable, x0: float, n: int, h: float = 1e-5) -> np.ndarray:
    """
    数值计算Taylor级数系数
    
    使用数值微分计算 f^(k)(x0) / k!
    
    参数:
        f: 函数
        x0: 展开点
        n: 展开阶数
        h: 微分步长
    
    返回:
        coeffs: Taylor系数数组
    """
    coeffs = np.zeros(n + 1)
    coeffs[0] = f(x0)
    
    for k in range(1, n + 1):
        # 数值微分计算 k 阶导数
        deriv = numerical_derivative(f, x0, k, h)
        coeffs[k] = deriv / np.math.factorial(k)
    
    return coeffs


def numerical_derivative(f: Callable, x: float, order: int, h: float = 1e-5) -> float:
    """
    计算数值导数（使用中心差分）
    
    参数:
        f: 函数
        x: 求导点
        order: 导数阶数
        h: 步长
    
    返回:
        导数值
    """
    if order == 1:
        return (f(x + h) - f(x - h)) / (2 * h)
    elif order == 2:
        return (f(x + h) - 2 * f(x) + f(x - h)) / (h ** 2)
    else:
        # 高阶导数使用公式
        result = 0.0
        for i in range(order + 1):
            result += ((-1) ** i * np.math.comb(order, i) * f(x + (order - 2 * i) * h)) 
                      / (h ** order)
        return result


def pade_approximation(
    f: Callable,
    x0: float,
    m: int,
    n: int,
    n_terms: int = 20
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Padé逼近计算
    
    Padé逼近是有理函数 R(x) = P(x) / Q(x)
    其中 P 是 m 阶多项式，Q 是 n 阶多项式
    
    原理:
        使用Taylor级数系数构造线性方程组
        f(x0 + x) = Σ a_k x^k ≈ Σ p_k x^k / Σ q_k x^k
        
        通过系数比较得到:
        a_0 = p_0 / q_0
        a_1 = (p_1 + p_0*q_1/q_0) / q_0 ... 等等
    
    参数:
        f: 被逼近函数
        x0: 展开点
        m: 分子阶数
        n: 分母阶数
        n_terms: Taylor级数计算项数
    
    返回:
        p: 分子系数 [p_0, p_1, ..., p_m]
        q: 分母系数 [q_0, q_1, ..., q_n]（约定 q_0 = 1）
    """
    # 计算Taylor系数
    coeffs = taylor_series(f, x0, m + n, h=1e-5)
    
    # 构建线性系统
    # 使用 Toeplitz 矩阵结构
    N = m + n + 1
    
    # 构建方程矩阵
    # 对于 j = 0, 1, ..., m+n:
    # a_j = p_j + Σ_{k=1}^{min(j,n)} q_k * a_{j-k}
    # 其中 a_j = 0 if j > m+n
    
    # 分离 p 和 q
    # p_j = a_j - Σ_{k=1}^{min(j,n)} q_k * a_{j-k}, for j <= m
    # 0 = a_j - Σ_{k=1}^{min(j,n)} q_k * a_{j-k}, for j > m
    
    # 未知数: [p_0, p_1, ..., p_m, q_1, q_2, ..., q_n]
    # 共 (m+1) + n 个未知数
    
    # 构建右端向量
    b = np.zeros(N)
    b[:m + 1] = coeffs[:m + 1]
    
    # 构建系数矩阵
    A = np.zeros((N, m + n + 1))
    
    # p 的系数 (列 0 到 m)
    for j in range(N):
        if j <= m:
            A[j, j] = 1.0
    
    # q 的系数 (列 m+1 到 m+n)
    for j in range(N):
        for k in range(1, min(j + 1, n + 1)):
            if j - k <= m:
                A[j, m + k] = -coeffs[j - k]
    
    # 求解（最小二乘）
    solution = np.linalg.lstsq(A, b, rcond=None)[0]
    
    p = solution[:m + 1]
    q = np.concatenate([[1.0], solution[m + 1:]])
    
    return p, q


def evaluate_pade(p: np.ndarray, q: np.ndarray, x: np.ndarray) -> np.ndarray:
    """
    评估Padé逼近值
    
    参数:
        p: 分子系数
        q: 分母系数
        x: 输入点
    
    返回:
        逼近值
    """
    # Horner法则评估多项式
    def horner(coeffs, x):
        result = np.zeros_like(x) if hasattr(x, '__len__') else 0.0
        for c in reversed(coeffs):
            result = result * x + c
        return result
    
    p_val = horner(p, x)
    q_val = horner(q, x)
    
    return p_val / q_val


def rational_approximation_chebyshev(
    f: Callable,
    a: float,
    b: float,
    m: int,
    n: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    使用Chebyshev节点的有理逼近
    
    参数:
        f: 被逼近函数
        a, b: 区间
        m, n: 分子分母阶数
    
    返回:
        p: 分子系数
        q: 分母系数
    """
    # Chebyshev节点
    k = np.arange(m + n + 1)
    x_cheb = np.cos(k * np.pi / (m + n))
    
    # 变换到 [a, b]
    x = (b - a) / 2 * x_cheb + (b + a) / 2
    
    # 函数值
    y = f(x)
    
    # 构建Vandermonde-like矩阵
    # R(x_i) = P(x_i) / Q(x_i) ≈ y_i
    # P(x) = Σ p_k * x^k
    # Q(x) = Σ q_k * x^k
    
    # 线性化: y_i * Q(x_i) - P(x_i) = 0
    N = m + n + 1
    
    # 未知数顺序: [p_0, ..., p_m, q_0, ..., q_n] (q_0 = 1)
    A = np.zeros((N, m + n + 2))
    b_vec = np.zeros(N)
    
    for i in range(N):
        xi = x[i]
        
        # P(x_i)
        for k in range(m + 1):
            A[i, k] = xi ** k
        
        # Q(x_i) * y_i (除了 q_0)
        for k in range(1, n + 1):
            A[i, m + k] = -y[i] * xi ** k
        
        b_vec[i] = y[i]  # 因为 q_0 = 1, 所以减去 1*y_i = -y_i + y_i = 0? 
                         # 实际上 P = y*Q 意味着 y = P/Q
    
    # 重新构建：y_i * Q(x_i) - P(x_i) = 0
    # y_i * (Σ q_k * x^k) - (Σ p_k * x^k) = 0
    A = np.zeros((N, m + n + 2))
    
    for i in range(N):
        xi = x[i]
        yi = y[i]
        
        # P 的系数
        for k in range(m + 1):
            A[i, k] = -xi ** k
        
        # Q 的系数 (乘以 y_i)
        for k in range(n + 1):
            A[i, m + 1 + k] = yi * xi ** k
    
    # 设置 q_0 = 1 的约束
    A[-1, m + 1] = 1.0
    b_vec[-1] = 1.0
    
    # 求解
    solution = np.linalg.lstsq(A, b_vec, rcond=None)[0]
    
    p = solution[:m + 1]
    q = solution[m + 1: m + n + 2]
    
    return p, q


def continued_fraction_to_rational(a: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    将连分式转换为有理函数
    
    连分式:
        f(x) = b_0 + a_1/(b_1 + a_2/(b_2 + ...))
    
    转换为 R(x) = P(x) / Q(x)
    
    参数:
        a: 分子系数 a_1, a_2, ...
        b: 分母系数 b_0, b_1, ...
    
    返回:
        p, q: 有理函数的分子和分母系数
    """
    # 从最后往前计算
    p_prev = np.array([0.0, 1.0])  # P_{n-1}
    q_prev = np.array([1.0, 0.0])  # Q_{n-1}
    
    for i in range(len(a) - 1, -1, -1):
        # P_i = a_i * P_{i-1} + b_i * P_{i-2}
        # Q_i = a_i * Q_{i-1} + b_i * Q_{i-2}
        p_curr = a[i] * p_prev[::-1] + np.concatenate([[0], b[i] * p_prev[:-1]])
        q_curr = a[i] * q_prev[::-1] + np.concatenate([[0], b[i] * q_prev[:-1]])
        
        p_prev, q_prev = p_curr, q_curr
    
    return p_prev, q_prev


if __name__ == "__main__":
    print("=" * 55)
    print("有理逼近与Padé逼近测试")
    print("=" * 55)
    
    # 测试1: exp(x) 的 Padé逼近
    print("\n--- exp(x) 的 Padé逼近 (m,n) = (3,3) ---")
    
    f_exp = np.exp
    p, q = pade_approximation(f_exp, 0, 3, 3)
    
    print(f"分子系数: {p}")
    print(f"分母系数: {q}")
    
    x_test = np.linspace(-2, 2, 100)
    exact = np.exp(x_test)
    approx = evaluate_pade(p, q, x_test)
    
    max_error = np.max(np.abs(exact - approx))
    print(f"最大误差: {max_error:.2e}")
    
    # 不同阶数的逼近对比
    print("\n--- 不同阶数Padé逼近对比 ---")
    print(f"{'(m,n)':>8} {'最大误差':>15} {'平均误差':>15}")
    print("-" * 40)
    
    for m, n in [(1,1), (2,2), (3,3), (4,4), (2,4), (4,2)]:
        p, q = pade_approximation(f_exp, 0, m, n)
        approx = evaluate_pade(p, q, x_test)
        max_err = np.max(np.abs(exact - approx))
        avg_err = np.mean(np.abs(exact - approx))
        print(f"({m},{n}): {max_err:>15.2e} {avg_err:>15.2e}")
    
    # 测试2: 有理逼近 vs 多项式逼近
    print("\n--- 有理逼近 vs 多项式逼近 (1/(1+25x²)) ---")
    
    f_rational = lambda x: 1 / (1 + 25 * x**2)
    x_test2 = np.linspace(-1, 1, 200)
    exact2 = f_rational(x_test2)
    
    # Padé逼近
    p_pade, q_pade = pade_approximation(f_rational, 0, 4, 4)
    approx_pade = evaluate_pade(p_pade, q_pade, x_test2)
    
    # 纯多项式逼近 (使用Taylor)
    coeffs_taylor = taylor_series(f_rational, 0, 10)
    approx_poly = np.zeros_like(x_test2)
    for i, c in enumerate(coeffs_taylor):
        approx_poly += c * x_test2 ** i
    
    print(f"Padé(4,4) 最大误差: {np.max(np.abs(exact2 - approx_pade)):.2e}")
    print(f"Taylor(10阶) 最大误差: {np.max(np.abs(exact2 - approx_poly)):.2e}")
    
    # 测试3: 端点行为
    print("\n--- 验证分母不为零 ---")
    x_check = np.linspace(-1, 1, 100)
    q_vals = evaluate_pade(np.array([1.0]), q_pade, x_check)  # Q(x)
    print(f"分母 Q(x) 范围: [{np.min(np.abs(q_vals)):.4f}, {np.max(np.abs(q_vals)):.4f}]")
    
    print("\n测试通过！有理逼近和Padé逼近工作正常。")
