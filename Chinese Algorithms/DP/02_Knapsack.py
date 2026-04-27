# -*- coding: utf-8 -*-

"""

算法实现：DP / 02_Knapsack



本文件实现 02_Knapsack 相关的算法功能。

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





if __name__ == "__main__":

    # 测试: knapsack

    result = knapsack()

    print(result)

