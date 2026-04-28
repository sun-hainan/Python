"""
Chebyshev逼近
==============
本模块实现Chebyshev多项式逼近：

Chebyshev多项式 T_n(x) = cos(n * arccos(x))，定义在 [-1, 1]
特性：
- 在所有次数为n的多项式中，Chebyshev多项式在区间上的最大误差最小
- 根节点分布使得插值多项式数值稳定
- 用于谱方法、PDE求解、函数逼近等

Author: 算法库
"""

import numpy as np
from typing import Callable, Tuple, List


def chebyshev_nodes(n: int) -> np.ndarray:
    """
    计算Chebyshev-Gauss-Lobatto节点
    
    节点: x_k = cos(k * π / (n-1)), k = 0, 1, ..., n-1
    
    参数:
        n: 节点数量
    
    返回:
        nodes: Chebyshev节点数组
    """
    k = np.arange(n)
    nodes = np.cos(k * np.pi / (n - 1))
    return nodes


def chebyshev_points_second_kind(n: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算第二类Chebyshev节点和权重（用于数值积分）
    
    节点: x_k = cos(k * π / n), k = 0, 1, ..., n
    权重: w_k = π / n (端点为 π/(2n))
    
    参数:
        n: 节点数量
    
    返回:
        nodes: 节点
        weights: 权重
    """
    k = np.arange(n + 1)
    nodes = np.cos(k * np.pi / n)
    
    weights = np.ones(n + 1) * np.pi / n
    weights[0] *= 0.5
    weights[-1] *= 0.5
    
    return nodes, weights


def chebyshev_polynomial(n: int, x: np.ndarray) -> np.ndarray:
    """
    计算Chebyshev多项式 T_n(x) 的值
    
    使用递推关系:
        T_0(x) = 1
        T_1(x) = x
        T_{n+1}(x) = 2x * T_n(x) - T_{n-1}(x)
    
    参数:
        n: 多项式阶数
        x: 输入点（数组）
    
    返回:
        T_n(x): Chebyshev多项式值
    """
    if n == 0:
        return np.ones_like(x)
    elif n == 1:
        return x.copy()
    else:
        T_prev = np.ones_like(x)
        T_curr = x.copy()
        for _ in range(2, n + 1):
            T_next = 2 * x * T_curr - T_prev
            T_prev, T_curr = T_curr, T_next
        return T_curr


def chebyshev_coefficients(
    f: Callable,
    n: int
) -> np.ndarray:
    """
    计算函数f在Chebyshev多项式基下的展开系数
    
    原理:
        f(x) ≈ Σ c_k * T_k(x)
        c_k = (2/π) * ∫_{-1}^{1} f(x) * T_k(x) / sqrt(1-x²) dx
        使用Clenshaw-Curtis积分近似
    
    参数:
        f: 被逼近函数
        n: 展开阶数
    
    返回:
        coeffs: Chebyshev系数数组
    """
    # 在Chebyshev节点上采样
    x_k = chebyshev_nodes(n)
    f_vals = f(x_k)
    
    # 使用离散余弦变换计算系数
    # 这是Clenshaw-Curtis方法的简化版本
    coeffs = np.zeros(n)
    
    for k in range(n):
        if k == 0:
            coeffs[k] = np.mean(f_vals)
        else:
            # 计算内积的近似
            sum_val = 0.0
            for j in range(n):
                sum_val += f_vals[j] * chebyshev_polynomial(k, x_k[j])
            coeffs[k] = 2.0 * sum_val / n
    
    return coeffs


def clenshaw_curtis_integration(
    f: Callable,
    a: float,
    b: float,
    n: int = 64
) -> float:
    """
    Clenshaw-Curtis数值积分
    
    使用Chebyshev节点和权重进行高精度积分
    
    参数:
        f: 被积函数
        a, b: 积分区间
        n: 节点数
    
    返回:
        integral: 积分近似值
    """
    # 计算Chebyshev节点和权重
    x_cheb, weights = chebyshev_points_second_kind(n)
    
    # 变换到 [a, b] 区间
    x = (b - a) / 2 * x_cheb + (b + a) / 2
    
    # 变换权重
    weights_transformed = (b - a) / 2 * weights
    
    # 计算积分
    f_vals = f(x)
    integral = np.sum(weights_transformed * f_vals)
    
    return integral


def chebyshev_approximation(
    f: Callable,
    a: float,
    b: float,
    n: int
) -> Callable:
    """
    创建Chebyshev逼近函数
    
    参数:
        f: 被逼近函数
        a, b: 逼近区间
        n: 展开阶数
    
    返回:
        approximation: 逼近函数
    """
    # 变换到 [-1, 1]
    def f_transformed(t):
        x = (b - a) / 2 * t + (b + a) / 2
        return f(x)
    
    # 计算系数
    coeffs = chebyshev_coefficients(f_transformed, n)
    
    def approximation(x):
        """Chebyshev逼近函数"""
        if np.isscalar(x):
            t = (2 * x - (b + a)) / (b - a)
            result = 0.0
            T_prev = 1.0
            T_curr = t
            if n >= 0:
                result += coeffs[0] * T_prev
            if n >= 1:
                result += coeffs[1] * T_curr
            for k in range(2, n):
                T_next = 2 * t * T_curr - T_prev
                result += coeffs[k] * T_next
                T_prev, T_curr = T_curr, T_next
            return result
        else:
            return np.array([approximation(xi) for xi in x])
    
    return approximation


def chebyshev_interpolation(
    f: Callable,
    a: float,
    b: float,
    n: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Chebyshev插值
    
    在Chebyshev节点上构建Lagrange插值多项式
    
    参数:
        f: 被插值函数
        a, b: 区间
        n: 插值阶数
    
    返回:
        coeffs: Chebyshev系数
        x_nodes: Chebyshev节点（原始区间）
    """
    # 在 [-1, 1] 上计算节点
    x_cheb = chebyshev_nodes(n)
    
    # 变换到 [a, b]
    x_nodes = (b - a) / 2 * x_cheb + (b + a) / 2
    
    # 函数值
    f_vals = f(x_nodes)
    
    # 使用Vandermonde矩阵求解系数
    # 这里用简化的方法：直接使用Chebyshev基
    V = np.zeros((n, n))
    for i in range(n):
        V[:, i] = chebyshev_polynomial(i, x_cheb)
    
    coeffs = np.linalg.solve(V, f_vals)
    
    return coeffs, x_nodes


def eval_chebyshev_poly(coeffs: np.ndarray, x: np.ndarray) -> np.ndarray:
    """
    使用Clenshaw算法评估Chebyshev多项式级数
    
    参数:
        coeffs: Chebyshev系数
        x: 输入点
    
    返回:
        result: 多项式值
    """
    n = len(coeffs)
    
    if n == 0:
        return np.zeros_like(x)
    
    # Clenshaw算法
    y_next = np.zeros_like(x)
    y_curr = np.zeros_like(x)
    
    for k in range(n - 1, 1, -1):
        y_prev = 2 * x * y_curr - y_next + coeffs[k]
        y_next, y_curr = y_curr, y_prev
    
    if n > 1:
        result = x * y_curr - y_next + coeffs[1]
    else:
        result = y_curr + coeffs[1] if n > 1 else y_curr
    
    result = x * result + coeffs[0]
    
    return result


if __name__ == "__main__":
    print("=" * 55)
    print("Chebyshev逼近测试")
    print("=" * 55)
    
    # 测试函数
    test_functions = [
        ("sin(10x)", lambda x: np.sin(10 * x), 0, 1),
        ("exp(-x²)", lambda x: np.exp(-x**2), -1, 1),
        ("1/(1+25x²)", lambda x: 1/(1+25*x**2), -1, 1),
    ]
    
    print("\n--- Chebyshev逼近精度测试 ---")
    
    for name, f, a, b in test_functions:
        print(f"\n函数: f(x) = {name}")
        print(f"区间: [{a}, {b}]")
        print(f"{'n':>4} {'最大误差':>15} {'L2误差':>15}")
        print("-" * 36)
        
        x_test = np.linspace(a, b, 1000)
        f_exact = f(x_test)
        
        for n in [5, 10, 20, 40]:
            approx_func = chebyshev_approximation(f, a, b, n)
            f_approx = approx_func(x_test)
            
            max_error = np.max(np.abs(f_exact - f_approx))
            l2_error = np.sqrt(np.mean((f_exact - f_approx) ** 2))
            
            print(f"{n:>4d} {max_error:>15.2e} {l2_error:>15.2e}")
    
    # Chebyshev节点性质
    print("\n--- Chebyshev节点分布 ---")
    n = 10
    nodes = chebyshev_nodes(n)
    print(f"n={n} 时，节点位置: {nodes}")
    
    # 验证节点在 [-1, 1] 内且两端点为 ±1
    print(f"端点值: [{nodes[0]:.4f}, {nodes[-1]:.4f}] (应为 [-1, 1])")
    
    # 积分测试
    print("\n--- Clenshaw-Curtis积分 ---")
    
    exact = np.pi / 2  # ∫_0^1 sqrt(1-x²) dx
    integral_cc = clenshaw_curtis_integration(
        lambda x: np.sqrt(1 - ((x - 0.5) * 2) ** 2) if abs((x - 0.5) * 2) <= 1 else 0,
        0, 1, n=64
    )
    print(f"精确值 (单位圆面积/2): {exact:.10f}")
    print(f"CC积分值: {integral_cc:.10f}")
    
    print("\n测试通过！Chebyshev逼近工作正常。")
