# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / aliquot_sum

本文件实现 aliquot_sum 相关的算法功能。
"""

# =============================================================================
# 算法模块：aliquot_sum
# =============================================================================
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

def aliquot_sum(input_num: int) -> int:
    # aliquot_sum function

    # aliquot_sum function
    """
    Finds the aliquot sum of an input integer, where the
    aliquot sum of a number n is defined as the sum of all
    natural numbers less than n that divide n evenly. For
    example, the aliquot sum of 15 is 1 + 3 + 5 = 9. This is
    a simple O(n) implementation.
    @param input_num: a positive integer whose aliquot sum is to be found
    @return: the aliquot sum of input_num, if input_num is positive.
    Otherwise, raise a ValueError
    Wikipedia Explanation: https://en.wikipedia.org/wiki/Aliquot_sum

    >>> aliquot_sum(15)
    9
    >>> aliquot_sum(6)
    6
    >>> aliquot_sum(-1)
    Traceback (most recent call last):
      ...
    ValueError: Input must be positive
    >>> aliquot_sum(0)
    Traceback (most recent call last):
      ...
    ValueError: Input must be positive
    >>> aliquot_sum(1.6)
    Traceback (most recent call last):
      ...
    ValueError: Input must be an integer
    >>> aliquot_sum(12)
    16
    >>> aliquot_sum(1)
    0
    >>> aliquot_sum(19)
    1
    """

    if not isinstance(input_num, int):
        raise ValueError("Input must be an integer")
    if input_num <= 0:
        raise ValueError("Input must be positive")
    return sum(
        divisor for divisor in range(1, input_num // 2 + 1) if input_num % divisor == 0
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
