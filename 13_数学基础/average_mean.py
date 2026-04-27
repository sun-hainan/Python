# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / average_mean



本文件实现 average_mean 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""













# =============================================================================

# 算法模块：mean

# =============================================================================

def mean(nums: list) -> float:

    # mean function



    # mean function

    """

    Find mean of a list of numbers.

    Wiki: https://en.wikipedia.org/wiki/Mean



    >>> mean([3, 6, 9, 12, 15, 18, 21])

    12.0

    >>> mean([5, 10, 15, 20, 25, 30, 35])

    20.0

    >>> mean([1, 2, 3, 4, 5, 6, 7, 8])

    4.5

    >>> mean([])

    Traceback (most recent call last):

        ...

    ValueError: List is empty

    """



    if not nums:

        raise ValueError("List is empty")

    return sum(nums) / len(nums)





if __name__ == "__main__":

    import doctest



    doctest.testmod()

