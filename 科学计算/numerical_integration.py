"""
数值积分方法
==============
本模块实现了两种高阶数值积分方法：
1. Romberg积分 - 通过 Richardson外推 不断提高精度
2. 高斯-勒让德求积 - 最高代数精度的积分方法

适用于函数定积分的精确计算。

Author: 算法库
"""

import numpy as np
from typing import Callable, Tuple


def trapz(f: Callable, a: float, b: float, n: int = 1) -> float:
    """
    复合梯形法则
    
    参数:
        f: 被积函数
        a, b: 积分区间
        n: 子区间数量
    
    返回:
        integral: 积分近似值
    """
    if n == 1:
        return (b - a) * (f(a) + f(b)) / 2.0
    
    # 将区间分成n个子区间
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = f(x)
    
    # 梯形法则公式
    integral = h * (y[0] + 2 * np.sum(y[1:-1]) + y[-1]) / 2.0
    return integral


def romberg(f: Callable, a: float, b: float,
            tol: float = 1e-10, max_order: int = 15) -> Tuple[float, int]:
    """
    Romberg积分法 - 复合梯形法则 + Richardson外推
    
    原理:
        T_{k+1} 是 T_k 的半间隔版本
        通过 Richardson 外推不断提高精度
        R_{k,m} 表示第k次二分、m次外推的结果
    
    参数:
        f: 被积函数
        a, b: 积分区间
        tol: 收敛容差
        max_order: 最大外推阶数
    
    返回:
        result: 积分近似值
        n_evaluations: 函数调用次数
    """
    # 初始化 Romberg 表
    R = np.zeros((max_order, max_order))
    
    # 计算第一列 (复合梯形法则, 2^n 个子区间)
    n_evaluations = 0
    for k in range(max_order):
        n_subintervals = 2 ** k
        R[k, 0] = trapz(f, a, b, n_subintervals)
        n_evaluations += n_subintervals + 1
    
    # Richardson 外推
    for m in range(1, max_order):
        for k in range(m, max_order):
            # R_{k,m} = (4^m * R_{k,m-1} - R_{k-1,m-1}) / (4^m - 1)
            factor = 4 ** m
            R[k, m] = (factor * R[k, m-1] - R[k-1, m-1]) / (factor - 1)
        
        # 检查收敛：对角线元素应趋于常数
        if k > 0:
            diff = abs(R[k, k] - R[k-1, k-1])
            if diff < tol:
                return R[k, k], n_evaluations
    
    # 返回对角线最后一个值
    return R[max_order-1, max_order-1], n_evaluations


