# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / factorial



本文件实现 factorial 相关的算法功能。

"""



# Factorial of a number using memoization



from functools import lru_cache





@lru_cache

def factorial(num: int) -> int:

    """

    >>> factorial(7)

    5040

    >>> factorial(-1)

    Traceback (most recent call last):

      ...

    ValueError: Number should not be negative.

    >>> [factorial(i) for i in range(10)]

    [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880]

    """

    if num < 0:

        raise ValueError("Number should not be negative.")



    return 1 if num in (0, 1) else num * factorial(num - 1)





if __name__ == "__main__":

    import doctest



    doctest.testmod()

