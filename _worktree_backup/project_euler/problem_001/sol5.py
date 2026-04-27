# -*- coding: utf-8 -*-
"""
Project Euler Problem 001

解决 Project Euler 第 001 题的 Python 实现。
https://projecteuler.net/problem=001
"""

# =============================================================================
# Project Euler 问题 001
# =============================================================================
def solution(n: int = 1000) -> int:
    """
    Returns the sum of all the multiples of 3 or 5 below n.
    A straightforward pythonic solution using list comprehension.

    >>> solution(3)
    0
    >>> solution(4)
    3
    >>> solution(10)
    23
    >>> solution(600)
    83700
    """

    return sum(i for i in range(n) if i % 3 == 0 or i % 5 == 0)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
