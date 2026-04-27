# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / l1_minimization



本文件实现 l1_minimization 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Callable





def iterative_reweighted_lsq(A: np.ndarray, y: np.ndarray,

                              p: float = 0.5,

                              max_iter: int = 100,

                              tol: float = 1e-6) -> Tuple[np.ndarray, int]:

    """

    迭代重加权最小二乘（IRLS）用于ℓp最小化

    核心思想：将非凸问题转化为一系列加权ℓ2问题



    min Σ w_i x_i^2  s.t. ||Ax - y||₂ ≤ ε

    其中 w_i = 1 / (|x_i| + δ)^(1-p)

    """

    n = A.shape[1]

    x = np.zeros(n)

    delta = 1e-6  # 避免除零



    for iteration in range(max_iter):

        # 计算权重

        weights = 1.0 / (np.abs(x) + delta) ** (1 - p)



        # 加权矩阵

        W = np.diag(weights)



        # 加权最小二乘：min ||W(Ax - y)||²

        WA = W @ A

        Wy = W @ y



        # 解加权最小二乘

        x_new, _, _, _ = np.linalg.lstsq(WA, Wy, rcond=None)



        # 检查收敛

        if np.linalg.norm(x_new - x) < tol:

            return x_new, iteration + 1



        x = x_new



    return x, max_iter





def half_thresholding(A: np.ndarray, y: np.ndarray,

                     s: int,

                     max_iter: int = 100,

                     tol: float = 1e-6) -> Tuple[np.ndarray, int]:

    """

    半阈值迭代（Half Thresholding）

    用于ℓ1/2正则化，阈值函数为：

    η(x, λ) = sign(x) * max(0, |x| - λ)

    但更复杂因为ℓ1/2的阈值函数非单调



    简化实现：使用迭代收缩

    """

    n = A.shape[1]

    x = np.zeros(n)

    lambda_0 = 0.1  # 正则化参数



    for iteration in range(max_iter):

        # 计算残差

        residual = y - A @ x



        # 梯度

        gradient = -A.T @ residual



        # 更新x

        x_new = x - lambda_0 * gradient



        # 硬阈值（稀疏约束）

        magnitudes = np.abs(x_new)

        threshold_idx = np.argsort(magnitudes)[-s:]

        x = np.zeros(n)

        x[threshold_idx] = x_new[threshold_idx]



        # 收敛检查

        if np.linalg.norm(x_new - x) < tol:

            break



    return x, iteration + 1





def reweighted_l0(A: np.ndarray, y: np.ndarray,

                 s: int,

                 max_iter: int = 20,

                 epsilon: float = 1e-6) -> Tuple[np.ndarray, int]:

    """

    迭代重加权ℓ0（IRL0）

    思想：用ℓ1近似ℓ0，然后逐步调整权重



    min Σ w_i |x_i|  s.t. ||Ax - y||² ≤ ε

    其中 w_i = 1 / (|x_i| + ε)

    """

    n = A.shape[1]

    x = np.zeros(n)

    weights = np.ones(n)



    for iteration in range(max_iter):

        # 加权ℓ1最小化

        W = np.diag(weights)



        # 构造加权问题（通过变量替换 z_i = w_i * x_i）

        # 简化：使用OMP风格的贪婪方法



        # 残差

        residual = y - A @ x



        # 更新权重

        new_weights = 1.0 / (np.abs(x) + epsilon)

        weights = new_weights



        # 选择最大相关列

        c = A.T @ residual

        weighted_c = weights * np.abs(c)



        support_size = min(s + iteration, n)

        support = np.argsort(weighted_c)[-support_size:]



        # 在支撑上求解

        A_support = A[:, support]

        x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)



        x_new = np.zeros(n)

        x_new[support] = x_support



        # 收敛检查

        if np.linalg.norm(x_new - x) < tol:

            x = x_new

            break



        x = x_new



    return x, iteration + 1





def scad_threshold(x: np.ndarray, lambda_: float, a: float = 3.7) -> np.ndarray:

    """

    SCAD（Smoothly Clipped Absolute Deviation）阈值函数

    比ℓ1更平滑的惩罚



    SCAD(x, λ) =

        sign(x) * max(0, λ - |x|)                     if |x| ≤ λ

        sign(x) * max(0, (aλ - |x|)/(a-1) - λ)       if λ < |x| ≤ aλ

        x                                              if |x| > aλ

    """

    n = len(x)

    x_scad = np.zeros(n)



    for i in range(n):

        abs_x = np.abs(x[i])



        if abs_x <= lambda_:

            x_scad[i] = np.sign(x[i]) * max(0, lambda_ - abs_x)

        elif abs_x <= a * lambda_:

            x_scad[i] = np.sign(x[i]) * (a * lambda_ - abs_x) / (a - 1)

        else:

            x_scad[i] = x[i]



    return x_scad





