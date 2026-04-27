# -*- coding: utf-8 -*-

"""

Project Euler Problem 002



解决 Project Euler 第 002 题的 Python 实现。

https://projecteuler.net/problem=002

"""



# =============================================================================

# Project Euler 问题 002

# =============================================================================

def solution(n: int = 4000000) -> int:

    """

    Returns the sum of all even fibonacci sequence elements that are lower

    or equal to n.



    >>> solution(10)

    10

    >>> solution(15)

    10

    >>> solution(2)

    2

    >>> solution(1)

    0

    >>> solution(34)

    44

    """



    if n <= 1:

        return 0

    # 返回结果

    a = 0

    b = 2

    count = 0

    while 4 * b + a <= n:

    # 条件循环

        a, b = b, 4 * b + a

        count += a

    return count + b

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

