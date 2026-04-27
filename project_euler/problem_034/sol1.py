# -*- coding: utf-8 -*-
"""
Project Euler Problem 034

解决 Project Euler 第 034 题的 Python 实现。
https://projecteuler.net/problem=034
"""

from math import factorial

DIGIT_FACTORIAL = {str(d): factorial(d) for d in range(10)}



# =============================================================================
# Project Euler 问题 034
# =============================================================================
def sum_of_digit_factorial(n: int) -> int:
    """
    Returns the sum of the factorial of digits in n
    >>> sum_of_digit_factorial(15)
    121
    >>> sum_of_digit_factorial(0)
    1
    """
    return sum(DIGIT_FACTORIAL[d] for d in str(n))
    # 返回结果


def solution() -> int:
    # solution 函数实现
    """
    Returns the sum of all numbers whose
    sum of the factorials of all digits
    add up to the number itself.
    >>> solution()
    40730
    """
    limit = 7 * factorial(9) + 1
    return sum(i for i in range(3, limit) if sum_of_digit_factorial(i) == i)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
