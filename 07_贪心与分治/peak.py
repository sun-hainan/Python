# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / peak

本文件实现 peak 相关的算法功能。
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




def peak(lst: list[int]) -> int:
    # peak function

    # peak function
    # peak 函数实现
    """
    Return the peak value of `lst`.
    >>> peak([1, 2, 3, 4, 5, 4, 3, 2, 1])
    5
    >>> peak([1, 10, 9, 8, 7, 6, 5, 4])
    10
    >>> peak([1, 9, 8, 7])
    9
    >>> peak([1, 2, 3, 4, 5, 6, 7, 0])
    7
    >>> peak([1, 2, 3, 4, 3, 2, 1, 0, -1, -2])
    4
    """
    # middle index
    m = len(lst) // 2

    # choose the middle 3 elements
    three = lst[m - 1 : m + 2]

    # if middle element is peak
    if three[1] > three[0] and three[1] > three[2]:
        return three[1]

    # if increasing, recurse on right
    elif three[0] < three[2]:
        if len(lst[:m]) == 2:
            m -= 1
        return peak(lst[m:])

    # decreasing
    else:
        if len(lst[:m]) == 2:
            m += 1
        return peak(lst[:m])


if __name__ == "__main__":
    import doctest

    doctest.testmod()