def mcp_threshold(x: np.ndarray, lambda_: float, gamma: float = 2.0) -> np.ndarray:

    """

    MCP（Minimax Concave Penalty）阈值函数

    MCP(x, λ, γ) = λ|x| - x²/(2γ)  for |x| ≤ γλ

                   = (γλ²)/2           for |x| > γλ

    """

    n = len(x)

    x_mcp = np.zeros(n)



    for i in range(n):

        abs_x = np.abs(x[i])



        if abs_x <= gamma * lambda_:

            # 惩罚项的梯度

            x_mcp[i] = np.sign(x[i]) * (abs_x - abs_x ** 2 / (2 * gamma * lambda_))

        else:

            x_mcp[i] = x[i]



    return x_mcp





def _soft_threshold(x: np.ndarray, threshold: float) -> np.ndarray:

    """软阈值函数"""

    return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)





def iterative_sparse_recovery(A: np.ndarray, y: np.ndarray,

                               method: str = "reweighted_l0",

                               s: int = 10,

                               max_iter: int = 100,

                               tol: float = 1e-6) -> Tuple[np.ndarray, int]:

    """

    通用迭代稀疏恢复接口

    支持多种非凸惩罚方法

    """

    if method == "reweighted_lp":

        return iterative_reweighted_lsq(A, y, p=0.5, max_iter=max_iter, tol=tol)

    elif method == "reweighted_l0":

        return reweighted_l0(A, y, s, max_iter=max_iter, tol=tol)

    elif method == "half":

        return half_thresholding(A, y, s, max_iter=max_iter, tol=tol)

    else:

        raise ValueError(f"Unknown method: {method}")





def test_nonconvex_cs():

    """测试非凸ℓp压缩感知"""

    np.random.seed(42)



    n = 500

    m = 150

    s = 20



    print("=== 非凸ℓp最小化测试 ===")

    print(f"信号维度: {n}, 测量数: {m}, 稀疏度: {s}")



    # 生成稀疏信号

    x_true = np.zeros(n)

    support = np.random.choice(n, s, replace=False)

    x_true[support] = np.random.randn(s)



    # 测量矩阵

    A = np.random.randn(m, n) / np.sqrt(m)



    # 测量

    y = A @ x_true + 0.001 * np.random.randn(m)



    # 不同的非凸方法

    print("\n--- 不同非凸方法对比 ---")

    print(f"{'方法':<20} {'迭代':>8} {'误差':>12}")



    methods = [

        ("reweighted_lp", iterative_sparse_recovery(A, y, "reweighted_lp", s)),

        ("reweighted_l0", iterative_sparse_recovery(A, y, "reweighted_l0", s)),

        ("half", iterative_sparse_recovery(A, y, "half", s)),

    ]



    for name, (x_rec, it) in methods:

        err = np.linalg.norm(x_rec - x_true) / np.linalg.norm(x_true)

        print(f"{name:<20} {it:>8d} {err:>12.6f}")



    # 对比ℓ1（cvx）

    print("\n--- ℓ1 vs ℓp=0.5 对比 ---")

    x_lp05, it_lp05 = iterative_reweighted_lsq(A, y, p=0.5)

    x_lp01, it_lp01 = iterative_reweighted_lsq(A, y, p=0.1)



    err_lp05 = np.linalg.norm(x_lp05 - x_true) / np.linalg.norm(x_true)

    err_lp01 = np.linalg.norm(x_lp01 - x_true) / np.linalg.norm(x_true)



    print(f"ℓ1 (p=1.0): 基准")

    print(f"ℓ0.5 (p=0.5): 误差={err_lp05:.6f}")

    print(f"ℓ0.1 (p=0.1): 误差={err_lp01:.6f}")



    # 不同稀疏度测试

    print("\n--- 不同稀疏度下性能 ---")

    print(f"{'s':>4} {'ℓ1误差':>12} {'ℓ0.5误差':>12} {'ℓ0.1误差':>12}")



    for s_test in [10, 20, 30, 40, 50]:

        x_t = np.zeros(n)

        sup = np.random.choice(n, s_test, replace=False)

        x_t[sup] = np.random.randn(s_test)

        y_t = A @ x_t



        x_l1, _ = iterative_sparse_recovery(A, y_t, "reweighted_lp", s_test)

        x_lp05, _ = iterative_reweighted_lsq(A, y_t, p=0.5)

        x_lp01, _ = iterative_reweighted_lsq(A, y_t, p=0.1)



        err_l1 = np.linalg.norm(x_l1 - x_t) / np.linalg.norm(x_t)

        err_lp05 = np.linalg.norm(x_lp05 - x_t) / np.linalg.norm(x_t)

        err_lp01 = np.linalg.norm(x_lp01 - x_t) / np.linalg.norm(x_t)



        print(f"{s_test:4d} {err_l1:12.6f} {err_lp05:12.6f} {err_lp01:12.6f}")





if __name__ == "__main__":

    test_nonconvex_cs()

