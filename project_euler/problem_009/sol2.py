# -*- coding: utf-8 -*-

"""

Project Euler Problem 009



解决 Project Euler 第 009 题的 Python 实现。

https://projecteuler.net/problem=009

"""



# =============================================================================

# Project Euler 问题 009

# =============================================================================

def solution(n: int = 1000) -> int:

    """

    Return the product of a,b,c which are Pythagorean Triplet that satisfies

    the following:

      1. a < b < c

      2. a**2 + b**2 = c**2

      3. a + b + c = n



    >>> solution(36)

    1620

    >>> solution(126)

    66780

    """



    product = -1

    candidate = 0

    for a in range(1, n // 3):

    # 遍历循环

        # Solving the two equations a**2+b**2=c**2 and a+b+c=N eliminating c

        b = (n * n - 2 * a * n) // (2 * n - 2 * a)

        c = n - a - b

        if c * c == (a * a + b * b):

            candidate = a * b * c

            product = max(product, candidate)

    return product

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

