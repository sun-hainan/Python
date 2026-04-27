# -*- coding: utf-8 -*-
"""
算法实现：special_numbers / catalan_number

本文件实现 catalan_number 相关的算法功能。
"""

# =============================================================================
# 算法模块：catalan
# =============================================================================
def catalan(number: int) -> int:
    # catalan function

    # catalan function
    """
    :param number: nth catalan number to calculate
    :return: the nth catalan number
    Note: A catalan number is only defined for positive integers

    >>> catalan(5)
    14
    >>> catalan(0)
    Traceback (most recent call last):
        ...
    ValueError: Input value of [number=0] must be > 0
    >>> catalan(-1)
    Traceback (most recent call last):
        ...
    ValueError: Input value of [number=-1] must be > 0
    >>> catalan(5.0)
    Traceback (most recent call last):
        ...
    TypeError: Input value of [number=5.0] must be an integer
    """

    if not isinstance(number, int):
        msg = f"Input value of [number={number}] must be an integer"
        raise TypeError(msg)

    if number < 1:
        msg = f"Input value of [number={number}] must be > 0"
        raise ValueError(msg)

    current_number = 1

    for i in range(1, number):
        current_number *= 4 * i - 2
        current_number //= i + 1

    return current_number


if __name__ == "__main__":
    import doctest

    doctest.testmod()
