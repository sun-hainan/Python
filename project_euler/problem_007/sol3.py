# -*- coding: utf-8 -*-

"""

Project Euler Problem 007



解决 Project Euler 第 007 题的 Python 实现。

https://projecteuler.net/problem=007

"""



import itertools

import math







# =============================================================================

# Project Euler 问题 007

# =============================================================================

def is_prime(number: int) -> bool:

    """Checks to see if a number is a prime in O(sqrt(n)).

    A number is prime if it has exactly two factors: 1 and itself.

    Returns boolean representing primality of given number (i.e., if the

    result is true, then the number is indeed prime else it is not).



    >>> is_prime(2)

    True

    >>> is_prime(3)

    True

    >>> is_prime(27)

    False

    >>> is_prime(2999)

    True

    >>> is_prime(0)

    False

    >>> is_prime(1)

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





def prime_generator():

    # prime_generator 函数实现

    """

    Generate a sequence of prime numbers

    """



    num = 2

    while True:

    # 条件循环

        if is_prime(num):

            yield num

        num += 1





def solution(nth: int = 10001) -> int:

    # solution 函数实现

    """

    Returns the n-th prime number.



    >>> solution(6)

    13

    >>> solution(1)

    2

    >>> solution(3)

    5

    >>> solution(20)

    71

    >>> solution(50)

    229

    >>> solution(100)

    541

    """

    return next(itertools.islice(prime_generator(), nth - 1, nth))

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

