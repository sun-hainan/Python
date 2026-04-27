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
      1. a**2 + b**2 = c**2
      2. a + b + c = 1000

    >>> solution()
    31875000
    """

    return next(
    # 返回结果
        iter(
            [
                a * b * (1000 - a - b)
                for a in range(1, 999)
    # 遍历循环
                for b in range(a, 999)
                if (a * a + b * b == (1000 - a - b) ** 2)
            ]
        )
    )


if __name__ == "__main__":
    print(f"{solution() = }")
