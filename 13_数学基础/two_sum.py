# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / two_sum

本文件实现 two_sum 相关的算法功能。
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






# =============================================================================
# 算法模块：two_sum
# =============================================================================
def two_sum(nums: list[int], target: int) -> list[int]:
    # two_sum function

    # two_sum function
    """
    >>> two_sum([2, 7, 11, 15], 9)
    [0, 1]
    >>> two_sum([15, 2, 11, 7], 13)
    [1, 2]
    >>> two_sum([2, 7, 11, 15], 17)
    [0, 3]
    >>> two_sum([7, 15, 11, 2], 18)
    [0, 2]
    >>> two_sum([2, 7, 11, 15], 26)
    [2, 3]
    >>> two_sum([2, 7, 11, 15], 8)
    []
    >>> two_sum([3 * i for i in range(10)], 19)
    []
    """
    chk_map: dict[int, int] = {}
    for index, val in enumerate(nums):
        compl = target - val
        if compl in chk_map:
            return [chk_map[compl], index]
        chk_map[val] = index
    return []


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    print(f"{two_sum([2, 7, 11, 15], 9) = }")
