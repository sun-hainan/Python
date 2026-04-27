# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / average_median



本文件实现 average_median 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""













# =============================================================================

# 算法模块：median

# =============================================================================

def median(nums: list) -> int | float:

    # median function



    # median function

    """

    Find median of a list of numbers.

    Wiki: https://en.wikipedia.org/wiki/Median



    >>> median([0])

    0

    >>> median([4, 1, 3, 2])

    2.5

    >>> median([2, 70, 6, 50, 20, 8, 4])

    8



    Args:

        nums: List of nums



    Returns:

        Median.

    """



    # The sorted function returns list[SupportsRichComparisonT@sorted]

    # which does not support `+`

    sorted_list: list[int] = sorted(nums)

    length = len(sorted_list)

    mid_index = length >> 1

    return (

        (sorted_list[mid_index] + sorted_list[mid_index - 1]) / 2

        if length % 2 == 0

        else sorted_list[mid_index]

    )





def main():

    # main function



    # main function

    import doctest



    doctest.testmod()





if __name__ == "__main__":

    main()

