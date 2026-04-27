# -*- coding: utf-8 -*-
"""
Project Euler Problem 173

解决 Project Euler 第 173 题的 Python 实现。
https://projecteuler.net/problem=173
"""

from math import ceil, sqrt



# =============================================================================
# Project Euler 问题 173
# =============================================================================
def solution(limit: int = 1000000) -> int:
    """
    Return the number of different square laminae that can be formed using up to
    one million tiles.
    >>> solution(100)
    41
    """
    answer = 0

    for outer_width in range(3, (limit // 4) + 2):
    # 遍历循环
        if outer_width**2 > limit:
            hole_width_lower_bound = max(ceil(sqrt(outer_width**2 - limit)), 1)
        else:
            hole_width_lower_bound = 1
        if (outer_width - hole_width_lower_bound) % 2:
            hole_width_lower_bound += 1

        answer += (outer_width - hole_width_lower_bound - 2) // 2 + 1

    return answer
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
