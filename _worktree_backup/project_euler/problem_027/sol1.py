# -*- coding: utf-8 -*-
"""
Project Euler Problem 027

解决 Project Euler 第 027 题的 Python 实现。
https://projecteuler.net/problem=027
"""

import math



# =============================================================================
# Project Euler 问题 027
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
    >>> is_prime(-10)
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


def solution(a_limit: int = 1000, b_limit: int = 1000) -> int:
    # solution 函数实现
    """
    >>> solution(1000, 1000)
    -59231
    >>> solution(200, 1000)
    -59231
    >>> solution(200, 200)
    -4925
    >>> solution(-1000, 1000)
    0
    >>> solution(-1000, -1000)
    0
    """
    longest = [0, 0, 0]  # length, a, b
    for a in range((a_limit * -1) + 1, a_limit):
    # 遍历循环
        for b in range(2, b_limit):
            if is_prime(b):
                count = 0
                n = 0
                while is_prime((n**2) + (a * n) + b):
    # 条件循环
                    count += 1
                    n += 1
                if count > longest[0]:
                    longest = [count, a, b]
    ans = longest[1] * longest[2]
    return ans
    # 返回结果


if __name__ == "__main__":
    print(solution(1000, 1000))
