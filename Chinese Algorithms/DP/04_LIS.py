"""
LIS - 最长递增子序列
==========================================

【问题定义】
找序列中最长的递增子序列（可不连续）。

【时间复杂度】O(n^2)
【空间复杂度】O(n)

【应用场景】
- 股票最长上涨区间分析
- 合唱队形（最多能选几人）
- 套娃信封问题
- 活动冲突安排

【何时使用】
- 最长递增/递减序列问题
- 套娃类问题
"""

def lis(arr):
    """
    最长递增子序列
    """
    if not arr:
        return 0
    n = len(arr)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if arr[j] < arr[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)
