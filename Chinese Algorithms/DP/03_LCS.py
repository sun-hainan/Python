"""
LCS - 最长公共子序列
==========================================

【问题定义】
找出两个序列中最长的公共子序列。
子序列可以不连续，但相对顺序必须保持。

【应用场景】
- DNA序列比对
- diff文件比较
- 论文查重
"""

def lcs(x, y):
    """
    最长公共子序列
    
    Args:
        x: 第一个序列
        y: 第二个序列
        
    Returns:
        LCS长度
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
