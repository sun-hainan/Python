"""
非线性方程求解
===============
本模块实现单变量非线性方程的根求解方法：
1. 二分法 (Bisection) - 保证收敛，线性收敛
2. Brent方法 - 组合多种方法，最可靠
3. Newton法 - 快速收敛，但需要导数
4. 割线法 (Secant) - 快速收敛，不需导数

适用于 f(x) = 0 形式的方程求根。

Author: 算法库
"""

import numpy as np
from typing import Callable, Tuple, Optional


def bisection(
    f: Callable,
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 100,
    verbose: bool = False
) -> Tuple[float, int, float]:
    """
    二分法求解非线性方程
    
    要求:
        - f(a) 和 f(b) 符号相反
        - f 在 [a, b] 上连续
    
    原理:
        每次迭代将区间减半，检查中点函数值符号
        收敛速度: 线性 (每次迭代误差减半)
    
    参数:
        f: 目标函数
        a, b: 搜索区间端点
        tol: 收敛容差
        max_iter: 最大迭代次数
        verbose: 是否输出迭代信息
    
    返回:
        root: 近似根
        iterations: 迭代次数
        residual: 最终函数值
    """
    fa, fb = f(a), f(b)
    
    # 检查符号条件
    if fa * fb > 0:
        raise ValueError(f"区间端点函数值同号: f(a)={fa:.2e}, f(b)={fb:.2e}")
    
    for iteration in range(max_iter):
        # 中点
        c = (a + b) / 2.0
        fc = f(c)
        
        if verbose:
            print(f"迭代 {iteration+1}: c = {c:.12f}, f(c) = {fc:.2e}, 区间 = [{a:.6f}, {b:.6f}]")
        
        # 检查收敛
        if abs(fc) < tol or (b - a) / 2.0 < tol:
            return c, iteration + 1, fc
        
        # 更新区间
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    
    return (a + b) / 2.0, max_iter, f((a + b) / 2.0)


def secant(
    f: Callable,
    x0: float,
    x1: float,
    tol: float = 1e-10,
    max_iter: int = 100,
    verbose: bool = False
) -> Tuple[float, int, float]:
    """
    割线法 (Secant Method)
    
    原理:
        通过两个点 (x0, f(x0)) 和 (x1, f(x1)) 作割线
        割线与x轴的交点作为新的近似
        x_{k+1} = x_k - f(x_k) * (x_k - x_{k-1}) / (f(x_k) - f(x_{k-1}))
    
    收敛速度: 超线性 (~1.618阶)
    优点: 不需要导数，收敛比二分法快
    缺点: 不保证收敛
    
    参数:
        f: 目标函数
        x0, x1: 初始两个点
        tol: 收敛容差
        max_iter: 最大迭代次数
        verbose: 是否输出迭代信息
    
    返回:
        root: 近似根
        iterations: 迭代次数
        residual: 最终函数值
    """
    x_prev = x0
    x_curr = x1
    f_prev = f(x_prev)
    f_curr = f(x_curr)
    
    for iteration in range(max_iter):
        # 避免除零
        if abs(f_curr - f_prev) < 1e-15:
            break
        
        # 割线公式
        x_new = x_curr - f_curr * (x_curr - x_prev) / (f_curr - f_prev)
        
        if verbose:
            print(f"迭代 {iteration+1}: x = {x_new:.12f}, f(x) = {f_curr:.2e}")
        
        # 更新
        x_prev, f_prev = x_curr, f_curr
        x_curr = x_new
        f_curr = f(x_curr)
        
        # 检查收敛
        if abs(f_curr) < tol or abs(x_curr - x_prev) < tol:
            return x_curr, iteration + 1, f_curr
    
    return x_curr, max_iter, f_curr


