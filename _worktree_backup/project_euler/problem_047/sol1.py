# -*- coding: utf-8 -*-
"""
Project Euler Problem 047

解决 Project Euler 第 047 题的 Python 实现。
https://projecteuler.net/problem=047
"""

from functools import lru_cache



# =============================================================================
# Project Euler 问题 047
# =============================================================================
def unique_prime_factors(n: int) -> set:
    """
    Find unique prime factors of an integer.
    Tests include sorting because only the set matters,
    not the order in which it is produced.
    >>> sorted(set(unique_prime_factors(14)))
    [2, 7]
    >>> sorted(set(unique_prime_factors(644)))
    [2, 7, 23]
    >>> sorted(set(unique_prime_factors(646)))
    [2, 17, 19]
    """
    i = 2
    factors = set()
    while i * i <= n:
    # 条件循环
        if n % i:
            i += 1
        else:
            n //= i
            factors.add(i)
    if n > 1:
        factors.add(n)
    return factors
    # 返回结果


@lru_cache
def upf_len(num: int) -> int:
    # upf_len 函数实现
    """
    Memoize upf() length results for a given value.
    >>> upf_len(14)
    2
    """
    return len(unique_prime_factors(num))
    # 返回结果


def equality(iterable: list) -> bool:
    # equality 函数实现
    """
    Check the equality of ALL elements in an iterable
    >>> equality([1, 2, 3, 4])
    False
    >>> equality([2, 2, 2, 2])
    True
    >>> equality([1, 2, 3, 2, 1])
    False
    """
    return len(set(iterable)) in (0, 1)
    # 返回结果


def run(n: int) -> list[int]:
    # run 函数实现
    """
    Runs core process to find problem solution.
    >>> run(3)
    [644, 645, 646]
    """

    # Incrementor variable for our group list comprehension.
    # This is the first number in each list of values
    # to test.
    base = 2

    while True:
    # 条件循环
        # Increment each value of a generated range
        group = [base + i for i in range(n)]

        # Run elements through the unique_prime_factors function
        # Append our target number to the end.
        checker = [upf_len(x) for x in group]
        checker.append(n)

        # If all numbers in the list are equal, return the group variable.
        if equality(checker):
            return group
    # 返回结果

        # Increment our base variable by 1
        base += 1


def solution(n: int = 4) -> int | None:
    # solution 函数实现
    """Return the first value of the first four consecutive integers to have four
    distinct prime factors each.
    >>> solution()
    134043
    """
    results = run(n)
    return results[0] if len(results) else None
    # 返回结果


if __name__ == "__main__":
    print(solution())
