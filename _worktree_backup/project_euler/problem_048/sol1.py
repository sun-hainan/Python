# -*- coding: utf-8 -*-
"""
Project Euler Problem 048

解决 Project Euler 第 048 题的 Python 实现。
https://projecteuler.net/problem=048
"""

# =============================================================================
# Project Euler 问题 048
# =============================================================================
def solution():
    """
    Returns the last 10 digits of the series, 1^1 + 2^2 + 3^3 + ... + 1000^1000.

    >>> solution()
    '9110846700'
    """
    total = 0
    for i in range(1, 1001):
    # 遍历循环
        total += i**i
    return str(total)[-10:]
    # 返回结果


if __name__ == "__main__":
    print(solution())
