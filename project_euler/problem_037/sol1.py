# -*- coding: utf-8 -*-
"""
Project Euler Problem 037

解决 Project Euler 第 037 题的 Python 实现。
https://projecteuler.net/problem=037
"""

from __future__ import annotations

"""
Project Euler Problem 037 — 中文注释版
https://projecteuler.net/problem=037

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




import math



# =============================================================================
# Project Euler 问题 037
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


def list_truncated_nums(n: int) -> list[int]:
    # list_truncated_nums 函数实现
    """
    Returns a list of all left and right truncated numbers of n
    >>> list_truncated_nums(927628)
    [927628, 27628, 92762, 7628, 9276, 628, 927, 28, 92, 8, 9]
    >>> list_truncated_nums(467)
    [467, 67, 46, 7, 4]
    >>> list_truncated_nums(58)
    [58, 8, 5]
    """
    str_num = str(n)
    list_nums = [n]
    for i in range(1, len(str_num)):
    # 遍历循环
        list_nums.append(int(str_num[i:]))
        list_nums.append(int(str_num[:-i]))
    return list_nums
    # 返回结果


def validate(n: int) -> bool:
    # validate 函数实现
    """
    To optimize the approach, we will rule out the numbers above 1000,
    whose first or last three digits are not prime
    >>> validate(74679)
    False
    >>> validate(235693)
    False
    >>> validate(3797)
    True
    """
    return not (
    # 返回结果
        len(str(n)) > 3
        and (not is_prime(int(str(n)[-3:])) or not is_prime(int(str(n)[:3])))
    )


def compute_truncated_primes(count: int = 11) -> list[int]:
    # compute_truncated_primes 函数实现
    """
    Returns the list of truncated primes
    >>> compute_truncated_primes(11)
    [23, 37, 53, 73, 313, 317, 373, 797, 3137, 3797, 739397]
    """
    list_truncated_primes: list[int] = []
    num = 13
    while len(list_truncated_primes) != count:
    # 条件循环
        if validate(num):
            list_nums = list_truncated_nums(num)
            if all(is_prime(i) for i in list_nums):
                list_truncated_primes.append(num)
        num += 2
    return list_truncated_primes
    # 返回结果


def solution() -> int:
    # solution 函数实现
    """
    Returns the sum of truncated primes
    """
    return sum(compute_truncated_primes(11))
    # 返回结果


if __name__ == "__main__":
    print(f"{sum(compute_truncated_primes(11)) = }")
