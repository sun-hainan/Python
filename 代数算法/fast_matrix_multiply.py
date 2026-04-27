# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / fast_matrix_multiply

本文件实现 fast_matrix_multiply 相关的算法功能。
"""

import numpy as np
from typing import Tuple


class FastMatrixMultiplier:
    """快速矩阵乘法框架"""

    def __init__(self, method: str = "strassen"):
        """
        参数：
            method: 方法选择
        """
        self.method = method

    def multiply(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        """
        矩阵乘法

        参数：
            A: m×k 矩阵
            B: k×n 矩阵

        返回：C = A × B
        """
        if self.method == "naive":
            return self._naive_multiply(A, B)
        elif self.method == "strassen":
            return self._strassen(A, B)
        elif self.method == "divide_conquer":
            return self._divide_conquer(A, B)
        else:
            return self._naive_multiply(A, B)

    def _naive_multiply(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        """朴素乘法 O(n³)"""
        m, k = A.shape
        k2, n = B.shape

        C = np.zeros((m, n))

        for i in range(m):
            for j in range(n):
                for p in range(k):
                    C[i, j] += A[i, p] * B[p, j]

        return C

    def _strassen(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        """Strassen算法 O(n^{2.81})"""
        n = A.shape[0]

        # 小矩阵用朴素乘法
        if n <= 64:
            return self._naive_multiply(A, B)

        # 分块
        mid = n // 2

        A11 = A[:mid, :mid]
        A12 = A[:mid, mid:]
        A21 = A[mid:, :mid]
        A22 = A[mid:, mid:]

        B11 = B[:mid, :mid]
        B12 = B[:mid, mid:]
        B21 = B[mid:, :mid]
        B22 = B[mid:, mid:]

        # Strassen的7个乘法
        M1 = self._strassen(A11 + A22, B11 + B22)
        M2 = self._strassen(A21 + A22, B11)
        M3 = self._strassen(A11, B12 - B22)
        M4 = self._strassen(A22, B21 - B11)
        M5 = self._strassen(A11 + A12, B22)
        M6 = self._strassen(A21 - A11, B11 + B12)
        M7 = self._strassen(A12 - A22, B21 + B22)

        # 组合结果
        C = np.zeros_like(A)

        C[:mid, :mid] = M1 + M4 - M5 + M7
        C[:mid, mid:] = M3 + M5
        C[mid:, :mid] = M2 + M4
        C[mid:, mid:] = M1 - M2 + M3 + M6

        return C

    def _divide_conquer(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        """分治乘法"""
        n = A.shape[0]

        if n <= 64:
            return self._naive_multiply(A, B)

        mid = n // 2

        # 分块
        C = np.zeros((n, n))

        A11 = A[:mid, :mid]
        A12 = A[:mid, mid:]
        A21 = A[mid:, :mid]
        A22 = A[mid:, mid:]

        B11 = B[:mid, :mid]
        B12 = B[:mid, mid:]
        B21 = B[mid:, :mid]
        B22 = B[mid:, mid:]

        # 递归
        C[:mid, :mid] = self._divide_conquer(A11, B11) + self._divide_conquer(A12, B21)
        C[:mid, mid:] = self._divide_conquer(A11, B12) + self._divide_conquer(A12, B22)
        C[mid:, :mid] = self._divide_conquer(A21, B11) + self._divide_conquer(A22, B21)
        C[mid:, mid:] = self._divide_conquer(A21, B12) + self._divide_conquer(A22, B22)

        return C


def matrix_mult_complexity():
    """矩阵乘法复杂度"""
    print("=== 矩阵乘法复杂度 ===")
    print()
    print("方法对比：")
    print("  朴素: O(n³)")
    print("  Strassen: O(n^{2.81})")
    print("  Coppersmith-Winograd: O(n^{2.37})")
    print("  最优已知: O(n^{2.37})")
    print()
    print("理论极限：")
    print("  下界: Ω(n²)")
    print("  上界: O(n^{2.37})")
    print("  是否能达到 n²？未知")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 快速矩阵乘法测试 ===\n")

    np.random.seed(42)

    # 测试矩阵
    n = 128
    A = np.random.rand(n, n)
    B = np.random.rand(n, n)

    print(f"矩阵大小: {n}×{n}")
    print()

    # 验证正确性
    multiplier = FastMatrixMultiplier(method="strassen")

    # Strassen
    C_strassen = multiplier.multiply(A, B)

    # 朴素（用于对比）
    C_numpy = A @ B

    # 检查误差
    error = np.linalg.norm(C_strassen - C_numpy)
    print(f"Strassen误差: {error:.6f}")

    # 性能测试
    import time

    for method in ["naive", "strassen"]:
        multiplier = FastMatrixMultiplier(method=method)

        start = time.time()
        C = multiplier.multiply(A, B)
        elapsed = time.time() - start

        print(f"{method}: {elapsed:.3f}秒")

    print()
    matrix_mult_complexity()

    print()
    print("说明：")
    print("  - Strassen适合大方阵")
    print("  - 小矩阵用朴素乘法更快")
    print("  - 实践中考虑缓存友好性")
