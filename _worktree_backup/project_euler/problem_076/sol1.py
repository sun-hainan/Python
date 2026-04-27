# -*- coding: utf-8 -*-
"""
Project Euler Problem 076

解决 Project Euler 第 076 题的 Python 实现。
https://projecteuler.net/problem=076
"""

# =============================================================================
# Project Euler 问题 076
# =============================================================================
def solution(m: int = 100) -> int:
    """
    Returns the number of different ways the number m can be written as a
    sum of at least two positive integers.

    >>> solution(100)
    190569291
    >>> solution(50)
    204225
    >>> solution(30)
    5603
    >>> solution(10)
    41
    >>> solution(5)
    6
    >>> solution(3)
    2
    >>> solution(2)
    1
    >>> solution(1)
    0
    """
    memo = [[0 for _ in range(m)] for _ in range(m + 1)]
    for i in range(m + 1):
    # 遍历循环
        memo[i][0] = 1

    for n in range(m + 1):
    # 遍历循环
        for k in range(1, m):
            memo[n][k] += memo[n][k - 1]
            if n > k:
                memo[n][k] += memo[n - k - 1][k]

    return memo[m][m - 1] - 1
    # 返回结果


if __name__ == "__main__":
    print(solution(int(input("Enter a number: ").strip())))
