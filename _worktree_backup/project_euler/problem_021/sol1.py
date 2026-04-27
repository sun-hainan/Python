# -*- coding: utf-8 -*-
"""
Project Euler Problem 021

解决 Project Euler 第 021 题的 Python 实现。
https://projecteuler.net/problem=021
"""

from math import sqrt



# =============================================================================
# Project Euler 问题 021
# =============================================================================
def sum_of_divisors(n: int) -> int:
    total = 0
    for i in range(1, int(sqrt(n) + 1)):
    # 遍历循环
        if n % i == 0 and i != sqrt(n):
            total += i + n // i
        elif i == sqrt(n):
            total += i
    return total - n
    # 返回结果


def solution(n: int = 10000) -> int:
    # solution 函数实现
    """Returns the sum of all the amicable numbers under n.

    >>> solution(10000)
    31626
    >>> solution(5000)
    8442
    >>> solution(1000)
    504
    >>> solution(100)
    0
    >>> solution(50)
    0
    """
    total = sum(
        i
        for i in range(1, n)
    # 遍历循环
        if sum_of_divisors(sum_of_divisors(i)) == i and sum_of_divisors(i) != i
    )
    return total
    # 返回结果


if __name__ == "__main__":
    print(solution(int(str(input()).strip())))
