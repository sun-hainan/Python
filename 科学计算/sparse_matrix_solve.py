"""
稀疏线性系统求解器
====================
本模块实现稀疏线性系统的迭代求解方法：
1. Conjugate Gradient (CG) - 对称正定
2. BiCGSTAB - 通用非对称矩阵
3. GMRES - 最小残差法

与稠密求解器相比，稀疏求解器利用矩阵的稀疏性大幅降低计算复杂度。

Author: 算法库
"""

import numpy as np
from typing import Tuple, Optional
from sparse_matrix_csr import CSRMatrix


def csr_matvec(A: CSRMatrix, x: np.ndarray) -> np.ndarray:
    """
    稀疏矩阵-向量乘积
    
    参数:
        A: CSR格式矩阵
        x: 输入向量
    
    返回:
        y: 输出向量
    """
    return A.matvec(x)


def csr_matvec_t(A: CSRMatrix, x: np.ndarray) -> np.ndarray:
    """
    稀疏矩阵转置-向量乘积
    
    参数:
        A: CSR格式矩阵
        x: 输入向量
    
    返回:
        y: 输出向量
    """
    return A.matvec_transpose(x)


def sparse_cg(
    A: CSRMatrix,
    b: np.ndarray,
    x0: Optional[np.ndarray] = None,
    tol: float = 1e-10,
    max_iter: Optional[int] = None
) -> Tuple[np.ndarray, int, float]:
    """
    稀疏矩阵共轭梯度法
    
    参数:
        A: 对称正定稀疏矩阵
        b: 右端向量
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大迭代次数
    
    返回:
        x: 解向量
        iterations: 迭代次数
        residual_norm: 最终残差范数
    """
    n = len(b)
    if max_iter is None:
        max_iter = n
    
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()
    
    # 初始残差
    r = b - csr_matvec(A, x)
    p = r.copy()
    
    r_norm0 = np.linalg.norm(r)
    
    for iteration in range(max_iter):
        # Ap
        Ap = csr_matvec(A, p)
        
        # 步长
        r_dot_r = np.dot(r, r)
        p_dot_Ap = np.dot(p, Ap)
        
        if abs(p_dot_Ap) < 1e-15:
            break
        
        alpha = r_dot_r / p_dot_Ap
        
        # 更新
        x = x + alpha * p
        r_new = r - alpha * Ap
        
        # 检查收敛
        r_norm = np.linalg.norm(r_new)
        if r_norm / r_norm0 < tol:
            return x, iteration + 1, r_norm
        
        # beta
        beta = np.dot(r_new, r_new) / r_dot_r
        p = r_new + beta * p
        
        r = r_new
    
    return x, max_iter, np.linalg.norm(r)


def sparse_bicgstab(
    A: CSRMatrix,
    b: np.ndarray,
    x0: Optional[np.ndarray] = None,
    tol: float = 1e-10,
    max_iter: Optional[int] = None
) -> Tuple[np.ndarray, int, float]:
    """
    稀疏矩阵BiCGSTAB方法
    
    参数:
        A: 非对称稀疏矩阵
        b: 右端向量
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大迭代次数
    
    返回:
        x: 解向量
        iterations: 迭代次数
        residual_norm: 最终残差范数
    """
    n = len(b)
    if max_iter is None:
        max_iter = n
    
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()
    
    r = b - csr_matvec(A, x)
    r_hat = r.copy()
    p = r.copy()
    
    r_norm0 = np.linalg.norm(r)
    
    for iteration in range(max_iter):
        Ap = csr_matvec(A, p)
        
        r_dot_r_hat = np.dot(r, r_hat)
        Ap_dot_r_hat = np.dot(Ap, r_hat)
        
        if abs(Ap_dot_r_hat) < 1e-15:
            break
        
        alpha = r_dot_r_hat / Ap_dot_r_hat
        
        s = r - alpha * Ap
        
        As = csr_matvec(A, s)
        
        s_dot_s = np.dot(s, s)
        s_dot_As = np.dot(s, As)
        
        if abs(s_dot_As) < 1e-15:
            x = x + alpha * p
            r = s
            break
        
        omega = s_dot_As / s_dot_As
        
        x_new = x + alpha * p + omega * s
        r_new = s - omega * As
        
        r_norm = np.linalg.norm(r_new)
        if r_norm / r_norm0 < tol:
            return x_new, iteration + 1, r_norm
        
        beta = (np.dot(r_new, r_hat) / r_dot_r_hat) * alpha / omega
        
        p = r_new + beta * (p - omega * Ap)
        
        x = x_new
        r = r_new
    
    return x, max_iter, np.linalg.norm(r)


