# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / numbers_different_signs

本文件实现 numbers_different_signs 相关的算法功能。
"""

def different_signs(num1: int, num2: int) -> bool:
    # different_signs function

    # different_signs function
    """
    Return True if numbers have opposite signs False otherwise.

    >>> different_signs(1, -1)
    True
    >>> different_signs(1, 1)
    False
    >>> different_signs(1000000000000000000000000000, -1000000000000000000000000000)
    True
    >>> different_signs(-1000000000000000000000000000, 1000000000000000000000000000)
    True
    >>> different_signs(50, 278)
    False
    >>> different_signs(0, 2)
    False
    >>> different_signs(2, 0)
    False
    """
    return num1 ^ num2 < 0


if __name__ == "__main__":
    import doctest

    doctest.testmod()
