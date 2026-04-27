# -*- coding: utf-8 -*-

"""

算法实现：代数算法 / strassen_algorithm



本文件实现 strassen_algorithm 相关的算法功能。

"""



import numpy as np

from typing import Tuple





class StrassenAlgorithm:

    """Strassen矩阵乘法"""



    def __init__(self, threshold: int = 64):

        """

        参数：

            threshold: 小矩阵切换阈值

        """

        self.threshold = threshold



    def multiply(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:

        """

        矩阵乘法



        返回：C = A @ B

        """

        # 确保是方阵且大小是2的幂

        n = max(len(A), len(A[0]), len(B), len(B[0]))

        n_pow2 = 1

        while n_pow2 < n:

            n_pow2 *= 2



        # 填充到2的幂

        A_pad = self._pad_matrix(A, n_pow2)

        B_pad = self._pad_matrix(B, n_pow2)



        # 递归计算

        C_pad = self._strassen_recursive(A_pad, B_pad)



        # 裁剪回原始大小

        m = len(A)

        n_cols = len(A[0]) if len(A) > 0 else len(B)

        return C_pad[:m, :n_cols]



    def _pad_matrix(self, M: np.ndarray, size: int) -> np.ndarray:

        """填充矩阵到指定大小"""

        m, n = M.shape

        padded = np.zeros((size, size))

        padded[:m, :n] = M

        return padded



    def _strassen_recursive(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:

        """

        Strassen递归乘法



        返回：C = A @ B

        """

        n = len(A)



        # 小矩阵用朴素乘法

        if n <= self.threshold:

            return A @ B



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

        M1 = self._strassen_recursive(A11 + A22, B11 + B22)

        M2 = self._strassen_recursive(A21 + A22, B11)

        M3 = self._strassen_recursive(A11, B12 - B22)

        M4 = self._strassen_recursive(A22, B21 - B11)

        M5 = self._strassen_recursive(A11 + A12, B22)

        M6 = self._strassen_recursive(A21 - A11, B11 + B12)

        M7 = self._strassen_recursive(A12 - A22, B21 + B22)



        # 组合结果

        C = np.zeros_like(A)



        C[:mid, :mid] = M1 + M4 - M5 + M7

        C[:mid, mid:] = M3 + M5

        C[mid:, :mid] = M2 + M4

        C[mid:, mid:] = M1 - M2 + M3 + M6



        return C





def strassen_complexity():

    """Strassen复杂度"""

    print("=== Strassen复杂度 ===")

    print()

    print("时间复杂度：")

    print("  - 朴素：O(n³)")

    print("  - Strassen：O(n^{2.807})")

    print()

    print("常数：")

    print("  - 递归开销大")

    print("  - 小矩阵时朴素更快")

    print()

    print("实际应用：")

    print("  - 大矩阵乘法")

    print("  - 科学研究")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Strassen算法测试 ===\n")



    np.random.seed(42)



    # 测试矩阵

    sizes = [4, 8, 16, 32]



    strassen = StrassenAlgorithm(threshold=16)



    for size in sizes:

        A = np.random.randn(size, size)

        B = np.random.randn(size, size)



        # Strassen

        C_strassen = strassen.multiply(A, B)



        # NumPy

        C_numpy = A @ B



        # 误差

        error = np.linalg.norm(C_strassen - C_numpy)

        print(f"大小 {size}×{size}: 误差 = {error:.6f}")



    print()

    strassen_complexity()



    print()

    print("说明：")

    print("  - Strassen是快速矩阵乘法的里程碑")

    print("  - 适合大矩阵")

    print("  - 比朴素乘法有理论加速")

