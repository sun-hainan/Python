# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / max_sum_sliding_window



本文件实现 max_sum_sliding_window 相关的算法功能。

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

# 算法模块：max_sum_in_array

# =============================================================================

def max_sum_in_array(array: list[int], k: int) -> int:

    # max_sum_in_array function



    # max_sum_in_array function

    """

    Returns the maximum sum of k consecutive elements

    >>> arr = [1, 4, 2, 10, 2, 3, 1, 0, 20]

    >>> k = 4

    >>> max_sum_in_array(arr, k)

    24

    >>> k = 10

    >>> max_sum_in_array(arr,k)

    Traceback (most recent call last):

        ...

    ValueError: Invalid Input

    >>> arr = [1, 4, 2, 10, 2, 13, 1, 0, 2]

    >>> k = 4

    >>> max_sum_in_array(arr, k)

    27

    """

    if len(array) < k or k < 0:

        raise ValueError("Invalid Input")

    max_sum = current_sum = sum(array[:k])

    for i in range(len(array) - k):

        current_sum = current_sum - array[i] + array[i + k]

        max_sum = max(max_sum, current_sum)

    return max_sum





if __name__ == "__main__":

    from doctest import testmod

    from random import randint



    testmod()

    array = [randint(-1000, 1000) for i in range(100)]

    k = randint(0, 110)

    print(

        f"The maximum sum of {k} consecutive elements is {max_sum_in_array(array, k)}"

    )

