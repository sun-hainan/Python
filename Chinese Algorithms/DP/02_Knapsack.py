"""
Knapsack - 背包问题
==========================================

【问题定义】
给定n个物品，每个有重量wt[i]和价值val[i]，
在不超过背包容量W的情况下，选择物品使总价值最大。

【应用场景】
- 资源分配
- 项目选择
- 投资组合优化
"""

def knapsack(W, weights, values, n):
    """
    0-1背包问题动态规划解法
    
    Args:
        W: 背包容量
        weights: 物品重量列表
        values: 物品价值列表
        n: 物品数量
        
    Returns:
        最大价值
    """
    # dp[i][w] = 前i个物品在容量w下的最大价值
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(W + 1):
            if weights[i - 1] <= w:
                # 选或不选第i个物品，取较大值
                dp[i][w] = max(
                    values[i - 1] + dp[i - 1][w - weights[i - 1]],
                    dp[i - 1][w]
                )
            else:
                # 不能选第i个物品
                dp[i][w] = dp[i - 1][w]
    
    return dp[n][W]


# ---------- LCS ----------
FILES['Chinese Algorithms/DP/03_LCS.py'] = 
LCS - 最长公共子序列
==========================================

【问题定义】
找出两个字符串/序列中，最长的公共子序列。
子序列可以不连续，但相对顺序必须保持。

【应用场景】
- DNA序列比对
- diff文件比较
- 论文查重
