# -*- coding: utf-8 -*-
"""
算法实现：外部内存算法 / cache_oblivious_matrix

本文件实现 cache_oblivious_matrix 相关的算法功能。
"""

import numpy as np
from typing import Tuple


class CacheObliviousMatrixMultiply:
    """缓存无关矩阵乘法"""

    def __init__(self, block_size: int = 64):
        """
        参数：
            block_size: 基础块大小
        """
        self.block_size = block_size

    def multiply_recursive(self, A: np.ndarray, B: np.ndarray,
                          C: np.ndarray,
                          row_start: int, col_start: int, k_start: int,
                          m: int, n: int, k: int) -> None:
        """
        递归分块乘法

        参数：
            A, B, C: 矩阵
            row_start, col_start, k_start: 起始位置
            m, n, k: 维度
        """
        # 小矩阵用朴素乘法
        if m <= self.block_size and n <= self.block_size and k <= self.block_size:
            self._naive_multiply(A, B, C, row_start, col_start, k_start, m, n, k)
            return

        # 分块
        if m >= n and m >= k:
            # 沿行方向分割
            mid = m // 2
            self.multiply_recursive(A, B, C, row_start, col_start, k_start, mid, n, k)
            self.multiply_recursive(A, B, C, row_start + mid, col_start, k_start, m - mid, n, k)
        elif n >= k:
            # 沿列方向分割
            mid = n // 2
            self.multiply_recursive(A, B, C, row_start, col_start, k_start, m, mid, k)
            self.multiply_recursive(A, B, C, row_start, col_start + mid, k_start, m, n - mid, k)
        else:
            # 沿k方向分割（最复杂）
            mid = k // 2
            self.multiply_recursive(A, B, C, row_start, col_start, k_start, m, n, mid)
            self.multiply_recursive(A, B, C, row_start, col_start, k_start + mid, m, n, k - mid)

    def _naive_multiply(self, A: np.ndarray, B: np.ndarray, C: np.ndarray,
                       row_start: int, col_start: int, k_start: int,
                       m: int, n: int, k: int) -> None:
        """朴素乘法"""
        for i in range(m):
            for j in range(n):
                for p in range(k):
                    C[row_start + i, col_start + j] += A[row_start + i, k_start + p] * B[k_start + p, col_start + j]

    def multiply(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        """
        矩阵乘法

        返回：C = A @ B
        """
        m, k1 = A.shape
        k2, n = B.shape

        if k1 != k2:
            raise ValueError("矩阵维度不匹配")

        C = np.zeros((m, n))

        self.multiply_recursive(A, B, C, 0, 0, 0, m, n, k1)

        return C


def cache_oblivious_analysis():
    """缓存无关分析"""
    print("=== 缓存无关分析 ===")
    print()
    print("复杂度：")
    print("  - 时间：O(n³)")
    print("  - 缓存：O(n²/B + n²/M)")
    print("  - 对任意缓存大小都有效")
    print()
    print("分块策略：")
    print("  - 递归分治")
    print("  - 平衡子问题大小")
    print("  - 保证缓存局部性")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 缓存无关矩阵乘法测试 ===\n")

    np.random.seed(42)

    # 小矩阵测试
    A = np.random.randn(4, 4)
    B = np.random.randn(4, 4)

    print(f"矩阵A: {A.shape}")
    print(f"矩阵B: {B.shape}")
    print()

    # 缓存无关乘法
    co_mult = CacheObliviousMatrixMultiply()

    C_co = co_mult.multiply(A, B)

    # NumPy参考
    C_np = A @ B

    # 误差
    error = np.linalg.norm(C_co - C_np)
    print(f"结果误差: {error:.6f}")
    print(f"正确: {'✅' if error < 1e-5 else '❌'}")

    print()
    print("说明：")
    print("  - 缓存无关算法对所有缓存大小都有效")
    print("  - 递归分块利用空间局部性")
    print("  - 理论上是外部内存算法的理想方案")
