"""
爬楼梯问题 (Climbing Stairs) - 中文注释版
==========================================

问题定义（LeetCode #70）：
    假设你正在爬楼梯，需要 n 阶才能到达顶部。
    每次你可以爬 1 或 2 个台阶。
    问有多少种不同的方法可以爬到顶部？

示例：
    输入: 3
    输出: 3
    解释: 有三种方法可以爬到顶部:
         1. 1 步 + 1 步 + 1 步
         2. 1 步 + 2 步
         3. 2 步 + 1 步

动态规划思路：
    定义 dp[i] = 爬到第 i 阶的方法数

    状态转移：
        dp[i] = dp[i-1] + dp[i-2]
        解释：第 i 阶只能从第 i-1 阶爬 1 步，或从第 i-2 阶爬 2 步

    初始条件：
        dp[0] = 1（0 阶有一种方式：什么都不做）
        dp[1] = 1（1 阶只有一种：爬 1 步）
        dp[2] = 2（2 阶有两种：1+1 或 2）

    这实际上是斐波那契数列！

时间复杂度：O(n)
空间复杂度：O(1)（只保存前两个状态）
"""


def climb_stairs(number_of_steps: int) -> int:
    """
    爬楼梯 - DP 解法

    参数:
        number_of_steps: 楼梯的总阶数

    返回:
        爬到顶部的方法数

    示例:
        >>> climb_stairs(3)
        3
        >>> climb_stairs(1)
        1
        >>> climb_stairs(10)
        89
    """
    assert isinstance(number_of_steps, int) and number_of_steps > 0, (
        f"number_of_steps 必须是正整数，输入值: {number_of_steps}"
    )

    if number_of_steps == 1:
        return 1

    # 空间优化：只用两个变量
    previous, current = 1, 1  # previous=dp[i-2], current=dp[i-1]
    for _ in range(number_of_steps - 1):
        current, previous = current + previous, current

    return current


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    print(f"爬 3 阶楼梯的方法数: {climb_stairs(3)}")  # 3
    print(f"爬 10 阶楼梯的方法数: {climb_stairs(10)}")  # 89
