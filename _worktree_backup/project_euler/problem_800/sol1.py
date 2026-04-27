# -*- coding: utf-8 -*-
"""
Project Euler Problem 800

解决 Project Euler 第 800 题的 Python 实现。
https://projecteuler.net/problem=800
"""

from math import isqrt, log2



# =============================================================================
# Project Euler 问题 800
# =============================================================================
def calculate_prime_numbers(max_number: int) -> list[int]:
    """
    Returns prime numbers below max_number

    >>> calculate_prime_numbers(10)
    [2, 3, 5, 7]
    """

    is_prime = [True] * max_number
    for i in range(2, isqrt(max_number - 1) + 1):
    # 遍历循环
        if is_prime[i]:
            for j in range(i**2, max_number, i):
    # 遍历循环
                is_prime[j] = False

    return [i for i in range(2, max_number) if is_prime[i]]
    # 返回结果


def solution(base: int = 800800, degree: int = 800800) -> int:
    # solution 函数实现
    """
    Returns the number of hybrid-integers less than or equal to base^degree

    >>> solution(800, 1)
    2

    >>> solution(800, 800)
    10790
    """

    upper_bound = degree * log2(base)
    max_prime = int(upper_bound)
    prime_numbers = calculate_prime_numbers(max_prime)

    hybrid_integers_count = 0
    left = 0
    right = len(prime_numbers) - 1
    while left < right:
    # 条件循环
        while (
            prime_numbers[right] * log2(prime_numbers[left])
            + prime_numbers[left] * log2(prime_numbers[right])
            > upper_bound
        ):
            right -= 1
        hybrid_integers_count += right - left
        left += 1

    return hybrid_integers_count
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
