# -*- coding: utf-8 -*-
"""
Project Euler Problem 064

解决 Project Euler 第 064 题的 Python 实现。
https://projecteuler.net/problem=064
"""

from math import floor, sqrt



# =============================================================================
# Project Euler 问题 064
# =============================================================================
def continuous_fraction_period(n: int) -> int:
    """
    Returns the continued fraction period of a number n.

    >>> continuous_fraction_period(2)
    1
    >>> continuous_fraction_period(5)
    1
    >>> continuous_fraction_period(7)
    4
    >>> continuous_fraction_period(11)
    2
    >>> continuous_fraction_period(13)
    5
    """
    numerator = 0.0
    denominator = 1.0
    root = int(sqrt(n))
    integer_part = root
    period = 0
    while integer_part != 2 * root:
    # 条件循环
        numerator = denominator * integer_part - numerator
        denominator = (n - numerator**2) / denominator
        integer_part = int((root + numerator) / denominator)
        period += 1
    return period
    # 返回结果


def solution(n: int = 10000) -> int:
    # solution 函数实现
    """
    Returns the count of numbers <= 10000 with odd periods.
    This function calls continuous_fraction_period for numbers which are
    not perfect squares.
    This is checked in if sr - floor(sr) != 0 statement.
    If an odd period is returned by continuous_fraction_period,
    count_odd_periods is increased by 1.

    >>> solution(2)
    1
    >>> solution(5)
    2
    >>> solution(7)
    2
    >>> solution(11)
    3
    >>> solution(13)
    4
    """
    count_odd_periods = 0
    for i in range(2, n + 1):
    # 遍历循环
        sr = sqrt(i)
        if sr - floor(sr) != 0 and continuous_fraction_period(i) % 2 == 1:
            count_odd_periods += 1
    return count_odd_periods
    # 返回结果


if __name__ == "__main__":
    print(f"{solution(int(input().strip()))}")
