"""
矩阵链乘法 (Matrix Chain Multiplication) - 中文注释版
==========================================

问题定义：
    给定一系列矩阵 (A1, A2, A3, ... An)，
    其中 Ai 的维度是 arr[i-1] × arr[i]。
    确定乘法运算的顺序，使得总乘法次数最少。

重要性质：
    - 矩阵乘法满足结合律：(A*B)*C = A*(B*C)
    - 但乘法次数不同：不同顺序会有不同的计算成本
    - 乘法次数计算：m×p 的矩阵 与 p×n 的矩阵相乘，代价是 m×p×n

应用场景：
    - 计算机图形学中的图像变换
    - 多项式计算优化
    - 宏观经济决策分析
    - 自动驾驶中的位置计算

动态规划思路（O(n³)）：
    定义 dp[i][j] = 矩阵 Ai 到 Aj 相乘的最小乘法次数

    dp[i][j] = min(
        dp[i][k] + dp[k+1][j] + arr[i-1]*arr[k]*arr[j]
        for k in range(i, j)
    )

    解释：在 i 和 j 之间找一个分割点 k，先算左半部分和右半部分，
    再加上最后一步合并的代价

时间复杂度：O(n³)
空间复杂度：O(n²)
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
