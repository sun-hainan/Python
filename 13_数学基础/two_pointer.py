# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / two_pointer



本文件实现 two_pointer 相关的算法功能。

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

# 算法模块：two_pointer

# =============================================================================

def two_pointer(nums: list[int], target: int) -> list[int]:

    # two_pointer function



    # two_pointer function

    """

    >>> two_pointer([2, 7, 11, 15], 9)

    [0, 1]

    >>> two_pointer([2, 7, 11, 15], 17)

    [0, 3]

    >>> two_pointer([2, 7, 11, 15], 18)

    [1, 2]

    >>> two_pointer([2, 7, 11, 15], 26)

    [2, 3]

    >>> two_pointer([1, 3, 3], 6)

    [1, 2]

    >>> two_pointer([2, 7, 11, 15], 8)

    []

    >>> two_pointer([3 * i for i in range(10)], 19)

    []

    >>> two_pointer([1, 2, 3], 6)

    []

    """

    i = 0

    j = len(nums) - 1



    while i < j:

        if nums[i] + nums[j] == target:

            return [i, j]

        elif nums[i] + nums[j] < target:

            i = i + 1

        else:

            j = j - 1



    return []





if __name__ == "__main__":

    import doctest



    doctest.testmod()

    print(f"{two_pointer([2, 7, 11, 15], 9) = }")

