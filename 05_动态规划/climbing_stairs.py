# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / climbing_stairs



本文件实现 climbing_stairs 相关的算法功能。

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

