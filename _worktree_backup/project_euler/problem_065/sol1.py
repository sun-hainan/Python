# -*- coding: utf-8 -*-
"""
Project Euler Problem 065

解决 Project Euler 第 065 题的 Python 实现。
https://projecteuler.net/problem=065
"""

# =============================================================================
# Project Euler 问题 065
# =============================================================================
def sum_digits(num: int) -> int:
    """
    Returns the sum of every digit in num.

    >>> sum_digits(1)
    1
    >>> sum_digits(12345)
    15
    >>> sum_digits(999001)
    28
    """
    digit_sum = 0
    while num > 0:
    # 条件循环
        digit_sum += num % 10
        num //= 10
    return digit_sum
    # 返回结果


def solution(max_n: int = 100) -> int:
    # solution 函数实现
    """
    Returns the sum of the digits in the numerator of the max-th convergent of
    the continued fraction for e.

    >>> solution(9)
    13
    >>> solution(10)
    17
    >>> solution(50)
    91
    """
    pre_numerator = 1
    cur_numerator = 2

    for i in range(2, max_n + 1):
    # 遍历循环
        temp = pre_numerator
        e_cont = 2 * i // 3 if i % 3 == 0 else 1
        pre_numerator = cur_numerator
        cur_numerator = e_cont * pre_numerator + temp

    return sum_digits(cur_numerator)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
