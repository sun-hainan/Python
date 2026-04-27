# -*- coding: utf-8 -*-
"""
算法实现：series / hexagonal_numbers

本文件实现 hexagonal_numbers 相关的算法功能。
"""

# =============================================================================
# 算法模块：hexagonal_numbers
# =============================================================================
def hexagonal_numbers(length: int) -> list[int]:
    # hexagonal_numbers function

    # hexagonal_numbers function
    """
    :param len: max number of elements
    :type len: int
    :return: Hexagonal numbers as a list

    Tests:
    >>> hexagonal_numbers(10)
    [0, 1, 6, 15, 28, 45, 66, 91, 120, 153]
    >>> hexagonal_numbers(5)
    [0, 1, 6, 15, 28]
    >>> hexagonal_numbers(0)
    Traceback (most recent call last):
      ...
    ValueError: Length must be a positive integer.
    """

    if length <= 0 or not isinstance(length, int):
        raise ValueError("Length must be a positive integer.")
    return [n * (2 * n - 1) for n in range(length)]


if __name__ == "__main__":
    print(hexagonal_numbers(length=5))
    print(hexagonal_numbers(length=10))
