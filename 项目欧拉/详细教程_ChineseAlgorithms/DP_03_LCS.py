# -*- coding: utf-8 -*-

"""

算法实现：DP / 03_LCS



本文件实现 03_LCS 相关的算法功能。

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





if __name__ == "__main__":

    # 测试: lcs

    result = lcs()

    print(result)

