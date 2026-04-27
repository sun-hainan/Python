# -*- coding: utf-8 -*-
"""
Project Euler Problem 009

解决 Project Euler 第 009 题的 Python 实现。
https://projecteuler.net/problem=009
"""

# =============================================================================
# Project Euler 问题 009
# =============================================================================
def solution() -> int:
    """
    Returns the product of a,b,c which are Pythagorean Triplet that satisfies
    the following:
      1. a < b < c
      2. a**2 + b**2 = c**2
      3. a + b + c = 1000

    >>> solution()
    31875000
    """

    for a in range(300):
    # 遍历循环
        for b in range(a + 1, 400):
            for c in range(b + 1, 500):
    # 遍历循环
                if (a + b + c) == 1000 and (a**2) + (b**2) == (c**2):
                    return a * b * c
    # 返回结果

    return -1
    # 返回结果


def solution_fast() -> int:
    # solution_fast 函数实现
    """
    Returns the product of a,b,c which are Pythagorean Triplet that satisfies
    the following:
      1. a < b < c
      2. a**2 + b**2 = c**2
      3. a + b + c = 1000

    >>> solution_fast()
    31875000
    """

    for a in range(300):
    # 遍历循环
        for b in range(400):
            c = 1000 - a - b
            if a < b < c and (a**2) + (b**2) == (c**2):
                return a * b * c
    # 返回结果

    return -1
    # 返回结果


def benchmark() -> None:
    # benchmark 函数实现
    """
    Benchmark code comparing two different version function.
    """
    import timeit

    print(
        timeit.timeit("solution()", setup="from __main__ import solution", number=1000)
    )
    print(
        timeit.timeit(
            "solution_fast()", setup="from __main__ import solution_fast", number=1000
        )
    )


if __name__ == "__main__":
    print(f"{solution() = }")