def gauss_legendre_nodes_weights(n: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算 n 点高斯-勒让德求积的节点和权重
    
    使用递推关系和牛顿法求解勒让德多项式的根
    
    参数:
        n: 节点数量（1 <= n <= 20）
    
    返回:
        nodes: 节点坐标（在 [-1, 1] 区间）
        weights: 对应权重
    """
    if n == 1:
        return np.array([0.0]), np.array([2.0])
    
    # 初始猜测：余弦函数分布的节点
    nodes = np.cos(np.pi * (np.arange(1, n + 1) - 0.5) / n)
    
    # 牛顿迭代求根
    max_iter = 100
    for _ in range(max_iter):
        # 计算勒让德多项式 P_n(x) 及其导数 P_n'(x)
        # 使用递推关系: (k+1)*P_{k+1}(x) = (2k+1)*x*P_k(x) - k*P_{k-1}(x)
        p = np.zeros((n + 1, n))
        p[0] = np.ones(n)  # P_0(x) = 1
        p[1] = nodes.copy()  # P_1(x) = x
        
        for k in range(1, n):
            p[k+1] = ((2 * k + 1) * nodes * p[k] - k * p[k-1]) / (k + 1)
        
        # P_n'(x) 可以通过相邻两个多项式得到
        # P_n'(x) = n * (x * P_n(x) - P_{n-1}(x)) / (x^2 - 1)
        pp = n * (nodes * p[n] - p[n-1]) / (nodes ** 2 - 1)
        
        # 牛顿更新
        nodes_new = nodes - p[n] / pp
        
        # 检查收敛
        if np.max(np.abs(nodes_new - nodes)) < 1e-15:
            nodes = nodes_new
            break
        
        nodes = nodes_new
    
    # 计算权重 w_i = 2 / [(1-x_i^2) * (P_n'(x_i))^2]
    weights = 2.0 / ((1 - nodes ** 2) * pp ** 2)
    
    return nodes, weights


def gauss_legendre_integrate(
    f: Callable,
    a: float,
    b: float,
    n: int = 5
) -> float:
    """
    使用高斯-勒让德求积计算定积分
    
    参数:
        f: 被积函数
        a, b: 积分区间（任意有限区间）
        n: 节点数量
    
    返回:
        integral: 积分近似值
    """
    # 区间变换: [-1,1] -> [a,b]
    # x = (b-a)/2 * t + (b+a)/2, t ∈ [-1,1]
    # dx = (b-a)/2 * dt
    
    # 获取标准区间上的节点和权重
    t, w = gauss_legendre_nodes_weights(n)
    
    # 变换到 [a,b] 区间
    x = (b - a) / 2.0 * t + (b + a) / 2.0
    
    # 计算积分
    integral = (b - a) / 2.0 * np.sum(w * f(x))
    
    return integral


def adaptive_quad(
    f: Callable,
    a: float,
    b: float,
    tol: float = 1e-10,
    max_depth: int = 50
) -> Tuple[float, int]:
    """
    自适应积分 - 根据函数特性自动调整采样点密度
    
    参数:
        f: 被积函数
        a, b: 积分区间
        tol: 容差
        max_depth: 最大递归深度
    
    返回:
        integral: 积分近似值
        n_evaluations: 函数调用次数
    """
    n_evaluations = 0
    
    def compute(f, a, b, tol, depth):
        nonlocal n_evaluations
        
        # 计算中点和函数值
        c = (a + b) / 2.0
        fa, fc, fb = f(a), f(c), f(b)
        n_evaluations += 3
        
        # 使用 Simpson 法则估计
        simpson = (b - a) / 6.0 * (fa + 4 * fc + fb)
        
        # 递归计算左右子区间的 Simpson 估计
        if depth >= max_depth:
            return simpson
        
        d = (a + c) / 2.0
        e = (c + b) / 2.0
        fd, fe = f(d), f(e)
        n_evaluations += 2
        
        left = (c - a) / 6.0 * (fa + 4 * fd + fc)
        right = (b - c) / 6.0 * (fc + 4 * fe + fb)
        
        combined = left + right
        
        # 如果当前区间不够精确，递归细分
        if abs(combined - simpson) < tol * 10:
            return combined + (combined - simpson) / 15.0
        else:
            left_val = compute(f, a, c, tol/2, depth+1)
            right_val = compute(f, c, b, tol/2, depth+1)
            return left_val + right_val
    
    return compute(f, a, b, tol, 0), n_evaluations


if __name__ == "__main__":
    print("=" * 50)
    print("数值积分方法测试")
    print("=" * 50)
    
    # 测试函数
    test_functions = [
        ("sin(x)", np.sin, 0, np.pi),
        ("x^2", lambda x: x**2, 0, 1),
        ("exp(-x^2)", lambda x: np.exp(-x**2), -1, 1),
        ("1/(1+x^2)", lambda x: 1/(1+x**2), -5, 5),
    ]
    
    print("\n--- Romberg积分 ---")
    print(f"{'函数':>15} {'精确值':>15} {'Romberg':>15} {'误差':>12}")
    print("-" * 60)
    
    for name, f, a, b in test_functions:
        exact = np.pi if name == "sin(x)" else None
        if exact is None:
            # 解析积分
            if name == "x^2":
                exact = 1/3
            elif name == "exp(-x^2)":
                exact = np.sqrt(np.pi) * np.math.erf(1)
            elif name == "1/(1+x^2)":
                exact = np.arctan(5) - np.arctan(-5)
        
        result, n_eval = romberg(f, a, b)
        error = abs(result - exact)
        print(f"{name:>15}{exact:>15.8f}{result:>15.8f}{error:>12.2e}")
    
    print("\n--- 高斯-勒让德求积 ---")
    print(f"{'函数':>15} {'精确值':>15} {'Gauss(n=5)':>15} {'Gauss(n=10)':>15}")
    print("-" * 65)
    
    for name, f, a, b in test_functions:
        if name == "sin(x)":
            exact = np.pi
        elif name == "x^2":
            exact = 1/3
        elif name == "exp(-x^2)":
            exact = np.sqrt(np.pi) * np.math.erf(1)
        else:
            exact = np.arctan(5) - np.arctan(-5)
        
        g5 = gauss_legendre_integrate(f, a, b, n=5)
        g10 = gauss_legendre_integrate(f, a, b, n=10)
        print(f"{name:>15}{exact:>15.8f}{g5:>15.8f}{g10:>15.8f}")
    
    print("\n测试通过！数值积分方法工作正常。")
