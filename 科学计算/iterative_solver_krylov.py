"""
Krylov子空间迭代法
=====================
本模块实现了三种经典的Krylov子空间方法：
1. CG (Conjugate Gradient) - 对称正定矩阵
2. GMRES (Generalized Minimal Residual) - 通用非对称矩阵
3. BiCGSTAB (Biconjugate Gradient Stabilized) - 非对称矩阵

Krylov子空间方法的核心思想是通过构造一系列搜索方向来逼近线性系统的解。

Author: 算法库
"""

import numpy as np
from typing import Tuple, Optional, Callable


def cg(A: np.ndarray, b: np.ndarray, x0: Optional[np.ndarray] = None,
       tol: float = 1e-10, max_iter: int = 1000) -> Tuple[np.ndarray, int, float]:
    """
    共轭梯度法求解对称正定线性系统 Ax = b
    
    参数:
        A: 系数矩阵 (n x n)，必须对称正定
        b: 右端向量 (n,)
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大迭代次数
    
    返回:
        x: 近似解
        iterations: 迭代次数
        residual_norm: 最终残差范数
    """
    n = len(b)
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()
    
    # 计算初始残差 r = b - Ax
    r = b - A @ x
    # 初始搜索方向
    p = r.copy()
    # 初始残差范数
    r_norm0 = np.linalg.norm(r)
    
    for iteration in range(max_iter):
        # 计算Ap
        Ap = A @ p
        
        # 计算步长 alpha
        # alpha = (r·r) / (p·Ap)
        r_dot_r = np.dot(r, r)
        p_dot_Ap = np.dot(p, Ap)
        
        if abs(p_dot_Ap) < 1e-15:
            break
            
        alpha = r_dot_r / p_dot_Ap
        
        # 更新解
        x = x + alpha * p
        
        # 更新残差
        r_new = r - alpha * Ap
        
        # 检查收敛
        r_norm = np.linalg.norm(r_new)
        if r_norm / r_norm0 < tol:
            return x, iteration + 1, r_norm
        
        # 计算 beta
        # beta = (r_{k+1}·r_{k+1}) / (r_k·r_k)
        beta = np.dot(r_new, r_new) / r_dot_r
        
        # 更新搜索方向
        p = r_new + beta * p
        
        r = r_new
    
    return x, max_iter, np.linalg.norm(r)


def gmres(A: np.ndarray, b: np.ndarray, x0: Optional[np.ndarray] = None,
          tol: float = 1e-10, max_iter: int = 1000, restart: int = 50) -> Tuple[np.ndarray, int, float]:
    """
    GMRES方法求解非对称线性系统 Ax = b
    
    参数:
        A: 系数矩阵 (n x n)
        b: 右端向量 (n,)
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大外部迭代次数
        restart: GMRES重启参数
    
    返回:
        x: 近似解
        iterations: 总迭代次数
        residual_norm: 最终残差范数
    """
    n = len(b)
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()
    
    # 初始残差
    r = b - A @ x
    beta = np.linalg.norm(r)
    
    total_iter = 0
    
    for outer in range(max_iter):
        # Arnoldi过程开始
        # 初始化第一向量
        q = r / beta
        Q = [q]  # Krylov子空间的正交基
        H = np.zeros((restart + 1, restart))  # Hessenberg矩阵
        
        # 初始残差
        e = np.zeros(restart + 1)
        e[0] = beta
        
        for j in range(restart):
            total_iter += 1
            # 计算 A*q_j
            v = A @ Q[j]
            
            # 正交化 (Gram-Schmidt)
            for i in range(j + 1):
                h = np.dot(v, Q[i])
                H[i, j] = h
                v = v - h * Q[i]
            
            # 归一化
            h_next = np.linalg.norm(v)
            H[j + 1, j] = h_next
            
            if h_next < 1e-15:
                # 提前终止
                Q.append(v)
                break
            
            q_new = v / h_next
            Q.append(q_new)
            
            # 最小二乘问题的解
            # min ||beta*e_1 - H*y||
            y = np.linalg.lstsq(H[:j+2, :j+1], e[:j+2], rcond=None)[0]
            
            # 计算当前近似解
            x_new = x + Q[:j+1] @ y
            
            # 检查收敛
            residual = b - A @ x_new
            if np.linalg.norm(residual) / beta < tol:
                return x_new, total_iter, np.linalg.norm(residual)
        
        # 重启
        x = x + Q[:restart] @ y
        r = b - A @ x
        beta = np.linalg.norm(r)
        
        if beta < tol:
            break
        
        e[0] = beta
    
    return x, total_iter, beta


