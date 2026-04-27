# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / iht

本文件实现 iht 相关的算法功能。
"""

import numpy as np
from typing import Tuple


def iht(A: np.ndarray, y: np.ndarray, s: int,
        max_iter: int = 500, tol: float = 1e-6,
        x0: np.ndarray = None) -> Tuple[np.ndarray, int, list[float]]:
    """
    迭代硬阈值算法（IHT）
    输入：
        A: 测量矩阵 (m × n)
        y: 测量向量 (m,)
        s: 稀疏度
        max_iter: 最大迭代次数
        tol: 收敛阈值
        x0: 初始估计
    输出：
        x: 恢复信号
        iterations: 迭代次数
        residual_history: 残差范数历史
    """
    m, n = A.shape

    # 初始化
    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()

    residual_history = []
    residual_norm = float('inf')

    # 计算步长（固定为1/L，谱范数的倒数）
    # L = λ_max(A^T A)，即A的最大奇异值的平方
    spectral_norm = np.linalg.norm(A, ord=2)
    step_size = 1.0 / (spectral_norm ** 2)

    for iteration in range(max_iter):
        # 1. 梯度步骤：x_{k+1} = x_k + μ * A^T (y - Ax)
        residual = y - A @ x
        gradient = A.T @ residual
        x_new = x + step_size * gradient

        # 2. 硬阈值：保留s个最大绝对值，其余置零
        magnitudes = np.abs(x_new)
        threshold_idx = np.argsort(magnitudes)[-s:]
        x_hard = np.zeros(n)
        x_hard[threshold_idx] = x_new[threshold_idx]

        # 3. 计算新的残差
        residual_new = y - A @ x_hard
        residual_norm_new = np.linalg.norm(residual_new)

        # 4. 记录残差历史
        residual_history.append(residual_norm_new)

        # 5. 收敛检查
        if abs(residual_norm_new - residual_norm) < tol:
            return x_hard, iteration + 1, residual_history

        x = x_hard
        residual_norm = residual_norm_new

        # 可选：提前终止如果残差增大
        if len(residual_history) > 1:
            if residual_history[-1] > residual_history[-2] * 1.1:
                break

    return x, iteration + 1, residual_history


def normalized_iht(A: np.ndarray, y: np.ndarray, s: int,
                  max_iter: int = 500, tol: float = 1e-6) -> Tuple[np.ndarray, int]:
    """
    归一化IHT（Normalized IHT）
    每轮自适应调整步长，提高收敛速度
    """
    m, n = A.shape
    x = np.zeros(n)
    residual = y.copy()

    for iteration in range(max_iter):
        # 计算步长：μ_k = ||r||² / ||A^T r||²
        AT_residual = A.T @ residual
        norm_AT_r = np.linalg.norm(AT_residual)
        if norm_AT_r < 1e-10:
            break

        step_size = np.dot(residual, residual) / np.dot(AT_residual, AT_residual)

        # 梯度步骤
        x_new = x + step_size * AT_residual

        # 硬阈值
        magnitudes = np.abs(x_new)
        threshold_idx = np.argsort(magnitudes)[-s:]
        x = np.zeros(n)
        x[threshold_idx] = x_new[threshold_idx]

        # 更新残差
        residual = y - A @ x

        # 收敛检查
        if np.linalg.norm(residual) < tol:
            break

    return x, iteration + 1


def hard_threshold(x: np.ndarray, s: int) -> np.ndarray:
    """
    硬阈值函数：保留最大的s个值，其余置零
    """
    n = len(x)
    x_thresh = np.zeros(n)
    indices = np.argsort(np.abs(x))[-s:]
    x_thresh[indices] = x[indices]
    return x_thresh


def ciht(A: np.ndarray, y: np.ndarray, s: int,
         max_iter: int = 500, tol: float = 1e-6) -> Tuple[np.ndarray, int]:
    """
    约束IHT（Constrained IHT）：在满足测量约束下求解
    等价于 projected IHT
    """
    m, n = A.shape
    x = np.zeros(n)

    spectral_norm = np.linalg.norm(A, ord=2)
    step_size = 1.0 / (spectral_norm ** 2)

    for iteration in range(max_iter):
        # 梯度步骤
        residual = y - A @ x
        x_new = x + step_size * A.T @ residual

        # 硬阈值
        x_new = hard_threshold(x_new, s)

        # 投影回可行解（如果需要）
        # x_new = project_to_measurement(x_new, y, A)

        # 收敛检查
        if np.linalg.norm(x_new - x) < tol:
            break

        x = x_new

    return x, iteration + 1


def test_iht():
    """测试IHT算法"""
    np.random.seed(42)

    n = 1000  # 信号维度
    m = 300   # 测量数
    s = 30    # 稀疏度

    # 生成稀疏信号
    x_true = np.zeros(n)
    support = np.random.choice(n, s, replace=False)
    x_true[support] = np.random.randn(s)

    # 测量矩阵
    A = np.random.randn(m, n) / np.sqrt(m)

    # 测量（添加少量噪声）
    noise_level = 0.01
    y = A @ x_true + noise_level * np.random.randn(m)

    print("=== 迭代硬阈值（IHT）测试 ===")
    print(f"信号维度: {n}, 测量数: {m}, 稀疏度: {s}")

    # 标准IHT
    x_iht, iterations, history = iht(A, y, s, max_iter=500)
    error_iht = np.linalg.norm(x_iht - x_true) / np.linalg.norm(x_true)

    print(f"\n标准IHT:")
    print(f"  迭代次数: {iterations}")
    print(f"  最终残差: {history[-1]:.6f}")
    print(f"  恢复误差: {error_iht:.6f}")

    # 归一化IHT
    x_niht, it_niht = normalized_iht(A, y, s)
    error_niht = np.linalg.norm(x_niht - x_true) / np.linalg.norm(x_true)

    print(f"\n归一化IHT:")
    print(f"  迭代次数: {it_niht}")
    print(f"  恢复误差: {error_niht:.6f}")

    # 约束IHT
    x_ciht, it_ciht = ciht(A, y, s)
    error_ciht = np.linalg.norm(x_ciht - x_true) / np.linalg.norm(x_true)

    print(f"\n约束IHT:")
    print(f"  迭代次数: {it_ciht}")
    print(f"  恢复误差: {error_ciht:.6f}")

    # 不同稀疏度测试
    print("\n--- 不同稀疏度下的性能 ---")
    print(f"{'s':>4} {'IHT迭代':>8} {'IHT误差':>12} {'收敛迭代':>10}")

    for s_test in [10, 20, 30, 40, 50]:
        x_t = np.zeros(n)
        sup = np.random.choice(n, s_test, replace=False)
        x_t[sup] = np.random.randn(s_test)
        y_t = A @ x_t + 0.001 * np.random.randn(m)

        x_r, it, _ = iht(A, y_t, s_test, max_iter=200)
        err = np.linalg.norm(x_r - x_t) / np.linalg.norm(x_t)

        print(f"{s_test:4d} {it:8d} {err:12.6f} {len([h for h in _ if h < _[0] * 0.1]):10d}")

    return error_iht < 0.1


if __name__ == "__main__":
    test_iht()
