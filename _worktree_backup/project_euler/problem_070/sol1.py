# -*- coding: utf-8 -*-
"""
Project Euler Problem 070

解决 Project Euler 第 070 题的 Python 实现。
https://projecteuler.net/problem=070
"""

from __future__ import annotations

"""
Project Euler Problem 070 — 中文注释版
https://projecteuler.net/problem=070

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




import numpy as np



# =============================================================================
# Project Euler 问题 070
# =============================================================================
def get_totients(max_one: int) -> list[int]:
    """
    Calculates a list of totients from 0 to max_one exclusive, using the
    definition of Euler's product formula.

    >>> get_totients(5)
    [0, 1, 1, 2, 2]

    >>> get_totients(10)
    [0, 1, 1, 2, 2, 4, 2, 6, 4, 6]
    """
    totients = np.arange(max_one)

    for i in range(2, max_one):
    # 遍历循环
        if totients[i] == i:
            x = np.arange(i, max_one, i)  # array of indexes to select
            totients[x] -= totients[x] // i

    return totients.tolist()
    # 返回结果


def has_same_digits(num1: int, num2: int) -> bool:
    # has_same_digits 函数实现
    """
    Return True if num1 and num2 have the same frequency of every digit, False
    otherwise.

    >>> has_same_digits(123456789, 987654321)
    True

    >>> has_same_digits(123, 23)
    False

    >>> has_same_digits(1234566, 123456)
    False
    """
    return sorted(str(num1)) == sorted(str(num2))
    # 返回结果


def solution(max_n: int = 10000000) -> int:
    # solution 函数实现
    """
    Finds the value of n from 1 to max such that n/φ(n) produces a minimum.

    >>> solution(100)
    21

    >>> solution(10000)
    4435
    """

    min_numerator = 1  # i
    min_denominator = 0  # φ(i)
    totients = get_totients(max_n + 1)

    for i in range(2, max_n + 1):
    # 遍历循环
        t = totients[i]

        if i * min_denominator < min_numerator * t and has_same_digits(i, t):
            min_numerator = i
            min_denominator = t

    return min_numerator
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
