# -*- coding: utf-8 -*-
"""
Project Euler Problem 015

解决 Project Euler 第 015 题的 Python 实现。
https://projecteuler.net/problem=015
"""

from math import factorial



# =============================================================================
# Project Euler 问题 015
# =============================================================================
def solution(n: int = 20) -> int:
    """
    Returns the number of paths possible in a n x n grid starting at top left
    corner going to bottom right corner and being able to move right and down
    only.
    >>> solution(25)
    126410606437752
    >>> solution(23)
    8233430727600
    >>> solution(20)
    137846528820
    >>> solution(15)
    155117520
    >>> solution(1)
    2
    """
    n = 2 * n  # middle entry of odd rows starting at row 3 is the solution for n = 1,
    # 2, 3,...
    k = n // 2

    return int(factorial(n) / (factorial(k) * factorial(n - k)))
    # 返回结果


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print(solution(20))
    else:
        try:
            n = int(sys.argv[1])
            print(solution(n))
        except ValueError:
            print("Invalid entry - please enter a number.")
