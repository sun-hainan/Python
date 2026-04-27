# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / is_square_free



本文件实现 is_square_free 相关的算法功能。

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

# 算法模块：is_square_free

# =============================================================================

def is_square_free(factors: list[int]) -> bool:

    # is_square_free function



    # is_square_free function

    """

    # doctest: +NORMALIZE_WHITESPACE

    This functions takes a list of prime factors as input.

    returns True if the factors are square free.

    >>> is_square_free([1, 1, 2, 3, 4])

    False



    These are wrong but should return some value

    it simply checks for repetition in the numbers.

    >>> is_square_free([1, 3, 4, 'sd', 0.0])

    True



    >>> is_square_free([1, 0.5, 2, 0.0])

    True

    >>> is_square_free([1, 2, 2, 5])

    False

    >>> is_square_free('asd')

    True

    >>> is_square_free(24)

    Traceback (most recent call last):

        ...

    TypeError: 'int' object is not iterable

    """

    return len(set(factors)) == len(factors)





if __name__ == "__main__":

    import doctest



    doctest.testmod()

