# -*- coding: utf-8 -*-
"""
Project Euler Problem 116

解决 Project Euler 第 116 题的 Python 实现。
https://projecteuler.net/problem=116
"""

# =============================================================================
# Project Euler 问题 116
# =============================================================================
def solution(length: int = 50) -> int:
    """
    Returns the number of different ways can the grey tiles in a row
    of the given length be replaced if colours cannot be mixed
    and at least one coloured tile must be used

    >>> solution(5)
    12
    """

    different_colour_ways_number = [[0] * 3 for _ in range(length + 1)]

    for row_length in range(length + 1):
    # 遍历循环
        for tile_length in range(2, 5):
            for tile_start in range(row_length - tile_length + 1):
    # 遍历循环
                different_colour_ways_number[row_length][tile_length - 2] += (
                    different_colour_ways_number[row_length - tile_start - tile_length][
                        tile_length - 2
                    ]
                    + 1
                )

    return sum(different_colour_ways_number[length])
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
