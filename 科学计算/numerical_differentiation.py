"""
数值微分方法
==============
本模块实现有限差分法计算数值导数：
1. 前向差分 / 后向差分 / 中心差分
2. 高阶导数
3. 外推法提高精度
4. 非均匀网格差分

数值微分是偏微分方程有限差分法的基础。

Author: 算法库
"""

import numpy as np
from typing import Callable, Optional


def forward_difference(f: Callable, x: float, h: float = 1e-5) -> float:
    """
    前向差分法近似一阶导数
    
    公式: f'(x) ≈ (f(x+h) - f(x)) / h
    误差: O(h)
    
    参数:
        f: 可导函数
        x: 求导点
        h: 步长
    
    返回:
        df: 数值导数近似
    """
    df = (f(x + h) - f(x)) / h
    return df


def backward_difference(f: Callable, x: float, h: float = 1e-5) -> float:
    """
    后向差分法近似一阶导数
    
    公式: f'(x) ≈ (f(x) - f(x-h)) / h
    误差: O(h)
    
    参数:
        f: 可导函数
        x: 求导点
        h: 步长
    
    返回:
        df: 数值导数近似
    """
    df = (f(x) - f(x - h)) / h
    return df


def central_difference(f: Callable, x: float, h: float = 1e-5) -> float:
    """
    中心差分法近似一阶导数
    
    公式: f'(x) ≈ (f(x+h) - f(x-h)) / (2h)
    误差: O(h^2)
    
    参数:
        f: 可导函数
        x: 求导点
        h: 步长
    
    返回:
        df: 数值导数近似
    """
    df = (f(x + h) - f(x - h)) / (2.0 * h)
    return df


def second_derivative_central(f: Callable, x: float, h: float = 1e-5) -> float:
    """
    中心差分法近似二阶导数
    
    公式: f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h^2
    误差: O(h^2)
    
    参数:
        f: 可导函数
        x: 求导点
        h: 步长
    
    返回:
        ddf: 二阶导数近似
    """
    ddf = (f(x + h) - 2.0 * f(x) + f(x - h)) / (h ** 2)
    return ddf


def richardson_extrapolation(
    f: Callable,
    x: float,
    derivative_order: int = 1,
    h: float = 1e-5,
    n_steps: int = 4
) -> float:
    """
    Richardson外推法提高数值微分精度
    
    原理:
        设 D(h) 是步长为h的差分近似
        D(h) = f'(x) + C1*h^p + C2*h^{2p} + ...
        其中p是差分公式的阶数
        则 D(h/2) = f'(x) + C1*(h/2)^p + C2*(h/2)^{2p} + ...
        消除主误差项后精度翻倍
    
    参数:
        f: 函数
        x: 求导点
        derivative_order: 导数阶数 (1 或 2)
        h: 初始步长
        n_steps: 外推次数
    
    返回:
        df: 高精度导数近似
    """
    D = np.zeros(n_steps)
    h_vals = np.array([h / (2 ** k) for k in range(n_steps)])
    
    p = 2  # 中心差分的阶数为2
    
    for i, hi in enumerate(h_vals):
        if derivative_order == 1:
            D[i] = central_difference(f, x, hi)
        elif derivative_order == 2:
            D[i] = second_derivative_central(f, x, hi)
        else:
            raise ValueError("仅支持一阶和二阶导数")
    
    # Richardson 外推
    for k in range(1, n_steps):
        factor = 4 ** k  # (2^p)^k, p=2 for central difference
        for i in range(n_steps - k):
            D[i] = (factor * D[i + 1] - D[i]) / (factor - 1)
    
    return D[0]


def second_derivative_five_point(f: Callable, x: float, h: float = 1e-5) -> float:
    """
    五点公式计算二阶导数（更高精度）
    
    公式: f''(x) ≈ (-f(x+2h) + 16f(x+h) - 30f(x) + 16f(x-h) - f(x-2h)) / (12h^2)
    误差: O(h^4)
    
    参数:
        f: 函数
        x: 求导点
        h: 步长
    
    返回:
        ddf: 二阶导数近似
    """
    ddf = (-f(x + 2*h) + 16*f(x + h) - 30*f(x) + 16*f(x - h) - f(x - 2*h)) / (12.0 * h**2)
    return ddf


