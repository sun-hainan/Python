# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / minimum_coin_change



本文件实现 minimum_coin_change 相关的算法功能。

"""



def dp_count(s, n):

    """

    硬币找零 - DP 解法



    参数:

        s: 硬币面值列表，如 [1, 2, 3]

        n: 目标金额



    返回:

        凑出金额 n 的方法数



    示例:

        >>> dp_count([1, 2, 3], 4)

        4

        # 4 = {1,1,1,1}, {1,1,2}, {1,3}, {2,2}



        >>> dp_count([1, 2, 3], 7)

        8

        >>> dp_count([2, 5, 3, 6], 10)

        5

        >>> dp_count([10], 99)

        0

        >>> dp_count([4, 5, 6], 0)

        1

    """

    if n < 0:

        return 0



    # dp[i] = 凑出金额 i 的方法数

    table = [0] * (n + 1)



    # base case：凑出金额 0 只有一种方法（什么都不选）

    table[0] = 1



    # 遍历每种硬币

    for coin_val in s:

        # 用当前硬币能凑出的金额

        for j in range(coin_val, n + 1):

            table[j] += table[j - coin_val]



    return table[n]





if __name__ == "__main__":

    import doctest

    doctest.testmod()

