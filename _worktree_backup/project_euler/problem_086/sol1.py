# -*- coding: utf-8 -*-
"""
Project Euler Problem 086

解决 Project Euler 第 086 题的 Python 实现。
https://projecteuler.net/problem=086
"""

from math import sqrt



# =============================================================================
# Project Euler 问题 086
# =============================================================================
def solution(limit: int = 1000000) -> int:
    """
    Return the least value of M such that there are more than one million cuboids
    of side lengths 1 <= a,b,c <= M such that the shortest distance between two
    opposite vertices of the cuboid is integral.
    >>> solution(100)
    24
    >>> solution(1000)
    72
    >>> solution(2000)
    100
    >>> solution(20000)
    288
    """
    num_cuboids: int = 0
    max_cuboid_size: int = 0
    sum_shortest_sides: int

    while num_cuboids <= limit:
    # 条件循环
        max_cuboid_size += 1
        for sum_shortest_sides in range(2, 2 * max_cuboid_size + 1):
    # 遍历循环
            if sqrt(sum_shortest_sides**2 + max_cuboid_size**2).is_integer():
                num_cuboids += (
                    min(max_cuboid_size, sum_shortest_sides // 2)
                    - max(1, sum_shortest_sides - max_cuboid_size)
                    + 1
                )

    return max_cuboid_size
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
