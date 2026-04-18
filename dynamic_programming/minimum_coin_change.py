"""
硬币找零问题 (Coin Change Problem) - 中文注释版
==========================================

问题定义：
    给定 m 种面值的硬币（每种无限枚），和一个金额 n，
    计算凑出金额 n 的不同方法数。

LeetCode/HackerRank 经典题目。

动态规划思路：
    定义 dp[i] = 凑出金额 i 的方法数

    状态转移：
        对于每种硬币 coin_val，遍历所有可能的金额 j
        dp[j] += dp[j - coin_val]

    解释：当我们决定用面值为 coin_val 的硬币时，
    剩余金额 j - coin_val 的方法数就是 dp[j - coin_val]

    base case：dp[0] = 1（凑出金额 0 只有一种方法：什么都不选）

时间复杂度：O(m * n)，m 为硬币种类数，n 为金额
空间复杂度：O(n)
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
