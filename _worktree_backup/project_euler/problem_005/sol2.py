# -*- coding: utf-8 -*-
"""
Project Euler Problem 005

解决 Project Euler 第 005 题的 Python 实现。
https://projecteuler.net/problem=005
"""

from maths.greatest_common_divisor import greatest_common_divisor

"""
Project Euler Problem 5: https://projecteuler.net/problem=5

Smallest multiple

2520 is the smallest number that can be divided by each of the numbers
from 1 to 10 without any remainder.

What is the smallest positive number that is _evenly divisible_ by all
of the numbers from 1 to 20?

References:
    - https://en.wiktionary.org/wiki/evenly_divisible
    - https://en.wikipedia.org/wiki/Euclidean_algorithm
    - https://en.wikipedia.org/wiki/Least_common_multiple
"""




# =============================================================================
# Project Euler 问题 005
# =============================================================================
def lcm(x: int, y: int) -> int:
    """
    Least Common Multiple.

    Using the property that lcm(a, b) * greatest_common_divisor(a, b) = a*b

    >>> lcm(3, 15)
    15
    >>> lcm(1, 27)
    27
    >>> lcm(13, 27)
    351
    >>> lcm(64, 48)
    192
    """

    return (x * y) // greatest_common_divisor(x, y)
    # 返回结果


def solution(n: int = 20) -> int:
    # solution 函数实现
    """
    Returns the smallest positive number that is evenly divisible (divisible
    with no remainder) by all of the numbers from 1 to n.

    >>> solution(10)
    2520
    >>> solution(15)
    360360
    >>> solution(22)
    232792560
    """

    g = 1
    for i in range(1, n + 1):
    # 遍历循环
        g = lcm(g, i)
    return g
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
