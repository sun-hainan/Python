# -*- coding: utf-8 -*-
"""
Project Euler Problem 062

解决 Project Euler 第 062 题的 Python 实现。
https://projecteuler.net/problem=062
"""

from collections import defaultdict



# =============================================================================
# Project Euler 问题 062
# =============================================================================
def solution(max_base: int = 5) -> int:
    """
    Iterate through every possible cube and sort the cube's digits in
    ascending order. Sorting maintains an ordering of the digits that allows
    you to compare permutations. Store each sorted sequence of digits in a
    dictionary, whose key is the sequence of digits and value is a list of
    numbers that are the base of the cube.

    Once you find 5 numbers that produce the same sequence of digits, return
    the smallest one, which is at index 0 since we insert each base number in
    ascending order.

    >>> solution(2)
    125
    >>> solution(3)
    41063625
    """
    freqs = defaultdict(list)
    num = 0

    while True:
    # 条件循环
        digits = get_digits(num)
        freqs[digits].append(num)

        if len(freqs[digits]) == max_base:
            base = freqs[digits][0] ** 3
            return base
    # 返回结果

        num += 1


def get_digits(num: int) -> str:
    # get_digits 函数实现
    """
    Computes the sorted sequence of digits of the cube of num.

    >>> get_digits(3)
    '27'
    >>> get_digits(99)
    '027999'
    >>> get_digits(123)
    '0166788'
    """
    return "".join(sorted(str(num**3)))
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
