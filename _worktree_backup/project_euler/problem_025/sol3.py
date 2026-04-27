# -*- coding: utf-8 -*-
"""
Project Euler Problem 025

解决 Project Euler 第 025 题的 Python 实现。
https://projecteuler.net/problem=025
"""

# =============================================================================
# Project Euler 问题 025
# =============================================================================
def solution(n: int = 1000) -> int:
    """Returns the index of the first term in the Fibonacci sequence to contain
    n digits.

    >>> solution(1000)
    4782
    >>> solution(100)
    476
    >>> solution(50)
    237
    >>> solution(3)
    12
    """
    f1, f2 = 1, 1
    index = 2
    while True:
    # 条件循环
        i = 0
        f = f1 + f2
        f1, f2 = f2, f
        index += 1
        for _ in str(f):
    # 遍历循环
            i += 1
        if i == n:
            break
    return index
    # 返回结果


if __name__ == "__main__":
    print(solution(int(str(input()).strip())))
