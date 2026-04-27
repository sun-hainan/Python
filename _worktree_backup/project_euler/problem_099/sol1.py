# -*- coding: utf-8 -*-

"""

Project Euler Problem 099



解决 Project Euler 第 099 题的 Python 实现。

https://projecteuler.net/problem=099

"""



import os

from math import log10







# =============================================================================

# Project Euler 问题 099

# =============================================================================

def solution(data_file: str = "base_exp.txt") -> int:

    """

    >>> solution()

    709

    """

    largest: float = 0

    result = 0

    for i, line in enumerate(open(os.path.join(os.path.dirname(__file__), data_file))):

    # 遍历循环

        a, x = list(map(int, line.split(",")))

        if x * log10(a) > largest:

            largest = x * log10(a)

            result = i + 1

    return result

    # 返回结果





if __name__ == "__main__":

    print(solution())

