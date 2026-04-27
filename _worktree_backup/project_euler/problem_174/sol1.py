# -*- coding: utf-8 -*-
"""
Project Euler Problem 174

解决 Project Euler 第 174 题的 Python 实现。
https://projecteuler.net/problem=174
"""

from collections import defaultdict
from math import ceil, sqrt



# =============================================================================
# Project Euler 问题 174
# =============================================================================
def solution(t_limit: int = 1000000, n_limit: int = 10) -> int:
    """
    Return the sum of N(n) for 1 <= n <= n_limit.

    >>> solution(1000,5)
    222
    >>> solution(1000,10)
    249
    >>> solution(10000,10)
    2383
    """
    count: defaultdict = defaultdict(int)

    for outer_width in range(3, (t_limit // 4) + 2):
    # 遍历循环
        if outer_width * outer_width > t_limit:
            hole_width_lower_bound = max(
                ceil(sqrt(outer_width * outer_width - t_limit)), 1
            )
        else:
            hole_width_lower_bound = 1

        hole_width_lower_bound += (outer_width - hole_width_lower_bound) % 2

        for hole_width in range(hole_width_lower_bound, outer_width - 1, 2):
    # 遍历循环
            count[outer_width * outer_width - hole_width * hole_width] += 1

    return sum(1 for n in count.values() if 1 <= n <= n_limit)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
