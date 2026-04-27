# -*- coding: utf-8 -*-
"""
Project Euler Problem 115

解决 Project Euler 第 115 题的 Python 实现。
https://projecteuler.net/problem=115
"""

from itertools import count



# =============================================================================
# Project Euler 问题 115
# =============================================================================
def solution(min_block_length: int = 50) -> int:
    """
    Returns for given minimum block length the least value of n
    for which the fill-count function first exceeds one million
    # 遍历循环

    >>> solution(3)
    30

    >>> solution(10)
    57
    """

    fill_count_functions = [1] * min_block_length

    for n in count(min_block_length):
    # 遍历循环
        fill_count_functions.append(1)

        for block_length in range(min_block_length, n + 1):
    # 遍历循环
            for block_start in range(n - block_length):
                fill_count_functions[n] += fill_count_functions[
                    n - block_start - block_length - 1
                ]

            fill_count_functions[n] += 1

        if fill_count_functions[n] > 1_000_000:
            break

    return n
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
