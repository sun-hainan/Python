# -*- coding: utf-8 -*-
"""
Project Euler Problem 015

解决 Project Euler 第 015 题的 Python 实现。
https://projecteuler.net/problem=015
"""

# =============================================================================
# Project Euler 问题 015
# =============================================================================
def solution(n: int = 20) -> int:
    """
    Solve by explicitly counting the paths with dynamic programming.

    >>> solution(6)
    924
    >>> solution(2)
    6
    >>> solution(1)
    2
    """

    counts = [[1 for _ in range(n + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
    # 遍历循环
        for j in range(1, n + 1):
            counts[i][j] = counts[i - 1][j] + counts[i][j - 1]

    return counts[n][n]
    # 返回结果


if __name__ == "__main__":
    print(solution())
