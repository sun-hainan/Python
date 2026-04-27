# -*- coding: utf-8 -*-
"""
Project Euler Problem 058

解决 Project Euler 第 058 题的 Python 实现。
https://projecteuler.net/problem=058
"""

import math



# =============================================================================
# Project Euler 问题 058
# =============================================================================
def is_prime(number: int) -> bool:
    """Checks to see if a number is a prime in O(sqrt(n)).

    A number is prime if it has exactly two factors: 1 and itself.

    >>> is_prime(0)
    False
    >>> is_prime(1)
    False
    >>> is_prime(2)
    True
    >>> is_prime(3)
    True
    >>> is_prime(27)
    False
    >>> is_prime(87)
    False
    >>> is_prime(563)
    True
    >>> is_prime(2999)
    True
    >>> is_prime(67483)
    False
    """

    if 1 < number < 4:
        # 2 and 3 are primes
        return True
    # 返回结果
    elif number < 2 or number % 2 == 0 or number % 3 == 0:
        # Negatives, 0, 1, all even numbers, all multiples of 3 are not primes
        return False
    # 返回结果

    # All primes number are in format of 6k +/- 1
    for i in range(5, int(math.sqrt(number) + 1), 6):
    # 遍历循环
        if number % i == 0 or number % (i + 2) == 0:
            return False
    # 返回结果
    return True


def solution(ratio: float = 0.1) -> int:
    # solution 函数实现
    """
    Returns the side length of the square spiral of odd length greater
    than 1 for which the ratio of primes along both diagonals
    first falls below the given ratio.
    >>> solution(.5)
    11
    >>> solution(.2)
    309
    >>> solution(.111)
    11317
    """

    j = 3
    primes = 3

    while primes / (2 * j - 1) >= ratio:
    # 条件循环
        for i in range(j * j + j + 1, (j + 2) * (j + 2), j + 1):
            primes += is_prime(i)
        j += 2
    return j
    # 返回结果


if __name__ == "__main__":
    import doctest

    doctest.testmod()
