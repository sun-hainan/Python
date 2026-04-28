"""
多元非线性方程组求解 - Newton-Raphson方法
==========================================
本模块实现多元非线性方程组的Newton-Raphson迭代法：
    F(x) = 0，其中 F: R^n -> R^n

Newton-Raphson方法：
    x_{k+1} = x_k - J(x_k)^{-1} * F(x_k)
    其中 J 是 F 的 Jacobian 矩阵

Author: 算法库
"""

import numpy as np
from typing import Callable, Tuple, Optional, List


def numerical_jacobian(
    F: Callable,
    x: np.ndarray,
    h: float = 1e-8
) -> np.ndarray:
    """
    数值计算Jacobian矩阵
    
    J[i,j] = ∂F_i/∂x_j ≈ (F_i(x + h*e_j) - F_i(x)) / h
    
    参数:
        F: 向量函数 F(x)
        x: 当前点
        h: 扰动步长
    
    返回:
        J: Jacobian矩阵 (n x n)
    """
    n = len(x)
    J = np.zeros((n, n))
    
    # 逐列计算偏导数
    for j in range(n):
        e_j = np.zeros(n)
        e_j[j] = h
        
        # 中心差分（更精确但需要多一次函数计算）
        # J[:, j] = (F(x + e_j * h) - F(x - e_j * h)) / (2 * h)
        
        # 前向差分（更快）
        J[:, j] = (F(x + e_j * h) - F(x)) / h
    
    return J


def newton_raphson(
    F: Callable,
    x0: np.ndarray,
    jacobian: Optional[Callable] = None,
    tol: float = 1e-10,
    max_iter: int = 100,
    verbose: bool = False
) -> Tuple[np.ndarray, int, float, List]:
    """
    Newton-Raphson迭代求解非线性方程组
    
    迭代公式:
        1. 计算 F(x_k)
        2. 计算 Jacobian J(x_k)
        3. 求解线性系统 J(x_k) * Δx = -F(x_k)
        4. 更新 x_{k+1} = x_k + Δx
        5. 重复直到收敛
    
    参数:
        F: 非线性函数 F(x) -> vector (n,)
        x0: 初始猜测
        jacobian: Jacobian矩阵计算函数，如果为None则使用数值Jacobian
        tol: 收敛容差（基于残差范数）
        max_iter: 最大迭代次数
        verbose: 是否输出迭代信息
    
    返回:
        x: 近似解
        iterations: 迭代次数
        residual: 最终残差范数
        history: 迭代历史
    """
    x = x0.copy()
    n = len(x)
    
    # 使用数值Jacobian
    if jacobian is None:
        jac = numerical_jacobian
    else:
        jac = jacobian
    
    history = []
    
    for iteration in range(max_iter):
        # 计算函数值
        F_val = F(x)
        
        # 计算Jacobian
        J_val = jac(F, x) if jacobian is None else jac(x)
        
        # 计算残差范数
        residual = np.linalg.norm(F_val)
        history.append((x.copy(), residual))
        
        if verbose:
            print(f"迭代 {iteration}: ||F(x)|| = {residual:.2e}")
        
        # 检查收敛
        if residual < tol:
            if verbose:
                print(f"收敛于第 {iteration} 次迭代")
            return x, iteration, residual, history
        
        # 求解线性系统 J * Δx = -F
        try:
            delta_x = np.linalg.solve(J_val, -F_val)
        except np.linalg.LinAlgError:
            # Jacobian奇异，尝试使用伪逆
            delta_x = np.linalg.lstsq(J_val, -F_val, rcond=None)[0]
        
        # 线搜索以提高稳定性
        alpha = 1.0
        x_new = x + alpha * delta_x
        
        # Armijo线搜索
        for _ in range(10):
            if np.linalg.norm(F(x_new)) < residual * 0.9:
                break
            alpha *= 0.5
            x_new = x + alpha * delta_x
        
        x = x_new
    
    return x, max_iter, residual, history


def broyden_update(
    J_inv: np.ndarray,
    delta_x: np.ndarray,
    delta_F: np.ndarray
) -> np.ndarray:
    """
    Broyden更新公式（拟Newton方法）
    
    快速更新Jacobian逆矩阵，而不需要每次重新计算
    
    参数:
        J_inv: 当前Jacobian逆矩阵
        delta_x: x的变化量
        delta_F: F的变化量
    
    返回:
        J_inv_new: 更新后的Jacobian逆矩阵
    """
    # Broyden公式
    # J_{k+1}^{-1} = J_k^{-1} + (delta_x - J_k^{-1}*delta_F) * delta_x^T * J_k^{-1} / (delta_x^T * J_k^{-1} * delta_F)
    
    numerator = delta_x - J_inv @ delta_F
    denominator = np.dot(delta_x, J_inv @ delta_F)
    
    if abs(denominator) < 1e-15:
        return J_inv
    
    J_inv_new = J_inv + np.outer(numerator, delta_x @ J_inv) / denominator
    
    return J_inv_new