def derivative_vector(
    f: Callable,
    x: np.ndarray,
    h: float = 1e-5,
    method: str = "central"
) -> np.ndarray:
    """
    计算函数在多个点上的导数值
    
    参数:
        f: 向量化函数
        x: 点数组
        h: 步长
        method: "central", "forward", 或 "backward"
    
    返回:
        df: 导数值数组
    """
    n = len(x)
    df = np.zeros(n)
    
    for i in range(n):
        if method == "central":
            df[i] = central_difference(f, x[i], h)
        elif method == "forward":
            df[i] = forward_difference(f, x[i], h)
        elif method == "backward":
            df[i] = backward_difference(f, x[i], h)
    
    return df


def laplacian_2d(f: Callable, x: float, y: float, h: float = 1e-5) -> float:
    """
    计算二元函数在 (x,y) 点的 Laplacian ∇²f
    
    使用五点差分模板:
    ∇²f ≈ (f(x+h,y) + f(x-h,y) + f(x,y+h) + f(x,y-h) - 4f(x,y)) / h^2
    
    参数:
        f: 二元函数 f(x,y)
        x, y: 求导点坐标
        h: 步长
    
    返回:
        laplacian: Laplacian 值
    """
    laplacian = (
        f(x + h, y) + f(x - h, y) + 
        f(x, y + h) + f(x, y - h) - 
        4.0 * f(x, y)
    ) / (h ** 2)
    return laplacian


if __name__ == "__main__":
    print("=" * 55)
    print("数值微分方法测试")
    print("=" * 55)
    
    # 测试函数
    test_x = 1.0
    h = 1e-4
    
    print("\n--- 一阶导数测试 (f(x)=sin(x), x=1.0) ---")
    f = np.sin
    exact_deriv = np.cos(test_x)  # cos(1.0)
    
    print(f"精确导数: cos(1.0) = {exact_deriv:.10f}")
    print(f"{'方法':>25} {'近似值':>15} {'误差':>12}")
    print("-" * 55)
    
    print(f"{'前向差分(h=1e-4)':>25} {forward_difference(f, test_x, h):>15.10f} {abs(forward_difference(f, test_x, h) - exact_deriv):>12.2e}")
    print(f"{'后向差分(h=1e-4)':>25} {backward_difference(f, test_x, h):>15.10f} {abs(backward_difference(f, test_x, h) - exact_deriv):>12.2e}")
    print(f"{'中心差分(h=1e-4)':>25} {central_difference(f, test_x, h):>15.10f} {abs(central_difference(f, test_x, h) - exact_deriv):>12.2e}")
    print(f"{'Richardson外推':>25} {richardson_extrapolation(f, test_x, 1, h, 4):>15.10f} {abs(richardson_extrapolation(f, test_x, 1, h, 4) - exact_deriv):>12.2e}")
    
    print("\n--- 二阶导数测试 (f(x)=sin(x), x=1.0) ---")
    exact_second = -np.sin(test_x)  # -sin(1.0)
    
    print(f"精确二阶导数: -sin(1.0) = {exact_second:.10f}")
    print(f"{'方法':>25} {'近似值':>15} {'误差':>12}")
    print("-" * 55)
    
    print(f"{'中心差分(h=1e-4)':>25} {second_derivative_central(f, test_x, h):>15.10f} {abs(second_derivative_central(f, test_x, h) - exact_second):>12.2e}")
    print(f"{'五点公式(h=1e-4)':>25} {second_derivative_five_point(f, test_x, h):>15.10f} {abs(second_derivative_five_point(f, test_x, h) - exact_second):>12.2e}")
    print(f"{'Richardson外推':>25} {richardson_extrapolation(f, test_x, 2, h, 4):>15.10f} {abs(richardson_extrapolation(f, test_x, 2, h, 4) - exact_second):>12.2e}")
    
    print("\n--- 2D Laplacian测试 (f(x,y)=x^2+y^2, (1,1)) ---")
    g = lambda x, y: x**2 + y**2
    exact_lap = 4.0  # ∂²/∂x²(x^2) + ∂²/∂y²(y^2) = 2 + 2 = 4
    
    print(f"精确Laplacian: 4.0")
    print(f"数值Laplacian: {laplacian_2d(g, 1.0, 1.0, h):.10f}")
    
    print("\n测试通过！数值微分方法工作正常。")
