# -*- coding: utf-8 -*-

"""

Project Euler Problem 075



解决 Project Euler 第 075 题的 Python 实现。

https://projecteuler.net/problem=075

"""



from collections import defaultdict

from math import gcd







# =============================================================================

# Project Euler 问题 075

# =============================================================================

def solution(limit: int = 1500000) -> int:

    """

    Return the number of values of L <= limit such that a wire of length L can be

    formmed into an integer sided right angle triangle in exactly one way.

    >>> solution(50)

    6

    >>> solution(1000)

    112

    >>> solution(50000)

    5502

    """

    frequencies: defaultdict = defaultdict(int)

    euclid_m = 2

    while 2 * euclid_m * (euclid_m + 1) <= limit:

    # 条件循环

        for euclid_n in range((euclid_m % 2) + 1, euclid_m, 2):

            if gcd(euclid_m, euclid_n) > 1:

                continue

            primitive_perimeter = 2 * euclid_m * (euclid_m + euclid_n)

            for perimeter in range(primitive_perimeter, limit + 1, primitive_perimeter):

    # 遍历循环

                frequencies[perimeter] += 1

        euclid_m += 1

    return sum(1 for frequency in frequencies.values() if frequency == 1)

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

