# -*- coding: utf-8 -*-
"""
Project Euler Problem 072

解决 Project Euler 第 072 题的 Python 实现。
https://projecteuler.net/problem=072
"""

import numpy as np



# =============================================================================
# Project Euler 问题 072
# =============================================================================
def solution(limit: int = 1_000_000) -> int:
    """
    Returns an integer, the solution to the problem
    >>> solution(10)
    31
    >>> solution(100)
    3043
    >>> solution(1_000)
    304191
    """

    # generating an array from -1 to limit
    phi = np.arange(-1, limit)

    for i in range(2, limit + 1):
    # 遍历循环
        if phi[i] == i - 1:
            ind = np.arange(2 * i, limit + 1, i)  # indexes for selection
            phi[ind] -= phi[ind] // i

    return int(np.sum(phi[2 : limit + 1]))
    # 返回结果


if __name__ == "__main__":
    print(solution())
