# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / rip_spark

本文件实现 rip_spark 相关的算法功能。
"""

import numpy as np
from typing import Optional
from scipy import linalg


def compute_spark(A: np.ndarray) -> int:
    """
    计算矩阵A的Spark常数
    Spark = 最小线性相关列数（即A列空间中任何两组列之间的线性关系数）

    计算方法：尝试所有可能的列组合，找到最小的线性相关数
    注意：这是NP-hard问题，实际中只计算到某个阈值
    """
    m, n = A.shape
    spark = n + 1  # 上界

    # 简化计算：只检查2-稀疏情况（因为计算量大）
    # 实际中可以通过SVD检查相关性

    # 方法：通过SVD计算列空间的最小奇异值
    # 如果最小的奇异值接近0，说明存在高度相关的列

    U, s, Vh = linalg.svd(A)
    rank = np.sum(s > 1e-10)  # 数值秩

    # Spark >= n - rank + 1
    # 即：线性无关列数的上界
    spark = n - rank + 1

    return spark


def check_rip_condition(A: np.ndarray, s: int, delta: float = 0.5) -> tuple[bool, float]:
    """
    检查矩阵A是否满足s阶RIP条件
    RIP: 对所有s-稀疏向量x，满足
    (1-δ) ||x||² ≤ ||Ax||² ≤ (1+δ) ||x||²

    方法：采样检查法（Monte Carlo RIP验证）
    """
    m, n = A.shape

    # 如果s * m < n，RIP可能不满足
    if s * m < n:
        return False, 0.0

    # 简化：用功率法估计RIP常数
    # 取多个随机s-稀疏向量检查
    max_ratio = 0.0
    min_ratio = float('inf')

    np.random.seed(42)
    num_tests = min(1000, 100 * s)

    for _ in range(num_tests):
        # 生成随机s-稀疏向量
        x = np.zeros(n)
        support = np.random.choice(n, s, replace=False)
        x[support] = np.random.randn(s)

        x_norm_sq = np.linalg.norm(x) ** 2
        if x_norm_sq < 1e-10:
            continue

        Ax = A @ x
        Ax_norm_sq = np.linalg.norm(Ax) ** 2

        ratio = Ax_norm_sq / x_norm_sq
        max_ratio = max(max_ratio, ratio)
        min_ratio = min(min_ratio, ratio)

    estimated_delta = max(max_ratio - 1, 1 - min_ratio)
    satisfies_rip = estimated_delta <= delta

    return satisfies_rip, estimated_delta


def compute_mutual_coherence(A: np.ndarray) -> float:
    """
    计算互相关度（Mutual Coherence）
    μ(A) = max_{i≠j} |a_i^T a_j| / (||a_i|| ||a_j||)
    性质：μ ≥ 1/√m, μ ≥ 1/√n

    RIP的充分条件：s < (1/μ + 1) / 2 时可恢复
    """
    # 归一化列
    A_norm = A / np.linalg.norm(A, axis=0)

    # 计算Gram矩阵
    G = A_norm.T @ A_norm

    # 对角线置零（排除自身相关）
    np.fill_diagonal(G, 0)

    # 最大绝对值即为互相关度
    mu = np.max(np.abs(G))

    return mu


def rip_bound_from_mutual_coherence(mu: float, s: int) -> bool:
    """
    互相关度推导RIP上界
    如果 μ < 1/(2s-1)，则RIP(s, 2δ)成立
    """
    return mu < 1.0 / (2 * s - 1)


def estimate_recovery_bound(A: np.ndarray, s: int) -> dict:
    """
    估计信号恢复的理论边界
    """
    m, n = A.shape
    mu = compute_mutual_coherence(A)

    spark = compute_spark(A)
    rip_ok, delta = check_rip_condition(A, s)

    return {
        "matrix_size": f"{m}×{n}",
        "sparsity": s,
        "mutual_coherence": mu,
        "spark_constant": spark,
        "rip_satisfied": rip_ok,
        "rip_delta": delta,
        "recovery_bound_s": s,
        "theoretical_max_s": int(0.5 * (1 / mu + 1)) if mu > 0 else n,
    }


if __name__ == "__main__":
    print("=== RIP与Spark常数演示 ===")

    # 创建测试矩阵
    np.random.seed(123)

    # 1. 随机高斯矩阵（RIP大概率满足）
    print("\n--- 随机高斯矩阵 (m=100, n=500) ---")
    A_gaussian = np.random.randn(100, 500) / np.sqrt(100)

    result = estimate_recovery_bound(A_gaussian, s=10)
    for k, v in result.items():
        print(f"  {k}: {v}")

    # 2. 傅里叶矩阵（稀疏测量场景）
    print("\n--- 傅里叶矩阵 (m=64, n=256) ---")
    n = 256
    m = 64
    A_fourier = np.fft.dft(np.eye(n))[:, :m].real  # 简化的傅里叶子矩阵

    result = estimate_recovery_bound(A_fourier, s=8)
    for k, v in result.items():
        print(f"  {k}: {v}")

    # 3. 相关性强的矩阵（RIP不满足）
    print("\n--- 相关矩阵（列高度相关）---")
    A_correlated = np.random.randn(50, 100)
    A_correlated[:, 1] = A_correlated[:, 0] + 0.1 * np.random.randn(50)  # 列1接近列0

    mu = compute_mutual_coherence(A_correlated)
    print(f"  互相关度: {mu:.4f}")
    print(f"  Spark: {compute_spark(A_correlated)}")

    # RIP验证
    print("\n=== RIP条件验证 ===")
    s_values = [5, 10, 15, 20]

    for s in s_values:
        rip_ok, delta = check_rip_condition(A_gaussian, s)
        print(f"s={s:2d}: RIP满足={'是' if rip_ok else '否'} (δ≈{delta:.3f})")

    print("\n理论边界:")
    print(f"基于互相关度，最大可恢复稀疏度: s < {result['theoretical_max_s']}")
