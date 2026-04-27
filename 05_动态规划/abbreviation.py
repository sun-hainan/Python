# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / abbreviation



本文件实现 abbreviation 相关的算法功能。

"""



def abbr(a: str, b: str) -> bool:

    # abbr function



    # abbr function

    # abbr 函数实现

    """

    >>> abbr("daBcd", "ABC")

    True

    >>> abbr("dBcd", "ABC")

    False

    """

    n = len(a)

    m = len(b)

    dp = [[False for _ in range(m + 1)] for _ in range(n + 1)]

    dp[0][0] = True

    for i in range(n):

        for j in range(m + 1):

            if dp[i][j]:

                if j < m and a[i].upper() == b[j]:

                    dp[i + 1][j + 1] = True

                if a[i].islower():

                    dp[i + 1][j] = True

    return dp[n][m]





if __name__ == "__main__":

    import doctest



    doctest.testmod()

