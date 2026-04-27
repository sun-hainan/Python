# -*- coding: utf-8 -*-
"""
Project Euler Problem 081

解决 Project Euler 第 081 题的 Python 实现。
https://projecteuler.net/problem=081
"""

import os



# =============================================================================
# Project Euler 问题 081
# =============================================================================
def solution(filename: str = "matrix.txt") -> int:
    """
    Returns the minimal path sum from the top left to the bottom right of the matrix.
    >>> solution()
    427337
    """
    with open(os.path.join(os.path.dirname(__file__), filename)) as in_file:
        data = in_file.read()

    grid = [[int(cell) for cell in row.split(",")] for row in data.strip().splitlines()]
    dp = [[0 for cell in row] for row in grid]
    n = len(grid[0])

    dp = [[0 for i in range(n)] for j in range(n)]
    dp[0][0] = grid[0][0]
    for i in range(1, n):
    # 遍历循环
        dp[0][i] = grid[0][i] + dp[0][i - 1]
    for i in range(1, n):
    # 遍历循环
        dp[i][0] = grid[i][0] + dp[i - 1][0]

    for i in range(1, n):
    # 遍历循环
        for j in range(1, n):
            dp[i][j] = grid[i][j] + min(dp[i - 1][j], dp[i][j - 1])

    return dp[-1][-1]
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
