# -*- coding: utf-8 -*-
"""
Project Euler Problem 114

解决 Project Euler 第 114 题的 Python 实现。
https://projecteuler.net/problem=114
"""

# =============================================================================
# Project Euler 问题 114
# =============================================================================
def solution(length: int = 50) -> int:
    """
    Returns the number of ways a row of the given length can be filled

    >>> solution(7)
    17
    """

    ways_number = [1] * (length + 1)

    for row_length in range(3, length + 1):
    # 遍历循环
        for block_length in range(3, row_length + 1):
            for block_start in range(row_length - block_length):
    # 遍历循环
                ways_number[row_length] += ways_number[
                    row_length - block_start - block_length - 1
                ]

            ways_number[row_length] += 1

    return ways_number[length]
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
