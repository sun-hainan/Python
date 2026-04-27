# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / power_using_recursion

本文件实现 power_using_recursion 相关的算法功能。
"""

# =============================================================================
# 算法模块：power
# =============================================================================
def power(base: int, exponent: int) -> float:
    # power function

    # power function
    """
    Calculate the power of a base raised to an exponent.

    >>> power(3, 4)
    81
    >>> power(2, 0)
    1
    >>> all(power(base, exponent) == pow(base, exponent)
    ...     for base in range(-10, 10) for exponent in range(10))
    True
    >>> power('a', 1)
    'a'
    >>> power('a', 2)
    Traceback (most recent call last):
        ...
    TypeError: can't multiply sequence by non-int of type 'str'
    >>> power('a', 'b')
    Traceback (most recent call last):
        ...
    TypeError: unsupported operand type(s) for -: 'str' and 'int'
    >>> power(2, -1)
    Traceback (most recent call last):
        ...
    RecursionError: maximum recursion depth exceeded
    >>> power(0, 0)
    1
    >>> power(0, 1)
    0
    >>> power(5,6)
    15625
    >>> power(23, 12)
    21914624432020321
    """
    return base * power(base, (exponent - 1)) if exponent else 1


if __name__ == "__main__":
    from doctest import testmod

    testmod()
    print("Raise base to the power of exponent using recursion...")
    base = int(input("Enter the base: ").strip())
    exponent = int(input("Enter the exponent: ").strip())
    result = power(base, abs(exponent))
    if exponent < 0:  # power() does not properly deal w/ negative exponents
        result = 1 / result
    print(f"{base} to the power of {exponent} is {result}")
