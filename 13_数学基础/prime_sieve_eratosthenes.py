# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / prime_sieve_eratosthenes

本文件实现 prime_sieve_eratosthenes 相关的算法功能。
"""

# =============================================================================
# 算法模块：prime_sieve_eratosthenes
# =============================================================================
def prime_sieve_eratosthenes(num: int) -> list[int]:
    # prime_sieve_eratosthenes function

    # prime_sieve_eratosthenes function
    """
    Print the prime numbers up to n

    >>> prime_sieve_eratosthenes(10)
    [2, 3, 5, 7]
    >>> prime_sieve_eratosthenes(20)
    [2, 3, 5, 7, 11, 13, 17, 19]
    >>> prime_sieve_eratosthenes(2)
    [2]
    >>> prime_sieve_eratosthenes(1)
    []
    >>> prime_sieve_eratosthenes(-1)
    Traceback (most recent call last):
    ...
    ValueError: Input must be a positive integer
    """

    if num <= 0:
        raise ValueError("Input must be a positive integer")

    primes = [True] * (num + 1)

    p = 2
    while p * p <= num:
        if primes[p]:
            for i in range(p * p, num + 1, p):
                primes[i] = False
        p += 1

    return [prime for prime in range(2, num + 1) if primes[prime]]


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    user_num = int(input("Enter a positive integer: ").strip())
    print(prime_sieve_eratosthenes(user_num))
