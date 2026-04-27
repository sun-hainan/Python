# -*- coding: utf-8 -*-
"""
Project Euler Problem 073

解决 Project Euler 第 073 题的 Python 实现。
https://projecteuler.net/problem=073
"""

from math import gcd



# =============================================================================
# Project Euler 问题 073
# =============================================================================
def solution(max_d: int = 12_000) -> int:
    """
    Returns number of fractions lie between 1/3 and 1/2 in the sorted set
    of reduced proper fractions for d ≤ max_d

    >>> solution(4)
    0

    >>> solution(5)
    1

    >>> solution(8)
    3
    """

    fractions_number = 0
    for d in range(max_d + 1):
    # 遍历循环
        n_start = d // 3 + 1
        n_step = 1
        if d % 2 == 0:
            n_start += 1 - n_start % 2
            n_step = 2
        for n in range(n_start, (d + 1) // 2, n_step):
    # 遍历循环
            if gcd(n, d) == 1:
                fractions_number += 1
    return fractions_number
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