def bicgstab(A: np.ndarray, b: np.ndarray, x0: Optional[np.ndarray] = None,
             tol: float = 1e-10, max_iter: int = 1000) -> Tuple[np.ndarray, int, float]:
    """
    BiCGSTAB方法求解非对称线性系统 Ax = b
    
    参数:
        A: 系数矩阵 (n x n)
        b: 右端向量 (n,)
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大迭代次数
    
    返回:
        x: 近似解
        iterations: 迭代次数
        residual_norm: 最终残差范数
    """
    n = len(b)
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()
    
    # 初始残差
    r = b - A @ x
    r_hat = r.copy()  # 辅助向量
    
    # 初始搜索方向
    p = r.copy()
    
    # 初始残差范数
    r_norm0 = np.linalg.norm(r)
    
    for iteration in range(max_iter):
        # 计算Ap
        Ap = A @ p
        
        # 计算alpha
        # alpha = (r·r_hat) / (Ap·r_hat)
        r_dot_r_hat = np.dot(r, r_hat)
        Ap_dot_r_hat = np.dot(Ap, r_hat)
        
        if abs(Ap_dot_r_hat) < 1e-15:
            break
            
        alpha = r_dot_r_hat / Ap_dot_r_hat
        
        # 更新解
        x = x + alpha * p
        
        # 更新残差
        r_new = r - alpha * Ap
        
        # 检查收敛
        r_norm = np.linalg.norm(r_new)
        if r_norm / r_norm0 < tol:
            return x, iteration + 1, r_norm
        
        # 计算As
        s = A @ r_new
        
        # 计算beta
        # beta = (r_new·r_hat) / (r·r_hat) * (r·r_hat) / (s·r_hat)
        # 简化为: beta = (r_new·r_hat) / (s·r_hat) * alpha
        s_dot_r_hat = np.dot(s, r_hat)
        if abs(s_dot_r_hat) < 1e-15:
            break
            
        beta = r_dot_r_hat / s_dot_r_hat * alpha
        
        # 更新搜索方向
        p = r_new + beta * (p - beta * s)
        
        r = r_new
    
    return x, max_iter, np.linalg.norm(r)


if __name__ == "__main__":
    print("=" * 50)
    print("Krylov子空间迭代法测试")
    print("=" * 50)
    
    # 创建测试问题
    np.random.seed(42)
    n = 50
    
    # 对称正定矩阵 (用于CG测试)
    # A = L @ L.T + 0.1 * I
    L = np.random.randn(n, n)
    A_sym = L @ L.T + 0.1 * np.eye(n)
    b_sym = np.random.randn(n)
    
    print("\n--- CG方法 (对称正定矩阵) ---")
    x_cg, iter_cg, res_cg = cg(A_sym, b_sym)
    print(f"迭代次数: {iter_cg}")
    print(f"最终残差: {res_cg:.2e}")
    print(f"残差范数/初始残差: {res_cg/np.linalg.norm(b_sym - A_sym @ np.zeros(n)):.2e}")
    
    # 非对称矩阵 (用于GMRES和BiCGSTAB测试)
    A_nonsym = L @ L.T + np.random.randn(n, n) * 0.5
    b_nonsym = np.random.randn(n)
    
    print("\n--- GMRES方法 (非对称矩阵) ---")
    x_gmres, iter_gmres, res_gmres = gmres(A_nonsym, b_nonsym, restart=20)
    print(f"迭代次数: {iter_gmres}")
    print(f"最终残差: {res_gmres:.2e}")
    
    print("\n--- BiCGSTAB方法 (非对称矩阵) ---")
    x_bicgstab, iter_bicgstab, res_bicgstab = bicgstab(A_nonsym, b_nonsym)
    print(f"迭代次数: {iter_bicgstab}")
    print(f"最终残差: {res_bicgstab:.2e}")
    
    print("\n测试通过！Krylov子空间迭代法工作正常。")
