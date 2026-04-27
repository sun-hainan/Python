# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / longest_increasing_subsequence_iterative

本文件实现 longest_increasing_subsequence_iterative 相关的算法功能。
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



import copy


def longest_subsequence(array: list[int]) -> list[int]:
    # longest_subsequence function

    # longest_subsequence function
    # longest_subsequence 函数实现
    """
    Some examples

    >>> longest_subsequence([10, 22, 9, 33, 21, 50, 41, 60, 80])
    [10, 22, 33, 50, 60, 80]
    >>> longest_subsequence([4, 8, 7, 5, 1, 12, 2, 3, 9])
    [1, 2, 3, 9]
    >>> longest_subsequence([9, 8, 7, 6, 5, 7])
    [7, 7]
    >>> longest_subsequence([28, 26, 12, 23, 35, 39])
    [12, 23, 35, 39]
    >>> longest_subsequence([1, 1, 1])
    [1, 1, 1]
    >>> longest_subsequence([])
    []
    """
    n = len(array)
    # The longest increasing subsequence ending at array[i]
    longest_increasing_subsequence = []
    for i in range(n):
        longest_increasing_subsequence.append([array[i]])

    for i in range(1, n):
        for prev in range(i):
            # If array[prev] is less than or equal to array[i], then
            # longest_increasing_subsequence[prev] + array[i]
            # is a valid increasing subsequence

            # longest_increasing_subsequence[i] is only set to
            # longest_increasing_subsequence[prev] + array[i] if the length is longer.

            if array[prev] <= array[i] and len(
                longest_increasing_subsequence[prev]
            ) + 1 > len(longest_increasing_subsequence[i]):
                longest_increasing_subsequence[i] = copy.copy(
                    longest_increasing_subsequence[prev]
                )
                longest_increasing_subsequence[i].append(array[i])

    result: list[int] = []
    for i in range(n):
        if len(longest_increasing_subsequence[i]) > len(result):
            result = longest_increasing_subsequence[i]

    return result


if __name__ == "__main__":
    import doctest

    doctest.testmod()
