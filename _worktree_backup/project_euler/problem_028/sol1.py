# -*- coding: utf-8 -*-
"""
Project Euler Problem 028

解决 Project Euler 第 028 题的 Python 实现。
https://projecteuler.net/problem=028
"""

from math import ceil



# =============================================================================
# Project Euler 问题 028
# =============================================================================
def solution(n: int = 1001) -> int:
    """Returns the sum of the numbers on the diagonals in a n by n spiral
    formed in the same way.

    >>> solution(1001)
    669171001
    >>> solution(500)
    82959497
    >>> solution(100)
    651897
    >>> solution(50)
    79697
    >>> solution(10)
    537
    """
    total = 1

    for i in range(1, ceil(n / 2.0)):
    # 遍历循环
        odd = 2 * i + 1
        even = 2 * i
        total = total + 4 * odd**2 - 6 * even

    return total
    # 返回结果


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print(solution())
    else:
        try:
            n = int(sys.argv[1])
            print(solution(n))
        except ValueError:
            print("Invalid entry - please enter a number")
