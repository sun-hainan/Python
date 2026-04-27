# -*- coding: utf-8 -*-
"""
Project Euler Problem 187

解决 Project Euler 第 187 题的 Python 实现。
https://projecteuler.net/problem=187
"""

from math import isqrt



# =============================================================================
# Project Euler 问题 187
# =============================================================================
def slow_calculate_prime_numbers(max_number: int) -> list[int]:
    """
    Returns prime numbers below max_number.
    See: https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes

    >>> slow_calculate_prime_numbers(10)
    [2, 3, 5, 7]

    >>> slow_calculate_prime_numbers(2)
    []
    """

    # List containing a bool value for every number below max_number/2
    is_prime = [True] * max_number

    for i in range(2, isqrt(max_number - 1) + 1):
    # 遍历循环
        if is_prime[i]:
            # Mark all multiple of i as not prime
            for j in range(i**2, max_number, i):
    # 遍历循环
                is_prime[j] = False

    return [i for i in range(2, max_number) if is_prime[i]]
    # 返回结果


def calculate_prime_numbers(max_number: int) -> list[int]:
    # calculate_prime_numbers 函数实现
    """
    Returns prime numbers below max_number.
    See: https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes

    >>> calculate_prime_numbers(10)
    [2, 3, 5, 7]

    >>> calculate_prime_numbers(2)
    []
    """

    if max_number <= 2:
        return []
    # 返回结果

    # List containing a bool value for every odd number below max_number/2
    is_prime = [True] * (max_number // 2)

    for i in range(3, isqrt(max_number - 1) + 1, 2):
    # 遍历循环
        if is_prime[i // 2]:
            # Mark all multiple of i as not prime using list slicing
            is_prime[i**2 // 2 :: i] = [False] * (
                # Same as: (max_number - (i**2)) // (2 * i) + 1
                # but faster than len(is_prime[i**2 // 2 :: i])
                len(range(i**2 // 2, max_number // 2, i))
            )

    return [2] + [2 * i + 1 for i in range(1, max_number // 2) if is_prime[i]]
    # 返回结果


def slow_solution(max_number: int = 10**8) -> int:
    # slow_solution 函数实现
    """
    Returns the number of composite integers below max_number have precisely two,
    not necessarily distinct, prime factors.

    >>> slow_solution(30)
    10
    """

    prime_numbers = slow_calculate_prime_numbers(max_number // 2)

    semiprimes_count = 0
    left = 0
    right = len(prime_numbers) - 1
    while left <= right:
    # 条件循环
        while prime_numbers[left] * prime_numbers[right] >= max_number:
            right -= 1
        semiprimes_count += right - left + 1
        left += 1

    return semiprimes_count
    # 返回结果


def while_solution(max_number: int = 10**8) -> int:
    # while_solution 函数实现
    """
    Returns the number of composite integers below max_number have precisely two,
    not necessarily distinct, prime factors.

    >>> while_solution(30)
    10
    """

    prime_numbers = calculate_prime_numbers(max_number // 2)

    semiprimes_count = 0
    left = 0
    right = len(prime_numbers) - 1
    while left <= right:
    # 条件循环
        while prime_numbers[left] * prime_numbers[right] >= max_number:
            right -= 1
        semiprimes_count += right - left + 1
        left += 1

    return semiprimes_count
    # 返回结果


def solution(max_number: int = 10**8) -> int:
    # solution 函数实现
    """
    Returns the number of composite integers below max_number have precisely two,
    not necessarily distinct, prime factors.

    >>> solution(30)
    10
    """

    prime_numbers = calculate_prime_numbers(max_number // 2)

    semiprimes_count = 0
    right = len(prime_numbers) - 1
    for left in range(len(prime_numbers)):
    # 遍历循环
        if left > right:
            break
        for r in range(right, left - 2, -1):
    # 遍历循环
            if prime_numbers[left] * prime_numbers[r] < max_number:
                break
        right = r
        semiprimes_count += right - left + 1

    return semiprimes_count
    # 返回结果


def benchmark() -> None:
    # benchmark 函数实现
    """
    Benchmarks
    """
    # Running performance benchmarks...
    # slow_solution : 108.50874730000032
    # while_sol     : 28.09581200000048
    # solution      : 25.063097400000515

    from timeit import timeit

    print("Running performance benchmarks...")

    print(f"slow_solution : {timeit('slow_solution()', globals=globals(), number=10)}")
    print(f"while_sol     : {timeit('while_solution()', globals=globals(), number=10)}")
    print(f"solution      : {timeit('solution()', globals=globals(), number=10)}")


if __name__ == "__main__":
    print(f"Solution: {solution()}")
    benchmark()