def sparse_gmres(
    A: CSRMatrix,
    b: np.ndarray,
    x0: Optional[np.ndarray] = None,
    tol: float = 1e-10,
    max_iter: int = 100,
    restart: int = 20
) -> Tuple[np.ndarray, int, float]:
    """
    稀疏矩阵GMRES方法
    
    参数:
        A: 非对称稀疏矩阵
        b: 右端向量
        x0: 初始猜测
        tol: 收敛容差
        max_iter: 最大外部迭代次数
        restart: 重启参数
    
    返回:
        x: 解向量
        iterations: 总迭代次数
        residual_norm: 最终残差范数
    """
    n = len(b)
    
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()
    
    r = b - csr_matvec(A, x)
    beta = np.linalg.norm(r)
    
    total_iter = 0
    
    for outer in range(max_iter):
        # 归一化初始向量
        q = r / beta
        Q = [q]
        H = np.zeros((restart + 1, restart))
        e = np.zeros(restart + 1)
        e[0] = beta
        
        for j in range(restart):
            total_iter += 1
            
            # Arnoldi过程
            v = csr_matvec(A, Q[j])
            
            for i in range(j + 1):
                h = np.dot(v, Q[i])
                H[i, j] = h
                v = v - h * Q[i]
            
            h_next = np.linalg.norm(v)
            H[j + 1, j] = h_next
            
            if h_next < 1e-15:
                Q.append(v)
                break
            
            Q.append(v / h_next)
            
            # 最小二乘
            y = np.linalg.lstsq(H[:j+2, :j+1], e[:j+2], rcond=None)[0]
            
            # 更新解
            x_new = x + sum(Q[k] * y[k] for k in range(j+1))
            
            # 检查收敛
            residual = b - csr_matvec(A, x_new)
            if np.linalg.norm(residual) / beta < tol:
                return x_new, total_iter, np.linalg.norm(residual)
        
        # 重启
        x = x_new
        r = b - csr_matvec(A, x)
        beta = np.linalg.norm(r)
        
        if beta < tol:
            break
    
    return x, total_iter, beta


def sparse_jacobi_precond(M: CSRMatrix) -> CSRMatrix:
    """
    创建Jacobi预处理矩阵 M = diag(A)^{-1}
    
    返回:
        预处理矩阵的逆（对角矩阵）
    """
    diag_A = M.diagonal()
    diag_inv = 1.0 / diag_A
    
    # 构建对角矩阵的CSR表示
    data = diag_inv
    indices = np.arange(len(diag_inv))
    indptr = np.arange(len(diag_inv) + 1)
    
    return CSRMatrix(data, indices, indptr)


if __name__ == "__main__":
    print("=" * 55)
    print("稀疏线性系统求解器测试")
    print("=" * 55)
    
    from sparse_matrix_csr import create_laplacian_1d, CSRMatrix
    
    # 创建测试问题: L @ x = b
    n = 500
    L = create_laplacian_1d(n)
    x_exact = np.random.randn(n)
    b = L.matvec(x_exact)
    
    print(f"\n测试问题: {n}x{n} 稀疏矩阵")
    info = L.info()
    print(f"非零元素: {info['nnz']}, 密度: {info['density']:.4f}")
    
    # CG求解
    print("\n--- 稀疏CG ---")
    x_cg, iter_cg, res_cg = sparse_cg(L, b)
    print(f"迭代次数: {iter_cg}")
    print(f"残差: {res_cg:.2e}")
    print(f"解误差: {np.linalg.norm(x_cg - x_exact):.2e}")
    
    # 创建非对称稀疏矩阵测试BiCGSTAB和GMRES
    print("\n--- 非对称稀疏矩阵测试 ---")
    np.random.seed(42)
    
    # 生成随机稀疏矩阵
    density = 0.02
    A_dense = np.random.randn(n, n) * (np.random.rand(n, n) < density)
    A_dense = A_dense + np.eye(n) * 5  # 对角占优
    
    A = CSRMatrix.from_dense(A_dense)
    x_exact2 = np.random.randn(n)
    b2 = A.matvec(x_exact2)
    
    print(f"矩阵密度: {A.info()['density']:.4f}")
    
    # BiCGSTAB
    print("\n--- 稀疏BiCGSTAB ---")
    x_bicg, iter_bicg, res_bicg = sparse_bicgstab(A, b2)
    print(f"迭代次数: {iter_bicg}")
    print(f"解误差: {np.linalg.norm(x_bicg - x_exact2):.2e}")
    
    # GMRES
    print("\n--- 稀疏GMRES (restart=30) ---")
    x_gmres, iter_gmres, res_gmres = sparse_gmres(A, b2, restart=30)
    print(f"迭代次数: {iter_gmres}")
    print(f"解误差: {np.linalg.norm(x_gmres - x_exact2):.2e}")
    
    # Jacobi预处理
    print("\n--- Jacobi预处理CG ---")
    M_inv = sparse_jacobi_precond(L)
    
    # 手动实现预处理CG
    x0 = np.zeros(n)
    r = b - L.matvec(x0)
    z = M_inv.matvec(r)
    p = z.copy()
    r_norm0 = np.linalg.norm(r)
    
    for iteration in range(min(n, 200)):
        Ap = L.matvec(p)
        r_dot_z = np.dot(r, z)
        p_dot_Ap = np.dot(p, Ap)
        
        if abs(p_dot_Ap) < 1e-15:
            break
        
        alpha = r_dot_z / p_dot_Ap
        x = x + alpha * p
        r_new = r - alpha * Ap
        
        if np.linalg.norm(r_new) / r_norm0 < 1e-10:
            print(f"预处理CG迭代次数: {iteration + 1}")
            break
        
        z_new = M_inv.matvec(r_new)
        beta = np.dot(r_new, z_new) / r_dot_z
        p = z_new + beta * p
        
        r = r_new
        z = z_new
    
    print(f"解误差: {np.linalg.norm(x - x_exact):.2e}")
    
    print("\n测试通过！稀疏求解器工作正常。")
