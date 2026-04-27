# -*- coding: utf-8 -*-

"""

Project Euler Problem 131



解决 Project Euler 第 131 题的 Python 实现。

https://projecteuler.net/problem=131

"""



from math import isqrt







# =============================================================================

# Project Euler 问题 131

# =============================================================================

def is_prime(number: int) -> bool:

    """

    Determines whether number is prime



    >>> is_prime(3)

    True



    >>> is_prime(4)

    False

    """



    return all(number % divisor != 0 for divisor in range(2, isqrt(number) + 1))

    # 返回结果





def solution(max_prime: int = 10**6) -> int:

    # solution 函数实现

    """

    Returns number of primes below max_prime with the property



    >>> solution(100)

    4

    """



    primes_count = 0

    cube_index = 1

    prime_candidate = 7

    while prime_candidate < max_prime:

    # 条件循环

        primes_count += is_prime(prime_candidate)



        cube_index += 1

        prime_candidate += 6 * cube_index



    return primes_count

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

