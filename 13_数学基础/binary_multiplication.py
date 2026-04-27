# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / binary_multiplication

本文件实现 binary_multiplication 相关的算法功能。
"""

# =============================================================================
# 算法模块：binary_multiply
# =============================================================================
def binary_multiply(a: int, b: int) -> int:
    # binary_multiply function

    # binary_multiply function
    """
    Multiply 'a' and 'b' using bitwise multiplication.

    Parameters:
    a (int): The first number.
    b (int): The second number.

    Returns:
    int: a * b

    Examples:
    >>> binary_multiply(2, 3)
    6
    >>> binary_multiply(5, 0)
    0
    >>> binary_multiply(3, 4)
    12
    >>> binary_multiply(10, 5)
    50
    >>> binary_multiply(0, 5)
    0
    >>> binary_multiply(2, 1)
    2
    >>> binary_multiply(1, 10)
    10
    """
    res = 0
    while b > 0:
        if b & 1:
            res += a

        a += a
        b >>= 1

    return res


def binary_mod_multiply(a: int, b: int, modulus: int) -> int:
    # binary_mod_multiply function

    # binary_mod_multiply function
    """
    Calculate (a * b) % c using binary multiplication and modular arithmetic.

    Parameters:
    a (int): The first number.
    b (int): The second number.
    modulus (int): The modulus.

    Returns:
    int: (a * b) % modulus.

    Examples:
    >>> binary_mod_multiply(2, 3, 5)
    1
    >>> binary_mod_multiply(5, 0, 7)
    0
    >>> binary_mod_multiply(3, 4, 6)
    0
    >>> binary_mod_multiply(10, 5, 13)
    11
    >>> binary_mod_multiply(2, 1, 5)
    2
    >>> binary_mod_multiply(1, 10, 3)
    1
    """
    res = 0
    while b > 0:
        if b & 1:
            res = ((res % modulus) + (a % modulus)) % modulus

        a += a
        b >>= 1

    return res


if __name__ == "__main__":
    import doctest

    doctest.testmod()