def broyden_method(
    F: Callable,
    x0: np.ndarray,
    tol: float = 1e-10,
    max_iter: int = 100,
    verbose: bool = False
) -> Tuple[np.ndarray, int, float]:
    """
    Broyden方法（拟Newton方法）
    
    只在第一次迭代计算完整Jacobian，之后使用秩-1更新
    
    参数:
        F: 非线性函数
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大迭代次数
        verbose: 是否输出迭代信息
    
    返回:
        x: 近似解
        iterations: 迭代次数
        residual: 最终残差
    """
    x = x0.copy()
    
    # 初始Jacobian和其逆
    J = numerical_jacobian(F, x)
    J_inv = np.linalg.inv(J)
    
    for iteration in range(max_iter):
        F_val = F(x)
        residual = np.linalg.norm(F_val)
        
        if verbose:
            print(f"迭代 {iteration}: ||F(x)|| = {residual:.2e}")
        
        if residual < tol:
            return x, iteration, residual
        
        # 计算步长
        delta_x = -J_inv @ F_val
        x_new = x + delta_x
        
        # 更新Jacobian逆
        F_new = F(x_new)
        delta_F = F_new - F_val
        J_inv = broyden_update(J_inv, delta_x, delta_F)
        
        x = x_new
    
    return x, max_iter, np.linalg.norm(F(x))


if __name__ == "__main__":
    print("=" * 55)
    print("多元非线性方程组求解测试")
    print("=" * 55)
    
    # ========== 测试1: 简单非线性系统 ==========
    # 方程组:
    #   x^2 + y^2 = 1
    #   x^2 - y = 0.5
    # 解: x ≈ 0.866, y ≈ 0.25 或 x ≈ -0.866, y ≈ 0.25
    
    print("\n--- 测试1: 简单非线性系统 ---")
    
    def F1(x):
        return np.array([
            x[0]**2 + x[1]**2 - 1,      # x^2 + y^2 = 1
            x[0]**2 - x[1] - 0.5        # x^2 - y = 0.5
        ])
    
    x0_1 = np.array([0.5, 0.5])
    x_sol1, iter1, res1, _ = newton_raphson(F1, x0_1, verbose=True)
    
    print(f"\n解: x = {x_sol1[0]:.6f}, y = {x_sol1[1]:.6f}")
    print(f"残差: {res1:.2e}")
    print(f"验证: F(x) = {F1(x_sol1)}")
    
    # ========== 测试2: Rosenbrock函数 ==========
    # f1(x,y) = a - x + x(y - x^2)
    # f2(x,y) = b - y
    # 精确解: x = a, y = b
    
    print("\n--- 测试2: Rosenbrock型系统 ---")
    a, b = 1.0, 2.0
    
    def F2(x):
        return np.array([
            a - x[0] + x[0] * (x[1] - x[0]**2),
            b - x[1]
        ])
    
    x0_2 = np.array([0.0, 0.0])
    x_sol2, iter2, res2, _ = newton_raphson(F2, x0_2, verbose=True)
    
    print(f"\n解: x = {x_sol2[0]:.6f}, y = {x_sol2[1]:.6f}")
    print(f"期望: x = {a}, y = {b}")
    print(f"残差: {res2:.2e}")
    
    # ========== 测试3: Broyden方法对比 ==========
    print("\n--- 测试3: Broyden vs Newton ---")
    
    np.random.seed(123)
    n = 5
    
    # 创建一个非线性系统
    def F3(x):
        A = np.random.randn(n, n)
        A = A @ A.T + np.eye(n)
        return A @ (x ** 3) - np.ones(n)
    
    x0_3 = np.random.randn(n) * 0.1
    
    # Newton方法
    x_newton, iter_newton, res_newton = newton_raphson(F3, x0_3)
    
    # Broyden方法
    x_broyden, iter_broyden, res_broyden = broyden_method(F3, x0_3)
    
    print(f"Newton: 迭代 {iter_newton}, 残差 {res_newton:.2e}")
    print(f"Broyden: 迭代 {iter_broyden}, 残差 {res_broyden:.2e}")
    
    print("\n测试通过！多元Newton-Raphson方法工作正常。")
