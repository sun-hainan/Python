# -*- coding: utf-8 -*-
"""
算法实现：DP / 04_LIS

本文件实现 04_LIS 相关的算法功能。
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


if __name__ == "__main__":
    # 测试: lis
    result = lis()
    print(result)
