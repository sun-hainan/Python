# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / kth_order_statistic

本文件实现 kth_order_statistic 相关的算法功能。
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



from random import choice


# random_pivot 算法
def random_pivot(lst):
    # random_pivot function

    # random_pivot function
    """
    Choose a random pivot for the list.
    We can use a more sophisticated algorithm here, such as the median-of-medians
    algorithm.
    """
    return choice(lst)


def kth_number(lst: list[int], k: int) -> int:
    # kth_number function

    # kth_number function
    """
    Return the kth smallest number in lst.
    >>> kth_number([2, 1, 3, 4, 5], 3)
    3
    >>> kth_number([2, 1, 3, 4, 5], 1)
    1
    >>> kth_number([2, 1, 3, 4, 5], 5)
    5
    >>> kth_number([3, 2, 5, 6, 7, 8], 2)
    3
    >>> kth_number([25, 21, 98, 100, 76, 22, 43, 60, 89, 87], 4)
    43
    """
    # pick a pivot and separate into list based on pivot.
    pivot = random_pivot(lst)

    # partition based on pivot
    # linear time
    small = [e for e in lst if e < pivot]
    big = [e for e in lst if e > pivot]

    # if we get lucky, pivot might be the element we want.
    # we can easily see this:
    # small (elements smaller than k)
    # + pivot (kth element)
    # + big (elements larger than k)
    if len(small) == k - 1:
        return pivot
    # pivot is in elements bigger than k
    elif len(small) < k - 1:
        return kth_number(big, k - len(small) - 1)
    # pivot is in elements smaller than k
    else:
        return kth_number(small, k)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
