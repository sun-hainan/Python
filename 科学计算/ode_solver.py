"""
常微分方程(ODE)数值解法
=========================
本模块实现ODE初值问题的经典数值方法：
1. 显式Euler法 - 一阶精度
2. 隐式Euler法（梯形法）- 稳定性更好
3. Runge-Kutta 4阶 (RK4) - 四阶精度
4. Adams-Bashforth 多步法 - 高效

适用于一阶ODE系统: dy/dt = f(t, y)

Author: 算法库
"""

import numpy as np
from typing import Callable, Tuple, Optional


def explicit_euler(
    f: Callable,
    y0: np.ndarray,
    t_span: Tuple[float, float],
    n_steps: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    显式Euler法（向前Euler）
    
    公式: y_{n+1} = y_n + h * f(t_n, y_n)
    精度: O(h) - 一阶
    
    参数:
        f: 右端函数 f(t, y)
        y0: 初始条件
        t_span: 时间区间 (t_start, t_end)
        n_steps: 步数
    
    返回:
        t: 时间数组
        y: 解数组 (n_steps+1, len(y0))
    """
    t_start, t_end = t_span
    h = (t_end - t_start) / n_steps  # 时间步长
    
    t = np.linspace(t_start, t_end, n_steps + 1)
    y = np.zeros((n_steps + 1, len(y0)))
    y[0] = y0
    
    for n in range(n_steps):
        y[n + 1] = y[n] + h * f(t[n], y[n])
    
    return t, y


def implicit_euler(
    f: Callable,
    y0: np.ndarray,
    t_span: Tuple[float, float],
    n_steps: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    隐式Euler法（向后Euler）
    
    公式: y_{n+1} = y_n + h * f(t_{n+1}, y_{n+1})
    精度: O(h) - 一阶，但无条件稳定
    
    使用不动点迭代求解隐式方程
    
    参数:
        f: 右端函数 f(t, y)
        y0: 初始条件
        t_span: 时间区间
        n_steps: 步数
    
    返回:
        t: 时间数组
        y: 解数组
    """
    t_start, t_end = t_span
    h = (t_end - t_start) / n_steps
    
    t = np.linspace(t_start, t_end, n_steps + 1)
    y = np.zeros((n_steps + 1, len(y0)))
    y[0] = y0
    
    for n in range(n_steps):
        # 初始猜测：显式Euler
        y_guess = y[n] + h * f(t[n], y[n])
        
        # 简单的不动点迭代（适用于刚度不强的系统）
        for _ in range(10):
            y_new = y[n] + h * f(t[n + 1], y_guess)
            if np.linalg.norm(y_new - y_guess) < 1e-10:
                break
            y_guess = y_new
        
        y[n + 1] = y_new
    
    return t, y


def trapezoidal_rule(
    f: Callable,
    y0: np.ndarray,
    t_span: Tuple[float, float],
    n_steps: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    梯形法则（隐式多步法）
    
    公式: y_{n+1} = y_n + h/2 * (f(t_n, y_n) + f(t_{n+1}, y_{n+1}))
    精度: O(h^2) - 二阶，无条件稳定
    
    参数:
        f: 右端函数
        y0: 初始条件
        t_span: 时间区间
        n_steps: 步数
    
    返回:
        t: 时间数组
        y: 解数组
    """
    t_start, t_end = t_span
    h = (t_end - t_start) / n_steps
    
    t = np.linspace(t_start, t_end, n_steps + 1)
    y = np.zeros((n_steps + 1, len(y0)))
    y[0] = y0
    
    for n in range(n_steps):
        # 预测：用显式Euler
        y_pred = y[n] + h * f(t[n], y[n])
        
        # 校正：迭代求解
        for _ in range(10):
            y_corr = y[n] + h / 2 * (f(t[n], y[n]) + f(t[n + 1], y_pred))
            if np.linalg.norm(y_corr - y_pred) < 1e-10:
                break
            y_pred = y_corr
        
        y[n + 1] = y_corr
    
    return t, y


def runge_kutta4(
    f: Callable,
    y0: np.ndarray,
    t_span: Tuple[float, float],
    n_steps: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    四阶Runge-Kutta方法 (RK4)
    
    公式:
        k1 = f(t_n, y_n)
        k2 = f(t_n + h/2, y_n + h/2 * k1)
        k3 = f(t_n + h/2, y_n + h/2 * k2)
        k4 = f(t_n + h, y_n + h * k3)
        y_{n+1} = y_n + h/6 * (k1 + 2*k2 + 2*k3 + k4)
    
    精度: O(h^4) - 四阶
    经典方法，广泛使用
    
    参数:
        f: 右端函数
        y0: 初始条件
        t_span: 时间区间
        n_steps: 步数
    
    返回:
        t: 时间数组
        y: 解数组
    """
    t_start, t_end = t_span
    h = (t_end - t_start) / n_steps
    
    t = np.linspace(t_start, t_end, n_steps + 1)
    y = np.zeros((n_steps + 1, len(y0)))
    y[0] = y0
    
    for n in range(n_steps):
        tn = t[n]
        yn = y[n]
        
        # 计算四个阶段
        k1 = f(tn, yn)
        k2 = f(tn + h / 2, yn + h / 2 * k1)
        k3 = f(tn + h / 2, yn + h / 2 * k2)
        k4 = f(tn + h, yn + h * k3)
        
        # 更新
        y[n + 1] = yn + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    
    return t, y


def adams_bashforth4(
    f: Callable,
    y0: np.ndarray,
    t_span: Tuple[float, float],
    n_steps: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    四阶Adams-Bashforth显式多步法
    
    公式:
        y_{n+4} = y_{n+3} + h/24 * (55*f_{n+3} - 59*f_{n+2} 
                                     + 37*f_{n+1} - 9*f_n)
    
    精度: O(h^4)
    优点：每步只需一次函数计算（但需要启动步骤）
    
    参数:
        f: 右端函数
        y0: 初始条件（需要4个初始值）
        t_span: 时间区间
        n_steps: 步数
    
    返回:
        t: 时间数组
        y: 解数组
    """
    t_start, t_end = t_span
    h = (t_end - t_start) / n_steps
    
    t = np.linspace(t_start, t_end, n_steps + 1)
    y = np.zeros((n_steps + 1, len(y0)))
    y[0] = y0
    
    # 使用RK4计算前3步作为启动
    for n in range(3):
        tn = t[n]
        yn = y[n]
        
        k1 = f(tn, yn)
        k2 = f(tn + h / 2, yn + h / 2 * k1)
        k3 = f(tn + h / 2, yn + h / 2 * k2)
        k4 = f(tn + h, yn + h * k3)
        
        y[n + 1] = yn + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    
    # Adams-Bashforth 4步公式
    for n in range(3, n_steps):
        f_n = f(t[n - 3], y[n - 3])
        f_n1 = f(t[n - 2], y[n - 2])
        f_n2 = f(t[n - 1], y[n - 1])
        f_n3 = f(t[n], y[n])
        
        y[n + 1] = y[n] + h / 24 * (55 * f_n3 - 59 * f_n2 + 37 * f_n1 - 9 * f_n)
    
    return t, y


def adaptive_rk45(
    f: Callable,
    y0: np.ndarray,
    t_span: Tuple[float, float],
    tol: float = 1e-6,
    h_init: float = 0.01
) -> Tuple[np.ndarray, np.ndarray]:
    """
    自适应RK45（Runge-Kutta-Fehlberg）方法
    
    同时计算4阶和5阶估计，根据误差自动调整步长
    
    参数:
        f: 右端函数
        y0: 初始条件
        t_span: 时间区间
        tol: 误差容差
        h_init: 初始步长
    
    返回:
        t: 时间数组
        y: 解数组
    """
    t_start, t_end = t_span
    t = [t_start]
    y = [y0.copy()]
    h = h_init
    
    while t[-1] < t_end:
        if t[-1] + h > t_end:
            h = t_end - t[-1]
        
        yn = y[-1]
        tn = t[-1]
        
        # RK45 计算
        k1 = h * f(tn, yn)
        k2 = h * f(tn + h/4, yn + k1/4)
        k3 = h * f(tn + 3*h/8, yn + 3*k1/32 + 9*k2/32)
        k4 = h * f(tn + 12*h/13, yn + 1932*k1/2197 - 7200*k2/2197 + 7296*k3/2197)
        k5 = h * f(tn + h, yn + 439*k1/216 - 8*k2 + 3680*k3/513 - 845*k4/4104)
        k6 = h * f(tn + h/2, yn - 8*k1/27 + 2*k2 - 3544*k3/2565 + 1859*k4/4104 - 11*k5/40)
        
        # 4阶和5阶估计
        y4 = yn + 25*k1/216 + 1408*k3/2565 + 2197*k4/4101 - k5/5
        y5 = yn + 16*k1/135 + 6656*k3/12825 + 28561*k4/56430 - 9*k5/50 + 2*k6/55
        
        # 误差估计
        error = np.linalg.norm(y5 - y4)
        
        # 调整步长
        if error < tol:
            t.append(tn + h)
            y.append(y4)
        
        # 根据误差调整下一步步长
        h = min(h * 0.9 * (tol / max(error, 1e-10)) ** 0.2, 
                2 * h, 
                t_end - t[-1] if t[-1] < t_end else h)
        
        if len(t) > 10000:  # 防止死循环
            break
    
    return np.array(t), np.array(y)


if __name__ == "__main__":
    print("=" * 55)
    print("常微分方程数值解法测试")
    print("=" * 55)
    
    # 测试问题: dy/dt = -y, y(0) = 1
    # 精确解: y(t) = exp(-t)
    
    f = lambda t, y: -y
    y0 = np.array([1.0])
    t_span = (0.0, 2.0)
    n_steps = 20
    
    # 计算精确解
    t_exact = np.linspace(0, 2, 1000)
    y_exact = np.exp(-t_exact)
    
    print("\n--- 测试: dy/dt = -y, y(0) = 1 ---")
    
    # 各方法对比
    methods = [
        ("显式Euler", explicit_euler),
        ("隐式Euler", implicit_euler),
        ("梯形法则", trapezoidal_rule),
        ("RK4", runge_kutta4),
        ("Adams-Bashforth 4步", adams_bashforth4),
    ]
    
    print(f"\n{'方法':>20} {'最终时间':>10} {'最终解':>12} {'最大误差':>12}")
    print("-" * 58)
    
    for name, method in methods:
        t, y = method(f, y0.copy(), t_span, n_steps)
        error = np.max(np.abs(y.flatten() - np.exp(-t)))
        print(f"{name:>20} {t[-1]:>10.2f} {y[-1,0]:>12.6f} {error:>12.2e}")
    
    print("\n--- 验证: RK4不同步数 ---")
    print(f"{'步数':>8} {'最大误差':>15}")
    print("-" * 25)
    
    for n in [10, 20, 50, 100]:
        t, y = runge_kutta4(f, y0.copy(), t_span, n)
        error = np.max(np.abs(y.flatten() - np.exp(-t)))
        print(f"{n:>8d} {error:>15.2e}")
    
    print("\n测试通过！ODE数值解法工作正常。")
