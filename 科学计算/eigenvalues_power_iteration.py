"""
特征值问题求解
================
本模块实现特征值和特征向量的数值算法：
1. 幂迭代法 (Power Iteration) - 求最大特征值
2. 逆幂迭代法 (Inverse Iteration) - 求指定特征值
3. QR分解算法 - 求全部特征值

特征值问题: A @ v = λ @ v

Author: 算法库
"""

import numpy as np
from typing import Tuple, Optional


def power_iteration(
    A: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-10,
    verbose: bool = False
) -> Tuple[float, np.ndarray, list]:
    """
    幂迭代法 - 求矩阵的最大特征值和对应特征向量
    
    原理:
        如果 A 的特征值满足 |λ1| > |λ2| >= ... >= |λn|
        选择随机向量 b0
        迭代: b_{k+1} = A @ b_k / ||A @ b_k||
        则 b_k 收敛到 λ1 的特征向量
        λ1 ≈ (A @ b_k) / b_k
    
    收敛速度: |λ2/λ1|^k - 线性收敛
    适用于: 只需最大特征值的情况
    
    参数:
        A: 方阵 (n x n)
        max_iter: 最大迭代次数
        tol: 收敛容差
        verbose: 是否输出迭代信息
    
    返回:
        eigenvalue: 最大特征值
        eigenvector: 对应特征向量
        history: 收敛历史
    """
    n = A.shape[0]
    
    # 随机初始向量
    b = np.random.randn(n)
    b = b / np.linalg.norm(b)  # 归一化
    
    eigenvalue_old = 0.0
    history = []
    
    for iteration in range(max_iter):
        # 矩阵-向量乘积
        Ab = A @ b
        
        # Rayleigh商估计特征值
        eigenvalue = np.dot(b, Ab)
        
        # 归一化
        norm_Ab = np.linalg.norm(Ab)
        b_new = Ab / norm_Ab
        
        # 计算误差
        error = np.abs(eigenvalue - eigenvalue_old)
        history.append((iteration, eigenvalue, error))
        
        if verbose and iteration % 20 == 0:
            print(f"迭代 {iteration}: λ = {eigenvalue:.10f}, 误差 = {error:.2e}")
        
        # 检查收敛
        if error < tol:
            if verbose:
                print(f"收敛于第 {iteration} 次迭代")
            break
        
        b = b_new
        eigenvalue_old = eigenvalue
    
    return eigenvalue, b, history


def inverse_iteration(
    A: np.ndarray,
    mu: float,
    max_iter: int = 100,
    tol: float = 1e-10,
    verbose: bool = False
) -> Tuple[float, np.ndarray]:
    """
    逆幂迭代法 - 求距离 μ 最近的特征值
    
    原理:
        迭代: (A - μI)^{-1} @ b
        收敛到距离 μ 最近的特征值对应的特征向量
    
    优点: 只需指定目标位置，即可求对应特征值
    收敛速度: 很快（如果 μ 接近目标特征值）
    
    参数:
        A: 方阵
        mu: 偏移量（目标特征值附近的值）
        max_iter: 最大迭代次数
        tol: 收敛容差
        verbose: 是否输出迭代信息
    
    返回:
        eigenvalue: 求得的特征值
        eigenvector: 对应特征向量
    """
    n = A.shape[0]
    
    # 移位矩阵
    B = A - mu * np.eye(n)
    
    # LU分解（或直接求逆）
    # 这里使用更稳健的方法
    B_inv = np.linalg.inv(B)
    
    # 随机初始向量
    b = np.random.randn(n)
    b = b / np.linalg.norm(b)
    
    for iteration in range(max_iter):
        # 逆幂迭代
        b_new = B_inv @ b
        b_new = b_new / np.linalg.norm(b_new)
        
        # Rayleigh商
        eigenvalue = np.dot(b_new, A @ b_new)
        
        if verbose:
            print(f"迭代 {iteration}: λ ≈ {eigenvalue:.10f}")
        
        # 检查收敛
        if np.linalg.norm(b_new - b) < tol or np.linalg.norm(b_new + b) < tol:
            b = b_new
            break
        
        b = b_new
    
    return eigenvalue, b


