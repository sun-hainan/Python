# -*- coding: utf-8 -*-

"""

Project Euler Problem 123



解决 Project Euler 第 123 题的 Python 实现。

https://projecteuler.net/problem=123

"""



from __future__ import annotations



"""

Project Euler Problem 123 — 中文注释版

https://projecteuler.net/problem=123



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""









from collections.abc import Generator







# =============================================================================

# Project Euler 问题 123

# =============================================================================

def sieve() -> Generator[int]:

    """

    Returns a prime number generator using sieve method.

    >>> type(sieve())

    <class 'generator'>

    >>> primes = sieve()

    >>> next(primes)

    2

    >>> next(primes)

    3

    >>> next(primes)

    5

    >>> next(primes)

    7

    >>> next(primes)

    11

    >>> next(primes)

    13

    """

    factor_map: dict[int, int] = {}

    prime = 2

    while True:

    # 条件循环

        factor = factor_map.pop(prime, None)

        if factor:

            x = factor + prime

            while x in factor_map:

    # 条件循环

                x += factor

            factor_map[x] = factor

        else:

            factor_map[prime * prime] = prime

            yield prime

        prime += 1





def solution(limit: float = 1e10) -> int:

    # solution 函数实现

    """

    Returns the least value of n for which the remainder first exceeds 10^10.

    >>> solution(1e8)

    2371

    >>> solution(1e9)

    7037

    """

    primes = sieve()



    n = 1

    while True:

    # 条件循环

        prime = next(primes)

        if (2 * prime * n) > limit:

            return n

    # 返回结果

        # Ignore the next prime as the reminder will be 2.

        next(primes)

        n += 2





if __name__ == "__main__":

    print(solution())

