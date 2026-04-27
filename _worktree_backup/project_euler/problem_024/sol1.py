# -*- coding: utf-8 -*-
"""
Project Euler Problem 024

解决 Project Euler 第 024 题的 Python 实现。
https://projecteuler.net/problem=024
"""

from itertools import permutations



# =============================================================================
# Project Euler 问题 024
# =============================================================================
def solution():
    """Returns the millionth lexicographic permutation of the digits 0, 1, 2,
    3, 4, 5, 6, 7, 8 and 9.

    >>> solution()
    '2783915460'
    """
    result = list(map("".join, permutations("0123456789")))
    return result[999999]
    # 返回结果


if __name__ == "__main__":
    print(solution())
