# -*- coding: utf-8 -*-
"""
Project Euler Problem 002

解决 Project Euler 第 002 题的 Python 实现。
https://projecteuler.net/problem=002
"""

# =============================================================================
# Project Euler 问题 002
# =============================================================================
def solution(n: int = 4000000) -> int:
    """
    Returns the sum of all even fibonacci sequence elements that are lower
    or equal to n.

    >>> solution(10)
    10
    >>> solution(15)
    10
    >>> solution(2)
    2
    >>> solution(1)
    0
    >>> solution(34)
    44
    """

    even_fibs = []
    a, b = 0, 1
    while b <= n:
    # 条件循环
        if b % 2 == 0:
            even_fibs.append(b)
        a, b = b, a + b
    return sum(even_fibs)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