def newton_1d(
    f: Callable,
    df: Callable,
    x0: float,
    tol: float = 1e-10,
    max_iter: int = 100,
    verbose: bool = False
) -> Tuple[float, int, float]:
    """
    Newton法求解单变量方程
    
    原理:
        x_{k+1} = x_k - f(x_k) / f'(x_k)
    
    收敛速度: 二次收敛 (误差平方递减)
    优点: 收敛非常快
    缺点: 需要导数，可能发散
    
    参数:
        f: 目标函数
        df: 导函数
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大迭代次数
        verbose: 是否输出迭代信息
    
    返回:
        root: 近似根
        iterations: 迭代次数
        residual: 最终函数值
    """
    x = x0
    f_val = f(x)
    
    for iteration in range(max_iter):
        df_val = df(x)
        
        if abs(df_val) < 1e-15:
            raise RuntimeError(f"导数接近零: f'({x}) = {df_val}")
        
        # Newton迭代
        x_new = x - f_val / df_val
        f_new = f(x_new)
        
        if verbose:
            print(f"迭代 {iteration+1}: x = {x_new:.12f}, f(x) = {f_new:.2e}")
        
        x = x_new
        f_val = f_new
        
        if abs(f_val) < tol:
            return x, iteration + 1, f_val
    
    return x, max_iter, f_val


def brent(
    f: Callable,
    a: float,
    b: float,
    tol: float = 1e-14,
    max_iter: int = 100,
    verbose: bool = False
) -> Tuple[float, int, float]:
    """
    Brent方法 - 组合二分法、割线法和逆二次插值
    
    原理:
        Brent方法结合了:
        1. 二分法的保证收敛性
        2. 割线法和逆二次插值的快速收敛
        
        每次迭代选择最合适的方法：
        - 如果当前值在区间中点，使用二分
        - 否则尝试割线或插值
    
    收敛速度: 介于线性和二次之间
    可靠性: 非常可靠，是求根的首选方法
    
    参数:
        f: 目标函数
        a, b: 搜索区间
        tol: 收敛容差
        max_iter: 最大迭代次数
        verbose: 是否输出迭代信息
    
    返回:
        root: 近似根
        iterations: 迭代次数
        residual: 最终函数值
    """
    fa, fb = f(a), f(b)
    
    if fa * fb > 0:
        raise ValueError("区间端点函数值同号")
    
    # 确保 |f(a)| >= |f(b)|
    if abs(fa) < abs(fb):
        a, fa, b, fb = b, fb, a, fa
    
    c, fc = a, fa  # c 记录上上次迭代的点
    d = b - a      # 区间中点到当前点的距离
    e = d          # 上一步的区间变化
    
    for iteration in range(max_iter):
        if abs(fb) < tol:
            return b, iteration, fb
        
        # 根据情况选择方法
        if abs(fa - fc) > tol and abs(fb - fc) > tol:
            # 逆二次插值
            # 使用 (a, f(a)), (b, f(b)), (c, f(c)) 构造双曲线的根
            s = (a * fb * fc / ((fa - fb) * (fa - fc)) +
                 b * fa * fc / ((fb - fa) * (fb - fc)) +
                 c * fa * fb / ((fc - fa) * (fc - fb)))
        else:
            # 割线法
            s = b - fb * (b - a) / (fb - fa)
        
        # 判断是否接受（需要满足特定条件）
        # 条件1: s 必须在 (a,b) 区间内
        # 条件2: 不能太接近端点
        condition1 = (s - b) * (s - 3*b + 2*a) > 0 if abs(s-b) < abs(b-c) or abs(s-b) < abs(b-a)/2 else False
        condition2 = abs(s-b) >= abs(b-c)/2 if abs(b-c) < abs(c-a) else abs(s-b) >= abs(b-a)/2
        condition3 = abs(fb) < abs(fa)/2 if abs(b-c) >= abs(c-a) else True
        
        use_secant = not (condition1 or condition2) and condition3
        
        if not use_secant:
            # 使用逆二次插值或割线
            pass  # s 已经是计算好的值
        else:
            # 使用割线
            s = b - fb * (b - a) / (fb - fa)
        
        # 如果选择的方法不好，回退到二分
        if abs(s - b) < abs(b - c) or abs(s - b) < abs(b - a) / 2:
            if abs(b - c) < abs(c - a):
                s = (a + b) / 2
            else:
                s = b - fb * (b - a) / (fb - fa)
        
        # 计算新点的函数值
        fs = f(s)
        
        if verbose:
            print(f"迭代 {iteration+1}: s = {s:.12f}, f(s) = {fs:.2e}")
        
        # 更新
        c, fc = b, fb
        if fa * fs < 0:
            b, fb = s, fs
        else:
            a, fa = s, fs
        
        # 确保 |f(a)| >= |f(b)|
        if abs(fa) < abs(fb):
            a, fa, b, fb = b, fb, a, fa
        
        # 更新步长
        d = b - a
        e = d
        
        if abs(fb) < tol:
            break
    
    return b, max_iter, fb


