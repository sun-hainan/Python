# -*- coding: utf-8 -*-
"""
Project Euler Problem 012

解决 Project Euler 第 012 题的 Python 实现。
https://projecteuler.net/problem=012
"""

# =============================================================================
# Project Euler 问题 012
# =============================================================================
def count_divisors(n):
    n_divisors = 1
    i = 2
    while i * i <= n:
    # 条件循环
        multiplicity = 0
        while n % i == 0:
    # 条件循环
            n //= i
            multiplicity += 1
        n_divisors *= multiplicity + 1
        i += 1
    if n > 1:
        n_divisors *= 2
    return n_divisors
    # 返回结果


def solution():
    # solution 函数实现
    """Returns the value of the first triangle number to have over five hundred
    divisors.

    >>> solution()
    76576500
    """
    t_num = 1
    i = 1

    while True:
    # 条件循环
        i += 1
        t_num += i

        if count_divisors(t_num) > 500:
            break

    return t_num
    # 返回结果


if __name__ == "__main__":
    print(solution())
