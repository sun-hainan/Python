# -*- coding: utf-8 -*-
"""
Project Euler Problem 045

解决 Project Euler 第 045 题的 Python 实现。
https://projecteuler.net/problem=045
"""

# =============================================================================
# Project Euler 问题 045
# =============================================================================
def hexagonal_num(n: int) -> int:
    """
    Returns nth hexagonal number
    >>> hexagonal_num(143)
    40755
    >>> hexagonal_num(21)
    861
    >>> hexagonal_num(10)
    190
    """
    return n * (2 * n - 1)
    # 返回结果


def is_pentagonal(n: int) -> bool:
    # is_pentagonal 函数实现
    """
    Returns True if n is pentagonal, False otherwise.
    >>> is_pentagonal(330)
    True
    >>> is_pentagonal(7683)
    False
    >>> is_pentagonal(2380)
    True
    """
    root = (1 + 24 * n) ** 0.5
    return ((1 + root) / 6) % 1 == 0
    # 返回结果


def solution(start: int = 144) -> int:
    # solution 函数实现
    """
    Returns the next number which is triangular, pentagonal and hexagonal.
    >>> solution(144)
    1533776805
    """
    n = start
    num = hexagonal_num(n)
    while not is_pentagonal(num):
    # 条件循环
        n += 1
        num = hexagonal_num(n)
    return num
    # 返回结果


if __name__ == "__main__":
    print(f"{solution()} = ")
