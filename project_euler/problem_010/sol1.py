# -*- coding: utf-8 -*-

"""

Project Euler Problem 010



解决 Project Euler 第 010 题的 Python 实现。

https://projecteuler.net/problem=010

"""



import math







# =============================================================================

# Project Euler 问题 010

# =============================================================================

def is_prime(number: int) -> bool:

    """Checks to see if a number is a prime in O(sqrt(n)).

    A number is prime if it has exactly two factors: 1 and itself.

    Returns boolean representing primality of given number num (i.e., if the

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





def solution(n: int = 2000000) -> int:

    # solution 函数实现

    """

    Returns the sum of all the primes below n.



    >>> solution(1000)

    76127

    >>> solution(5000)

    1548136

    >>> solution(10000)

    5736396

    >>> solution(7)

    10

    """



    return sum(num for num in range(3, n, 2) if is_prime(num)) + 2 if n > 2 else 0

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

