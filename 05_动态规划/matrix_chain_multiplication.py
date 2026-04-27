# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / matrix_chain_multiplication

本文件实现 matrix_chain_multiplication 相关的算法功能。
"""

from sys import maxsize


def matrix_chain_multiply(arr: list[int]) -> int:
    """
    矩阵链乘法 - 迭代 DP 版

    参数:
        arr: 维度数组，如 [40, 20, 30, 10, 30]
             表示 4 个矩阵：40×20, 20×30, 30×10, 10×30

    返回:
        最少乘法次数

    示例:
        >>> matrix_chain_multiply([1, 2, 3, 4, 3])
        30
        >>> matrix_chain_multiply([10])
        0
        >>> matrix_chain_multiply([10, 20])
        0
        >>> matrix_chain_multiply([19, 2, 19])
        722
    """
    if len(arr) < 2:
        return 0

    n = len(arr)
    # dp[i][j] = 矩阵 Ai 到 Aj 相乘的最小代价
    dp = [[maxsize for _ in range(n)] for _ in range(n)]

    # 只有一个矩阵时，代价为 0
    for i in range(1, n):
        dp[i][i] = 0

    # 枚举链的长度（从 2 到 n）
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            if j >= n:
                continue
            # 枚举分割点 k
            for k in range(i, j):
                # 代价 = 左半 + 右半 + 最后一次合并
                cost = dp[i][k] + dp[k + 1][j] + arr[i - 1] * arr[k] * arr[j]
                dp[i][j] = min(dp[i][j], cost)

    return dp[1][n - 1]


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # 示例
    print(f"[1,2,3,4,3] 的最小乘法次数: {matrix_chain_multiply([1, 2, 3, 4, 3])}")  # 30
