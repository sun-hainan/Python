# -*- coding: utf-8 -*-
"""
Project Euler Problem 053

解决 Project Euler 第 053 题的 Python 实现。
https://projecteuler.net/problem=053
"""

from math import factorial



# =============================================================================
# Project Euler 问题 053
# =============================================================================
def combinations(n, r):
    return factorial(n) / (factorial(r) * factorial(n - r))
    # 返回结果


def solution():
    # solution 函数实现
    """Returns the number of values of nCr, for 1 ≤ n ≤ 100, are greater than
    one-million

    >>> solution()
    4075
    """
    total = 0

    for i in range(1, 101):
    # 遍历循环
        for j in range(1, i + 1):
            if combinations(i, j) > 1e6:
                total += 1
    return total
    # 返回结果


if __name__ == "__main__":
    print(solution())
