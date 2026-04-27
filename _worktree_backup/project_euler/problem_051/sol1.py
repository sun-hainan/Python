# -*- coding: utf-8 -*-
"""
Project Euler Problem 051

解决 Project Euler 第 051 题的 Python 实现。
https://projecteuler.net/problem=051
"""

from __future__ import annotations

"""
Project Euler Problem 051 — 中文注释版
https://projecteuler.net/problem=051

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




from collections import Counter



# =============================================================================
# Project Euler 问题 051
# =============================================================================
def prime_sieve(n: int) -> list[int]:
    """
    Sieve of Erotosthenes
    Function to return all the prime numbers up to a certain number
    https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes

    >>> prime_sieve(3)
    [2]

    >>> prime_sieve(50)
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    """
    is_prime = [True] * n
    is_prime[0] = False
    is_prime[1] = False
    is_prime[2] = True

    for i in range(3, int(n**0.5 + 1), 2):
    # 遍历循环
        index = i * 2
        while index < n:
    # 条件循环
            is_prime[index] = False
            index = index + i

    primes = [2]

    for i in range(3, n, 2):
    # 遍历循环
        if is_prime[i]:
            primes.append(i)

    return primes
    # 返回结果


def digit_replacements(number: int) -> list[list[int]]:
    # digit_replacements 函数实现
    """
    Returns all the possible families of digit replacements in a number which
    contains at least one repeating digit

    >>> digit_replacements(544)
    [[500, 511, 522, 533, 544, 555, 566, 577, 588, 599]]

    >>> digit_replacements(3112)
    [[3002, 3112, 3222, 3332, 3442, 3552, 3662, 3772, 3882, 3992]]
    """
    number_str = str(number)
    replacements = []
    digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    for duplicate in Counter(number_str) - Counter(set(number_str)):
    # 遍历循环
        family = [int(number_str.replace(duplicate, digit)) for digit in digits]
        replacements.append(family)

    return replacements
    # 返回结果


def solution(family_length: int = 8) -> int:
    # solution 函数实现
    """
    Returns the solution of the problem

    >>> solution(2)
    229399

    >>> solution(3)
    221311
    """
    numbers_checked = set()

    # Filter primes with less than 3 replaceable digits
    primes = {
        x for x in set(prime_sieve(1_000_000)) if len(str(x)) - len(set(str(x))) >= 3
    }

    for prime in primes:
    # 遍历循环
        if prime in numbers_checked:
            continue

        replacements = digit_replacements(prime)

        for family in replacements:
    # 遍历循环
            numbers_checked.update(family)
            primes_in_family = primes.intersection(family)

            if len(primes_in_family) != family_length:
                continue

            return min(primes_in_family)
    # 返回结果

    return -1
    # 返回结果


if __name__ == "__main__":
    print(solution())
