# -*- coding: utf-8 -*-

"""

Project Euler Problem 050



解决 Project Euler 第 050 题的 Python 实现。

https://projecteuler.net/problem=050

"""



from __future__ import annotations



"""

Project Euler Problem 050 — 中文注释版

https://projecteuler.net/problem=050



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""













# =============================================================================

# Project Euler 问题 050

# =============================================================================

def prime_sieve(limit: int) -> list[int]:

    """

    Sieve of Erotosthenes

    Function to return all the prime numbers up to a number 'limit'

    https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes



    >>> prime_sieve(3)

    [2]



    >>> prime_sieve(50)

    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

    """

    is_prime = [True] * limit

    is_prime[0] = False

    is_prime[1] = False

    is_prime[2] = True



    for i in range(3, int(limit**0.5 + 1), 2):

    # 遍历循环

        index = i * 2

        while index < limit:

    # 条件循环

            is_prime[index] = False

            index = index + i



    primes = [2]



    for i in range(3, limit, 2):

    # 遍历循环

        if is_prime[i]:

            primes.append(i)



    return primes

    # 返回结果





def solution(ceiling: int = 1_000_000) -> int:

    # solution 函数实现

    """

    Returns the biggest prime, below the celing, that can be written as the sum

    of consecutive the most consecutive primes.



    >>> solution(500)

    499



    >>> solution(1_000)

    953



    >>> solution(10_000)

    9521

    """

    primes = prime_sieve(ceiling)

    length = 0

    largest = 0



    for i in range(len(primes)):

    # 遍历循环

        for j in range(i + length, len(primes)):

            sol = sum(primes[i:j])

            if sol >= ceiling:

                break



            if sol in primes:

                length = j - i

                largest = sol



    return largest

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

