"""
Knapsack - 背包问题
==========================================

【问题定义】
给定物品的重量和价值，在容量限制下选择最大价值。

【时间复杂度】O(n * W)
【空间复杂度】O(n * W)

【应用场景】
- 旅行行李打包（限额重量内最大化价值）
- 双11凑单（预算内买最多商品）
- 项目投资选择
- 资源分配优化

【何时使用】
- 有容量/预算限制的组合优化
"""

def knapsack(W, weights, values, n):
    """
    0-1背包问题
    """
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(W + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(values[i - 1] + dp[i - 1][w - weights[i - 1]], dp[i - 1][w])
            else:
                dp[i][w] = dp[i - 1][w]
    return dp[n][W]
