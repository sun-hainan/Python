# -*- coding: utf-8 -*-
"""
Project Euler Problem 041

解决 Project Euler 第 041 题的 Python 实现。
https://projecteuler.net/problem=041
"""

from __future__ import annotations

"""
Project Euler Problem 041 — 中文注释版
https://projecteuler.net/problem=041

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




import math
from itertools import permutations



# =============================================================================
# Project Euler 问题 041
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


def solution(n: int = 7) -> int:
    # solution 函数实现
    """
    Returns the maximum pandigital prime number of length n.
    If there are none, then it will return 0.
    >>> solution(2)
    0
    >>> solution(4)
    4231
    >>> solution(7)
    7652413
    """
    pandigital_str = "".join(str(i) for i in range(1, n + 1))
    perm_list = [int("".join(i)) for i in permutations(pandigital_str, n)]
    pandigitals = [num for num in perm_list if is_prime(num)]
    return max(pandigitals) if pandigitals else 0
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
