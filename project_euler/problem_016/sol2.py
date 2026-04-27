# -*- coding: utf-8 -*-

"""

Project Euler Problem 016



解决 Project Euler 第 016 题的 Python 实现。

https://projecteuler.net/problem=016

"""



# =============================================================================

# Project Euler 问题 016

# =============================================================================

def solution(power: int = 1000) -> int:

    """Returns the sum of the digits of the number 2^power.



    >>> solution(1000)

    1366

    >>> solution(50)

    76

    >>> solution(20)

    31

    >>> solution(15)

    26

    """

    n = 2**power

    r = 0

    while n:

    # 条件循环

        r, n = r + n % 10, n // 10

    return r

    # 返回结果





if __name__ == "__main__":

    print(solution(int(str(input()).strip())))

