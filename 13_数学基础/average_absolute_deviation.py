# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / average_absolute_deviation

本文件实现 average_absolute_deviation 相关的算法功能。
"""

# =============================================================================
# 算法模块：average_absolute_deviation
# =============================================================================
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

def average_absolute_deviation(nums: list[int]) -> float:
    # average_absolute_deviation function

    # average_absolute_deviation function
    """
    Return the average absolute deviation of a list of numbers.
    Wiki: https://en.wikipedia.org/wiki/Average_absolute_deviation

    >>> average_absolute_deviation([0])
    0.0
    >>> average_absolute_deviation([4, 1, 3, 2])
    1.0
    >>> average_absolute_deviation([2, 70, 6, 50, 20, 8, 4, 0])
    20.0
    >>> average_absolute_deviation([-20, 0, 30, 15])
    16.25
    >>> average_absolute_deviation([])
    Traceback (most recent call last):
        ...
    ValueError: List is empty
    """

    if not nums:  # Makes sure that the list is not empty
        raise ValueError("List is empty")

    average = sum(nums) / len(nums)  # Calculate the average
    return sum(abs(x - average) for x in nums) / len(nums)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
