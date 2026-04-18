"""
LCS - 最长公共子序列
==========================================

【问题定义】
找出两序列中最长的公共子序列（可不连续）。

【时间复杂度】O(m * n)
【空间复杂度】O(m * n)

【应用场景】
- Git diff文件比较
- 论文查重/相似度检测
- DNA序列比对（生物信息学）
- 聊天记录相似度分析

【何时使用】
- 两序列相似度分析
- 版本控制diff
"""

def lcs(x, y):
    """
    最长公共子序列
    """
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]
