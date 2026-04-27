# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / mobius_function

本文件实现 mobius_function 相关的算法功能。
"""

from maths.is_square_free import is_square_free
from maths.prime_factors import prime_factors



# =============================================================================
# 算法模块：mobius
# =============================================================================
def mobius(n: int) -> int:
    # mobius function

    # mobius function
    """
    Mobius function
    >>> mobius(24)
    0
    >>> mobius(-1)
    1
    >>> mobius('asd')
    Traceback (most recent call last):
        ...
    TypeError: '<=' not supported between instances of 'int' and 'str'
    >>> mobius(10**400)
    0
    >>> mobius(10**-400)
    1
    >>> mobius(-1424)
    1
    >>> mobius([1, '2', 2.0])
    Traceback (most recent call last):
        ...
    TypeError: '<=' not supported between instances of 'int' and 'list'
    """
    factors = prime_factors(n)
    if is_square_free(factors):
        return -1 if len(factors) % 2 else 1
    return 0


if __name__ == "__main__":
    import doctest

    doctest.testmod()
