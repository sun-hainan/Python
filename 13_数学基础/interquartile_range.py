# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / interquartile_range

本文件实现 interquartile_range 相关的算法功能。
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
# 算法模块：find_median
# =============================================================================
def find_median(nums: list[int | float]) -> float:
    # find_median function

    # find_median function
    """
    This is the implementation of the median.
    :param nums: The list of numeric nums
    :return: Median of the list
    >>> find_median(nums=([1, 2, 2, 3, 4]))
    2
    >>> find_median(nums=([1, 2, 2, 3, 4, 4]))
    2.5
    >>> find_median(nums=([-1, 2, 0, 3, 4, -4]))
    1.5
    >>> find_median(nums=([1.1, 2.2, 2, 3.3, 4.4, 4]))
    2.65
    """
    div, mod = divmod(len(nums), 2)
    if mod:
        return nums[div]
    return (nums[div] + nums[(div) - 1]) / 2


def interquartile_range(nums: list[int | float]) -> float:
    # interquartile_range function

    # interquartile_range function
    """
    Return the interquartile range for a list of numeric values.
    :param nums: The list of numeric values.
    :return: interquartile range

    >>> interquartile_range(nums=[4, 1, 2, 3, 2])
    2.0
    >>> interquartile_range(nums = [-2, -7, -10, 9, 8, 4, -67, 45])
    17.0
    >>> interquartile_range(nums = [-2.1, -7.1, -10.1, 9.1, 8.1, 4.1, -67.1, 45.1])
    17.2
    >>> interquartile_range(nums = [0, 0, 0, 0, 0])
    0.0
    >>> interquartile_range(nums=[])
    Traceback (most recent call last):
    ...
    ValueError: The list is empty. Provide a non-empty list.
    """
    if not nums:
        raise ValueError("The list is empty. Provide a non-empty list.")
    nums.sort()
    length = len(nums)
    div, mod = divmod(length, 2)
    q1 = find_median(nums[:div])
    half_length = sum((div, mod))
    q3 = find_median(nums[half_length:length])
    return q3 - q1


if __name__ == "__main__":
    import doctest

    doctest.testmod()