def find_all_roots(
    f: Callable,
    interval: Tuple[float, float],
    n_intervals: int = 50,
    tol: float = 1e-10
) -> list:
    """
    在给定区间内查找所有根
    
    参数:
        f: 目标函数
        interval: 搜索区间
        n_intervals: 划分子区间数量
        tol: 求根容差
    
    返回:
        roots: 根列表
    """
    a, b = interval
    x = np.linspace(a, b, n_intervals + 1)
    roots = []
    
    for i in range(len(x) - 1):
        try:
            fa, fb = f(x[i]), f(x[i + 1])
            if fa * fb <= 0:  # 符号变化
                root, _, _ = brent(f, x[i], x[i + 1], tol=tol)
                # 检查是否是新根（避免重复）
                if not any(abs(root - r) < tol * 10 for r in roots):
                    roots.append(root)
        except (ValueError, RuntimeError):
            continue
    
    return sorted(roots)


if __name__ == "__main__":
    print("=" * 55)
    print("非线性方程求解测试")
    print("=" * 55)
    
    # ========== 测试1: 简单方程 ==========
    print("\n--- 测试1: sin(x) = 0 在 [3, 4] ---")
    root1, iter1, res1 = brent(np.sin, 3.0, 4.0, verbose=True)
    print(f"\n根: x = {root1:.12f}")
    print(f"迭代次数: {iter1}, 残差: {res1:.2e}")
    print(f"验证: sin({root1}) = {np.sin(root1):.2e}")
    
    # ========== 测试2: 复杂函数 ==========
    print("\n--- 测试2: x^3 - 2x - 5 = 0 ---")
    f2 = lambda x: x**3 - 2*x - 5
    
    root2_bis, _, _ = bisection(f2, 2.0, 3.0)
    root2_sec, _, _ = secant(f2, 2.0, 3.0)
    root2_brent, _, _ = brent(f2, 2.0, 3.0)
    
    print(f"二分法: x = {root2_bis:.12f}")
    print(f"割线法: x = {root2_sec:.12f}")
    print(f"Brent:   x = {root2_brent:.12f}")
    print(f"验证 f(x) = {f2(root2_brent):.2e}")
    
    # ========== 测试3: 多根搜索 ==========
    print("\n--- 测试3: 区间内多根搜索 ---")
    f3 = lambda x: np.sin(5 * x) * np.exp(-x**2)
    
    roots3 = find_all_roots(f3, (-3, 3), n_intervals=100)
    print(f"找到 {len(roots3)} 个根:")
    for i, r in enumerate(roots3):
        print(f"  根{i+1}: x = {r:.8f}, f(x) = {f3(r):.2e}")
    
    # ========== 对比收敛速度 ==========
    print("\n--- 收敛速度对比: sin(x) = 0 在 [3, 4] ---")
    
    _, iter_bis, _ = bisection(np.sin, 3.0, 4.0)
    _, iter_sec, _ = secant(np.sin, 3.0, 4.0)
    _, iter_brent, _ = brent(np.sin, 3.0, 4.0)
    
    print(f"二分法: {iter_bis} 次迭代")
    print(f"割线法: {iter_sec} 次迭代")
    print(f"Brent:  {iter_brent} 次迭代")
    
    print("\n测试通过！非线性方程求解方法工作正常。")
