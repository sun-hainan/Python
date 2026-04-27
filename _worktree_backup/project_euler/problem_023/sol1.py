# -*- coding: utf-8 -*-
"""
Project Euler Problem 023

解决 Project Euler 第 023 题的 Python 实现。
https://projecteuler.net/problem=023
"""

# =============================================================================
# Project Euler 问题 023
# =============================================================================
def solution(limit=28123):
    """
    Finds the sum of all the positive integers which cannot be written as
    the sum of two abundant numbers
    as described by the statement above.

    >>> solution()
    4179871
    """
    sum_divs = [1] * (limit + 1)

    for i in range(2, int(limit**0.5) + 1):
    # 遍历循环
        sum_divs[i * i] += i
        for k in range(i + 1, limit // i + 1):
    # 遍历循环
            sum_divs[k * i] += k + i

    abundants = set()
    res = 0

    for n in range(1, limit + 1):
    # 遍历循环
        if sum_divs[n] > n:
            abundants.add(n)

        if not any((n - a in abundants) for a in abundants):
            res += n

    return res
    # 返回结果


if __name__ == "__main__":
    print(solution())
