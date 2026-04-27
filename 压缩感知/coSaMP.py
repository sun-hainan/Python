# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / coSaMP

本文件实现 coSaMP 相关的算法功能。
"""

import numpy as np
from typing import tuple, Optional


def cosamp(A: np.ndarray, y: np.ndarray, s: int, max_iter: int = 100, tol: float = 1e-6) -> tuple[np.ndarray, int]:
    """
    CoSaMP算法实现
    输入：
        A: 测量矩阵 (m × n)
        y: 测量向量 (m,)
        s: 信号稀疏度（已知）
        max_iter: 最大迭代次数
        tol: 收敛阈值
    输出：
        x: 恢复的稀疏信号 (n,)
        iterations: 迭代次数
    """
    m, n = A.shape
    x = np.zeros(n)
    support = np.zeros(n, dtype=bool)  # 支撑集
    r = y.copy()                        # 残差
    iterations = 0

    for iteration in range(max_iter):
        iterations += 1

        # 1. 匹配：计算A与残差的相关性
        c = A.T @ r  # (n,) 向量

        # 2. 候选集：选择2s个最大相关列
        magnitudes = np.abs(c)
        # 找到前2s个最大值的索引
        candidate_indices = np.argsort(magnitudes)[-2 * s:]
        candidate_set = np.union1d(
            np.where(support)[0],
            candidate_indices
        )

        # 3. 最小二乘估计：在候选集上求解最小二乘
        A_cand = A[:, candidate_set]
        # 最小二乘解：x_cand = (A_cand^T A_cand)^(-1) A_cand^T y
        # 使用伪逆避免病态
        x_cand = np.linalg.lstsq(A_cand, y, rcond=None)[0]

        # 4. 支撑集更新：选出s个最大系数
        # 重排x_cand到完整n维空间
        x_full = np.zeros(n)
        x_full[candidate_set] = x_cand

        # 选出前s个最大非零元
        support_new = np.zeros(n, dtype=bool)
        if np.any(x_cand != 0):
            s_largest = np.argsort(np.abs(x_cand))[-s:]
            support_new[candidate_set[s_largest]] = True

        # 5. 更新信号估计
        x_new = np.zeros(n)
        x_new[support_new] = x_cand[np.argsort(np.abs(x_cand))[-s:]]

        # 6. 更新残差
        Ax_new = A @ x_new
        r_new = y - Ax_new

        # 7. 收敛检查
        residual_norm = np.linalg.norm(r_new)
        if residual_norm < tol:
            x = x_new
            r = r_new
            break

        # 更新
        support = support_new
        x = x_new
        r = r_new

    return x, iterations


def cosamp_known_sparsity(A: np.ndarray, y: np.ndarray, s: int,
                         epsilon: Optional[float] = None) -> tuple[np.ndarray, int]:
    """
    带误差控制的CoSaMP
    适用于测量噪声场景
    """
    m, n = A.shape

    if epsilon is None:
        # 无噪声情况
        return cosamp(A, y, s)

    # 有噪声情况：残差阈值
    x = np.zeros(n)
    r = y.copy()
    support = np.zeros(n, dtype=bool)
    iterations = 0

    for iteration in range(max(100, 2 * s)):
        iterations += 1

        # 匹配
        c = A.T @ r

        # 候选集
        magnitudes = np.abs(c)
        candidate_indices = np.argsort(magnitudes)[-2 * s:]
        candidate_set = np.union1d(np.where(support)[0], candidate_indices)

        # LS估计
        A_cand = A[:, candidate_set]
        x_cand = np.linalg.lstsq(A_cand, y, rcond=None)[0]

        # 选出s个最大
        x_full = np.zeros(n)
        x_full[candidate_set] = x_cand

        support_new = np.zeros(n, dtype=bool)
        s_largest = np.argsort(np.abs(x_cand))[-s:]
        support_new[candidate_set[s_largest]] = True

        x_new = np.zeros(n)
        x_new[support_new] = x_cand[np.argsort(np.abs(x_cand))[-s:]]

        Ax_new = A @ x_new
        r_new = y - Ax_new

        # 有噪声：检查残差是否低于阈值
        if np.linalg.norm(r_new) < epsilon:
            return x_new, iterations

        support = support_new
        x = x_new
        r = r_new

    return x, iterations


def test_cosamp():
    """测试CoSaMP算法"""
    np.random.seed(42)

    # 参数设置
    n = 500   # 信号维度
    m = 150   # 测量数
    s = 15    # 稀疏度

    # 生成稀疏信号
    x_true = np.zeros(n)
    support = np.random.choice(n, s, replace=False)
    x_true[support] = np.random.randn(s)
    x_true = x_true / np.linalg.norm(x_true)  # 归一化

    # 生成测量矩阵（高斯随机）
    A = np.random.randn(m, n) / np.sqrt(m)

    # 测量
    y = A @ x_true

    # CoSaMP恢复
    x_recovered, iterations = cosamp(A, y, s)

    # 计算误差
    error = np.linalg.norm(x_recovered - x_true) / np.linalg.norm(x_true)

    print(f"信号维度: {n}")
    print(f"测量数: {m}")
    print(f"稀疏度: {s}")
    print(f"迭代次数: {iterations}")
    print(f"恢复误差: {error:.6f}")
    print(f"支撑集重合度: {np.sum(support == np.argsort(np.abs(x_recovered))[-s:]) / s * 100:.1f}%")

    return error < 0.1  # 恢复质量检验


if __name__ == "__main__":
    print("=== CoSaMP算法演示 ===\n")

    print("--- 测试1：无噪声稀疏恢复 ---")
    error = test_cosamp()

    print("\n--- 测试2：有噪声场景 ---")
    np.random.seed(42)

    n, m, s = 500, 150, 15
    x_true = np.zeros(n)
    support = np.random.choice(n, s, replace=False)
    x_true[support] = np.random.randn(s)

    A = np.random.randn(m, n) / np.sqrt(m)
    y = A @ x_true + 0.01 * np.random.randn(m)  # 添加噪声

    x_recovered, iterations = cosamp(A, y, s)
    print(f"迭代次数: {iterations}")
    print(f"恢复误差: {np.linalg.norm(x_recovered - x_true) / np.linalg.norm(x_true):.4f}")

    print("\n--- 测试3：不同稀疏度 ---")
    print(f"{'s':>4} {'m':>4} {'迭代':>6} {'误差':>10}")
    for s_test in [5, 10, 15, 20, 25]:
        x_t = np.zeros(n)
        sup = np.random.choice(n, s_test, replace=False)
        x_t[sup] = np.random.randn(s_test)
        y_t = A @ x_t
        x_r, it = cosamp(A, y_t, s_test)
        err = np.linalg.norm(x_r - x_t) / np.linalg.norm(x_t)
        print(f"{s_test:4d} {m:4d} {it:6d} {err:10.6f}")
