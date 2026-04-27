# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / perfect_square

本文件实现 perfect_square 相关的算法功能。
"""

import math



# =============================================================================
# 算法模块：perfect_square
# =============================================================================
def perfect_square(num: int) -> bool:
    # perfect_square function

    # perfect_square function
    """
    Check if a number is perfect square number or not
    :param num: the number to be checked
    :return: True if number is square number, otherwise False

    >>> perfect_square(9)
    True
    >>> perfect_square(16)
    True
    >>> perfect_square(1)
    True
    >>> perfect_square(0)
    True
    >>> perfect_square(10)
    False
    """

    return math.sqrt(num) * math.sqrt(num) == num


def perfect_square_binary_search(n: int) -> bool:
    # perfect_square_binary_search function

    # perfect_square_binary_search function
    """
    Check if a number is perfect square using binary search.
    Time complexity : O(Log(n))
    Space complexity: O(1)

    >>> perfect_square_binary_search(9)
    True
    >>> perfect_square_binary_search(16)
    True
    >>> perfect_square_binary_search(1)
    True
    >>> perfect_square_binary_search(0)
    True
    >>> perfect_square_binary_search(10)
    False
    >>> perfect_square_binary_search(-1)
    False
    >>> perfect_square_binary_search(1.1)
    False
    >>> perfect_square_binary_search("a")
    Traceback (most recent call last):
        ...
    TypeError: '<=' not supported between instances of 'int' and 'str'
    >>> perfect_square_binary_search(None)
    Traceback (most recent call last):
        ...
    TypeError: '<=' not supported between instances of 'int' and 'NoneType'
    >>> perfect_square_binary_search([])
    Traceback (most recent call last):
        ...
    TypeError: '<=' not supported between instances of 'int' and 'list'
    """
    left = 0
    right = n
    while left <= right:
        mid = (left + right) // 2
        if mid**2 == n:
            return True
        elif mid**2 > n:
            right = mid - 1
        else:
            left = mid + 1
    return False


if __name__ == "__main__":
    import doctest

    doctest.testmod()
