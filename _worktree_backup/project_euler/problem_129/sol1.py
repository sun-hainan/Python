# -*- coding: utf-8 -*-

"""

Project Euler Problem 129



解决 Project Euler 第 129 题的 Python 实现。

https://projecteuler.net/problem=129

"""



# =============================================================================

# Project Euler 问题 129

# =============================================================================

def least_divisible_repunit(divisor: int) -> int:

    """

    Return the least value k such that the Repunit of length k is divisible by divisor.

    >>> least_divisible_repunit(7)

    6

    >>> least_divisible_repunit(41)

    5

    >>> least_divisible_repunit(1234567)

    34020

    """

    if divisor % 5 == 0 or divisor % 2 == 0:

        return 0

    # 返回结果

    repunit = 1

    repunit_index = 1

    while repunit:

    # 条件循环

        repunit = (10 * repunit + 1) % divisor

        repunit_index += 1

    return repunit_index

    # 返回结果





def solution(limit: int = 1000000) -> int:

    # solution 函数实现

    """

    Return the least value of n for which least_divisible_repunit(n)

    first exceeds limit.

    >>> solution(10)

    17

    >>> solution(100)

    109

    >>> solution(1000)

    1017

    """

    divisor = limit - 1

    if divisor % 2 == 0:

        divisor += 1

    while least_divisible_repunit(divisor) <= limit:

    # 条件循环

        divisor += 2

    return divisor

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

