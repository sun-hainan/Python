# -*- coding: utf-8 -*-
"""
Project Euler Problem 046

解决 Project Euler 第 046 题的 Python 实现。
https://projecteuler.net/problem=046
"""

from __future__ import annotations

"""
Project Euler Problem 046 — 中文注释版
https://projecteuler.net/problem=046

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




import math



# =============================================================================
# Project Euler 问题 046
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


odd_composites = [num for num in range(3, 100001, 2) if not is_prime(num)]


def compute_nums(n: int) -> list[int]:
    # compute_nums 函数实现
    """
    Returns a list of first n odd composite numbers which do
    not follow the conjecture.
    >>> compute_nums(1)
    [5777]
    >>> compute_nums(2)
    [5777, 5993]
    >>> compute_nums(0)
    Traceback (most recent call last):
        ...
    ValueError: n must be >= 0
    >>> compute_nums("a")
    Traceback (most recent call last):
        ...
    ValueError: n must be an integer
    >>> compute_nums(1.1)
    Traceback (most recent call last):
        ...
    ValueError: n must be an integer

    """
    if not isinstance(n, int):
        raise ValueError("n must be an integer")
    if n <= 0:
        raise ValueError("n must be >= 0")

    list_nums = []
    for num in range(len(odd_composites)):
    # 遍历循环
        i = 0
        while 2 * i * i <= odd_composites[num]:
    # 条件循环
            rem = odd_composites[num] - 2 * i * i
            if is_prime(rem):
                break
            i += 1
        else:
            list_nums.append(odd_composites[num])
            if len(list_nums) == n:
                return list_nums
    # 返回结果

    return []
    # 返回结果


def solution() -> int:
    # solution 函数实现
    """Return the solution to the problem"""
    return compute_nums(1)[0]
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
