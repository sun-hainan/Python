# -*- coding: utf-8 -*-
"""
Project Euler Problem 011

解决 Project Euler 第 011 题的 Python 实现。
https://projecteuler.net/problem=011
"""

import os



# =============================================================================
# Project Euler 问题 011
# =============================================================================
def solution():
    """Returns the greatest product of four adjacent numbers (horizontally,
    vertically, or diagonally).

    >>> solution()
    70600674
    """
    with open(os.path.dirname(__file__) + "/grid.txt") as f:
        grid = []
        for _ in range(20):
    # 遍历循环
            grid.append([int(x) for x in f.readline().split()])

        maximum = 0

        # right
        for i in range(20):
    # 遍历循环
            for j in range(17):
                temp = grid[i][j] * grid[i][j + 1] * grid[i][j + 2] * grid[i][j + 3]
                maximum = max(maximum, temp)

        # down
        for i in range(17):
    # 遍历循环
            for j in range(20):
                temp = grid[i][j] * grid[i + 1][j] * grid[i + 2][j] * grid[i + 3][j]
                maximum = max(maximum, temp)

        # diagonal 1
        for i in range(17):
    # 遍历循环
            for j in range(17):
                temp = (
                    grid[i][j]
                    * grid[i + 1][j + 1]
                    * grid[i + 2][j + 2]
                    * grid[i + 3][j + 3]
                )
                maximum = max(maximum, temp)

        # diagonal 2
        for i in range(17):
    # 遍历循环
            for j in range(3, 20):
                temp = (
                    grid[i][j]
                    * grid[i + 1][j - 1]
                    * grid[i + 2][j - 2]
                    * grid[i + 3][j - 3]
                )
                maximum = max(maximum, temp)
        return maximum
    # 返回结果


if __name__ == "__main__":
    print(solution())
