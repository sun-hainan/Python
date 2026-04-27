# -*- coding: utf-8 -*-
"""
算法实现：arrays / pairs_with_given_sum

本文件实现 pairs_with_given_sum 相关的算法功能。
"""

#!/usr/bin/env python3

"""
Given an array of integers and an integer req_sum, find the number of pairs of array
elements whose sum is equal to req_sum.

https://practice.geeksforgeeks.org/problems/count-pairs-with-given-sum5022/0
"""
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""



from itertools import combinations



# =============================================================================
# 算法模块：pairs_with_sum
# =============================================================================
def pairs_with_sum(arr: list, req_sum: int) -> int:
    # pairs_with_sum function

    # pairs_with_sum function
    """
    Return the no. of pairs with sum "sum"
    >>> pairs_with_sum([1, 5, 7, 1], 6)
    2
    >>> pairs_with_sum([1, 1, 1, 1, 1, 1, 1, 1], 2)
    28
    >>> pairs_with_sum([1, 7, 6, 2, 5, 4, 3, 1, 9, 8], 7)
    4
    """
    return len([1 for a, b in combinations(arr, 2) if a + b == req_sum])


if __name__ == "__main__":
    from doctest import testmod

    testmod()
