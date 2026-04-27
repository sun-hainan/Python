# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / sum_of_arithmetic_series

本文件实现 sum_of_arithmetic_series 相关的算法功能。
"""

# DarkCoder

# =============================================================================
# 算法模块：sum_of_series
# =============================================================================
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

def sum_of_series(first_term: int, common_diff: int, num_of_terms: int) -> float:
    # sum_of_series function

    # sum_of_series function
    """
    Find the sum of n terms in an arithmetic progression.

    >>> sum_of_series(1, 1, 10)
    55.0
    >>> sum_of_series(1, 10, 100)
    49600.0
    """

    total = (num_of_terms / 2) * (2 * first_term + (num_of_terms - 1) * common_diff)
    # formula for sum of series
    return total


def main():
    # main function

    # main function
    print(sum_of_series(1, 1, 10))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
