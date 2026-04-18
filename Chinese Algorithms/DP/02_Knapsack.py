"""
Knapsack - 背包问题
==========================================

【问题定义】
给定n个物品，每个有重量wt[i]和价值val[i]，
在不超过背包容量W的情况下，选择物品使总价值最大。

【时间复杂度】O(n * W)
【空间复杂度】O(n * W)

【应用场景】
- 电商促销组合优惠
- 旅行行李打包
- 项目投资选择
- 资源分配优化

【何时使用】
- 组合优化问题
- 有容量/预算限制的选择
- 投资组合优化
- 资源有限的项目选择

【实际案例】
# 旅行打包行李（背包容量有限）
items = [
    {"name": "护照", "weight": 0.2, "value": 100},
    {"name": "电脑", "weight": 2.0, "value": 80},
    {"name": "衣服", "weight": 3.0, "value": 30},
    {"name": "相机", "weight": 1.5, "value": 60}
]
# 行李限额10kg，如何打包价值最高？

# 双11购物凑单（预算有限，如何凑满减最大）
products = [
    {"name": "面膜", "price": 50, "value": 5},
    {"name": "精华", "price": 200, "value": 15},
    {"name": "面霜", "price": 150, "value": 10}
]
# 预算500元，如何凑单最优惠？
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
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(W + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(
                    values[i - 1] + dp[i - 1][w - weights[i - 1]],
                    dp[i - 1][w]
                )
            else:
                dp[i][w] = dp[i - 1][w]
    
    return dp[n][W]
