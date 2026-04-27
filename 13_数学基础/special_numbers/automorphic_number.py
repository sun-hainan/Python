# -*- coding: utf-8 -*-
"""
算法实现：special_numbers / automorphic_number

本文件实现 automorphic_number 相关的算法功能。
"""

# Author : Akshay Dubey (https://github.com/itsAkshayDubey)
# Time Complexity : O(log10n)



# =============================================================================
# 算法模块：is_automorphic_number
# =============================================================================
def is_automorphic_number(number: int) -> bool:
    # is_automorphic_number function

    # is_automorphic_number function
    """
    # doctest: +NORMALIZE_WHITESPACE
    This functions takes an integer number as input.
    returns True if the number is automorphic.
    >>> is_automorphic_number(-1)
    False
    >>> is_automorphic_number(0)
    True
    >>> is_automorphic_number(5)
    True
    >>> is_automorphic_number(6)
    True
    >>> is_automorphic_number(7)
    False
    >>> is_automorphic_number(25)
    True
    >>> is_automorphic_number(259918212890625)
    True
    >>> is_automorphic_number(259918212890636)
    False
    >>> is_automorphic_number(740081787109376)
    True
    >>> is_automorphic_number(5.0)
    Traceback (most recent call last):
        ...
    TypeError: Input value of [number=5.0] must be an integer
    """
    if not isinstance(number, int):
        msg = f"Input value of [number={number}] must be an integer"
        raise TypeError(msg)
    if number < 0:
        return False
    number_square = number * number
    while number > 0:
        if number % 10 != number_square % 10:
            return False
        number //= 10
        number_square //= 10
    return True


if __name__ == "__main__":
    import doctest

    doctest.testmod()
