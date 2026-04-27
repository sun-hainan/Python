# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / subspace_pursuit

本文件实现 subspace_pursuit 相关的算法功能。
"""

import numpy as np
from typing import Tuple


def subspace_pursuit(A: np.ndarray, y: np.ndarray, s: int,
                     max_iter: int = 100, tol: float = 1e-6) -> Tuple[np.ndarray, int]:
    """
    子空间追踪（SP）算法
    输入：
        A: 测量矩阵 (m × n)
        y: 测量向量 (m,)
        s: 稀疏度
    输出：
        x: 恢复信号 (n,)
        iterations: 迭代次数
    """
    m, n = A.shape
    x = np.zeros(n)
    support = np.zeros(n, dtype=bool)  # 支撑集
    residual = y.copy()
    iterations = 0

    for iteration in range(max_iter):
        iterations += 1

        # 1. 计算相关性向量
        c = A.T @ residual  # (n,)

        # 2. 候选集：选择s个最大相关列
        magnitudes = np.abs(c)
        # 找到s个最大值的索引（排除已在支撑集的）
        remaining_indices = np.where(~support)[0]
        remaining_magnitudes = magnitudes[remaining_indices]
        s_largest_idx = np.argsort(remaining_magnitudes)[-s:]
        candidate_indices = remaining_indices[s_largest_idx]

        # 合并候选集与当前支撑集
        candidate_set = np.union1d(np.where(support)[0], candidate_indices)

        # 3. 最小二乘求解
        A_cand = A[:, candidate_set]
        # 使用伪逆求解：x_cand = (A^T A)^(-1) A^T y
        # 简化为lstsq
        x_cand = np.linalg.lstsq(A_cand, y, rcond=None)[0]

        # 4. 支撑集更新：选择s个最大系数
        # 重建完整向量
        x_new = np.zeros(n)
        x_new[candidate_set] = x_cand

        # 选出s个最大非零系数
        new_support = np.zeros(n, dtype=bool)
        if np.any(np.abs(x_cand) > 0):
            s_indices = np.argsort(np.abs(x_cand))[-s:]
            new_support[candidate_set[s_indices]] = True

        # 5. 重新计算最小二乘解（仅在新支撑集上）
        A_support = A[:, new_support]
        x_final = np.zeros(n)
        x_final[new_support] = np.linalg.lstsq(A_support, y, rcond=None)[0]

        # 6. 更新残差
        residual_new = y - A @ x_final
        residual_norm = np.linalg.norm(residual_new)

        # 7. 收敛检查
        if residual_norm < tol:
            return x_final, iterations

        # 更新
        support = new_support
        x = x_final
        residual = residual_new

    return x, iterations


def sp_with_confidence(A: np.ndarray, y: np.ndarray, s: int,
                       delta: float = 0.01) -> Tuple[np.ndarray, int]:
    """
    带置信度检查的SP算法
    迭代时检查残差是否持续减小
    """
    m, n = A.shape
    x = np.zeros(n)
    support = np.zeros(n, dtype=bool)
    residual = y.copy()
    prev_residual_norm = float('inf')
    iterations = 0

    for _ in range(max(100, 2 * s)):
        iterations += 1

        # 相关性
        c = A.T @ residual
        magnitudes = np.abs(c)

        # 候选集选择
        remaining_indices = np.where(~support)[0]
        remaining_mags = magnitudes[remaining_indices]
        s_largest_idx = np.argsort(remaining_mags)[-s:]
        candidate_indices = remaining_indices[s_largest_idx]

        candidate_set = np.union1d(np.where(support)[0], candidate_indices)

        # LS求解
        A_cand = A[:, candidate_set]
        x_cand = np.linalg.lstsq(A_cand, y, rcond=None)[0]

        # 支撑集更新
        x_full = np.zeros(n)
        x_full[candidate_set] = x_cand

        new_support = np.zeros(n, dtype=bool)
        s_indices = np.argsort(np.abs(x_cand))[-s:]
        new_support[candidate_set[s_indices]] = True

        # 重新求解
        A_support = A[:, new_support]
        x_new = np.zeros(n)
        x_new[new_support] = np.linalg.lstsq(A_support, y, rcond=None)[0]

        # 残差
        residual_new = y - A @ x_new
        residual_norm = np.linalg.norm(residual_new)

        # 检查残差是否减小
        if residual_norm >= prev_residual_norm * (1 - delta):
            # 收敛
            break

        prev_residual_norm = residual_norm
        support = new_support
        x = x_new
        residual = residual_new

    return x, iterations


def test_sp():
    """测试子空间追踪算法"""
    np.random.seed(42)

    n, m, s = 500, 120, 12

    # 生成稀疏信号
    x_true = np.zeros(n)
    support = np.random.choice(n, s, replace=False)
    x_true[support] = np.random.randn(s)

    # 测量矩阵
    A = np.random.randn(m, n) / np.sqrt(m)

    # 测量
    y = A @ x_true

    # 恢复
    x_recovered, iterations = subspace_pursuit(A, y, s)

    # 评估
    error = np.linalg.norm(x_recovered - x_true) / np.linalg.norm(x_true)

    print(f"信号维度: {n}")
    print(f"测量数: {m}")
    print(f"稀疏度: {s}")
    print(f"迭代次数: {iterations}")
    print(f"恢复误差: {error:.6f}")

    # 检查支撑集
    recovered_support = set(np.where(np.abs(x_recovered) > 0.1)[0])
    true_support = set(support)
    overlap = len(recovered_support & true_support)
    print(f"支撑集重合: {overlap}/{s} ({overlap/s*100:.1f}%)")

    return error < 0.1


if __name__ == "__main__":
    print("=== 子空间追踪（SP）算法演示 ===\n")

    print("--- 基础测试 ---")
    test_sp()

    print("\n--- 性能对比：SP vs CoSaMP ---")
    print(f"{'s':>4} {'SP误差':>12} {'SP迭代':>8} {'CoSaMP误差':>12} {'CoSaMP迭代':>12}")

    np.random.seed(123)
    n, m = 500, 150

    # CoSaMP函数引用（假设已定义）
    from cosamp import cosamp

    for s in [8, 12, 16, 20, 24]:
        x_t = np.zeros(n)
        sup = np.random.choice(n, s, replace=False)
        x_t[sup] = np.random.randn(s)

        A = np.random.randn(m, n) / np.sqrt(m)
        y = A @ x_t

        x_sp, it_sp = subspace_pursuit(A, y, s)
        x_cosamp, it_cosamp = cosamp(A, y, s)

        err_sp = np.linalg.norm(x_sp - x_t) / np.linalg.norm(x_t)
        err_cosamp = np.linalg.norm(x_cosamp - x_t) / np.linalg.norm(x_t)

        print(f"{s:4d} {err_sp:12.6f} {it_sp:8d} {err_cosamp:12.6f} {it_cosamp:12d}")
