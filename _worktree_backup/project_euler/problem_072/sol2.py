# -*- coding: utf-8 -*-

"""

Project Euler Problem 072



解决 Project Euler 第 072 题的 Python 实现。

https://projecteuler.net/problem=072

"""



# =============================================================================

# Project Euler 问题 072

# =============================================================================

def solution(limit: int = 1000000) -> int:

    """

    Return the number of reduced proper fractions with denominator less than limit.

    >>> solution(8)

    21

    >>> solution(1000)

    304191

    """

    primes = set(range(3, limit, 2))

    primes.add(2)

    for p in range(3, limit, 2):

    # 遍历循环

        if p not in primes:

            continue

        primes.difference_update(set(range(p * p, limit, p)))



    phi = [float(n) for n in range(limit + 1)]



    for p in primes:

    # 遍历循环

        for n in range(p, limit + 1, p):

            phi[n] *= 1 - 1 / p



    return int(sum(phi[2:]))

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

