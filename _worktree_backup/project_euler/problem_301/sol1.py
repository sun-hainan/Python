# -*- coding: utf-8 -*-
"""
Project Euler Problem 301

解决 Project Euler 第 301 题的 Python 实现。
https://projecteuler.net/problem=301
"""

# =============================================================================
# Project Euler 问题 301
# =============================================================================
def solution(exponent: int = 30) -> int:
    """
    For any given exponent x >= 0, 1 <= n <= 2^x.
    This function returns how many Nim games are lost given that
    each Nim game has three heaps of the form (n, 2*n, 3*n).
    >>> solution(0)
    1
    >>> solution(2)
    3
    >>> solution(10)
    144
    """
    # To find how many total games were lost for a given exponent x,
    # we need to find the Fibonacci number F(x+2).
    fibonacci_index = exponent + 2
    phi = (1 + 5**0.5) / 2
    fibonacci = (phi**fibonacci_index - (phi - 1) ** fibonacci_index) / 5**0.5

    return int(fibonacci)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
