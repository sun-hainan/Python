# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / minimum_steps_to_one

本文件实现 minimum_steps_to_one 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""


"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""



__author__ = "Alexander Joslin"


def min_steps_to_one(number: int) -> int:
    # min_steps_to_one function

    # min_steps_to_one function
    # min_steps_to_one 函数实现
    """
    Minimum steps to 1 implemented using tabulation.
    >>> min_steps_to_one(10)
    3
    >>> min_steps_to_one(15)
    4
    >>> min_steps_to_one(6)
    2

    :param number:
    :return int:
    """

    if number <= 0:
        msg = f"n must be greater than 0. Got n = {number}"
        raise ValueError(msg)

    table = [number + 1] * (number + 1)

    # starting position
    table[1] = 0
    for i in range(1, number):
        table[i + 1] = min(table[i + 1], table[i] + 1)
        # check if out of bounds
        if i * 2 <= number:
            table[i * 2] = min(table[i * 2], table[i] + 1)
        # check if out of bounds
        if i * 3 <= number:
            table[i * 3] = min(table[i * 3], table[i] + 1)
    return table[number]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