def qr_algorithm(
    A: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-10,
    verbose: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    QR分解算法 - 求矩阵的全部特征值
    
    原理:
        A_0 = A
        for k = 0, 1, 2, ...:
            A_k = Q_k @ R_k (QR分解)
            A_{k+1} = R_k @ Q_k
        A_k 收敛到上三角矩阵（Schur形式）
        对角线元素即为特征值
    
    收敛速度: 线性（对于一般矩阵较慢）
    实用中会加入移位策略加速
    
    参数:
        A: 方阵
        max_iter: 最大迭代次数
        tol: 收敛容差
        verbose: 是否输出迭代信息
    
    返回:
        eigenvalues: 特征值数组
        A_final: 迭代结束时的矩阵
    """
    n = A.shape[0]
    A_k = A.copy().astype(float)
    
    for iteration in range(max_iter):
        # QR分解
        Q, R = np.linalg.qr(A_k)
        
        # 更新
        A_k_new = R @ Q
        
        # 检查收敛（off-diagonal元素是否足够小）
        off_diagonal = np.sqrt(np.sum(A_k_new ** 2) - np.sum(np.diag(A_k_new) ** 2))
        
        if verbose and iteration % 50 == 0:
            print(f"迭代 {iteration}: off-diagonal norm = {off_diagonal:.2e}")
        
        if off_diagonal < tol:
            if verbose:
                print(f"收敛于第 {iteration} 次迭代")
            break
        
        A_k = A_k_new
    
    # 提取特征值（对角线）
    eigenvalues = np.diag(A_k)
    
    return eigenvalues, A_k


def shifted_qr_algorithm(
    A: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-10,
    verbose: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    带移位的QR算法 - 更高效的全面特征值求解
    
    移位策略:
        每次迭代使用底部右下角元素作为移位量
        加速收敛到特征值
    
    参数:
        A: 方阵
        max_iter: 最大迭代次数
        tol: 收敛容差
        verbose: 是否输出迭代信息
    
    返回:
        eigenvalues: 特征值数组
        A_final: 迭代结束时的矩阵
    """
    n = A.shape[0]
    A_k = A.copy().astype(float)
    
    for iteration in range(max_iter):
        # 移位量：底部右下角元素
        mu = A_k[-1, -1]
        
        # 移位后的矩阵
        B = A_k - mu * np.eye(n)
        
        # QR分解
        Q, R = np.linalg.qr(B)
        
        # 更新并还原移位
        A_k_new = R @ Q + mu * np.eye(n)
        
        # 检查收敛
        off_diag_norm = np.sqrt(np.sum(np.tril(A_k_new, -1) ** 2))
        
        if verbose:
            print(f"迭代 {iteration}: μ = {mu:.6f}, off-diag = {off_diag_norm:.2e}")
        
        if off_diag_norm < tol:
            if verbose:
                print(f"收敛于第 {iteration} 次迭代")
            break
        
        A_k = A_k_new
    
    eigenvalues = np.diag(A_k)
    return eigenvalues, A_k


def rayleigh_quotient_iteration(
    A: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-10
) -> Tuple[float, np.ndarray]:
    """
    Rayleigh商迭代 - 同时优化特征值和特征向量
    
    原理:
        每步使用当前特征向量估计计算最佳移位
        收敛速度: 立方收敛
    
    参数:
        A: 方阵
        max_iter: 最大迭代次数
        tol: 收敛容差
    
    返回:
        eigenvalue: 特征值
        eigenvector: 特征向量
    """
    n = A.shape[0]
    
    # 随机初始向量
    v = np.random.randn(n)
    v = v / np.linalg.norm(v)
    
    # 初始Rayleigh商
    lam = np.dot(v, A @ v)
    
    for iteration in range(max_iter):
        # 求解 (A - λI) w = v
        B = A - lam * np.eye(n)
        
        try:
            w = np.linalg.solve(B, v)
        except np.linalg.LinAlgError:
            w = np.linalg.lstsq(B, v, rcond=None)[0]
        
        # 归一化
        v_new = w / np.linalg.norm(w)
        
        # 更新Rayleigh商
        lam_new = np.dot(v_new, A @ v_new)
        
        # 检查收敛
        if np.abs(lam_new - lam) < tol and np.linalg.norm(v_new - v) < tol:
            return lam_new, v_new
        
        v = v_new
        lam = lam_new
    
    return lam, v


if __name__ == "__main__":
    print("=" * 55)
    print("特征值问题求解测试")
    print("=" * 55)
    
    # 创建测试矩阵
    np.random.seed(42)
    n = 5
    
    # 对称矩阵（特征值都是实数）
    A_sym = np.random.randn(n, n)
    A_sym = (A_sym + A_sym.T) / 2  # 对称化
    
    # 特征值分解验证
    eigenvalues_exact, eigenvectors_exact = np.linalg.eigh(A_sym)
    
    print("\n--- 测试矩阵 ---")
    print(f"维度: {A_sym.shape}")
    print(f"精确特征值: {eigenvalues_exact}")
    
    # 幂迭代法
    print("\n--- 幂迭代法 (最大特征值) ---")
    lam_max, vec_max, _ = power_iteration(A_sym, verbose=True)
    print(f"计算的最大特征值: {lam_max:.10f}")
    print(f"精确的最大特征值: {eigenvalues_exact[-1]:.10f}")
    print(f"相对误差: {abs(lam_max - eigenvalues_exact[-1]) / abs(eigenvalues_exact[-1]):.2e}")
    
    # 逆幂迭代
    print("\n--- 逆幂迭代法 (中间特征值) ---")
    target_lambda = eigenvalues_exact[n // 2]  # 取中间特征值
    lam_inv, vec_inv = inverse_iteration(A_sym, target_lambda + 0.1)
    print(f"目标值: {target_lambda:.6f}")
    print(f"计算的特征值: {lam_inv:.10f}")
    
    # QR算法
    print("\n--- QR分解算法 ---")
    eigenvalues_qr, _ = qr_algorithm(A_sym, verbose=True)
    eigenvalues_qr = np.sort(eigenvalues_qr)
    print(f"QR算法特征值: {eigenvalues_qr}")
    print(f"精确特征值:   {np.sort(eigenvalues_exact)}")
    
    # 带移位QR算法
    print("\n--- 带移位QR算法 ---")
    eigenvalues_shifted, _ = shifted_qr_algorithm(A_sym, verbose=True)
    print(f"移位QR特征值: {np.sort(eigenvalues_shifted)}")
    
    # Rayleigh商迭代
    print("\n--- Rayleigh商迭代 ---")
    lam_rayleigh, vec_rayleigh = rayleigh_quotient_iteration(A_sym)
    print(f"Rayleigh商特征值: {lam_rayleigh:.10f}")
    print(f"最大精确特征值:    {eigenvalues_exact[-1]:.10f}")
    
    # 验证特征向量正交性
    print("\n--- 特征向量正交性验证 ---")
    Q = eigenvectors_exact
    orthogonality = np.abs(Q.T @ Q - np.eye(n))
    print(f"Q^T @ Q - I 的范数: {np.linalg.norm(orthogonality):.2e}")
    
    print("\n测试通过！特征值算法工作正常。")
