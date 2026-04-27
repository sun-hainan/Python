# -*- coding: utf-8 -*-
"""
Project Euler Problem 069

解决 Project Euler 第 069 题的 Python 实现。
https://projecteuler.net/problem=069
"""

# =============================================================================
# Project Euler 问题 069
# =============================================================================
def solution(n: int = 10**6) -> int:
    """
    Returns solution to problem.
    Algorithm:
    1. Precompute φ(k) for all natural k, k <= n using product formula (wikilink below)
    https://en.wikipedia.org/wiki/Euler%27s_totient_function#Euler's_product_formula

    2. Find k/φ(k) for all k ≤ n and return the k that attains maximum

    >>> solution(10)
    6

    >>> solution(100)
    30

    >>> solution(9973)
    2310

    """

    if n <= 0:
        raise ValueError("Please enter an integer greater than 0")

    phi = list(range(n + 1))
    for number in range(2, n + 1):
    # 遍历循环
        if phi[number] == number:
            phi[number] -= 1
            for multiple in range(number * 2, n + 1, number):
    # 遍历循环
                phi[multiple] = (phi[multiple] // number) * (number - 1)

    answer = 1
    for number in range(1, n + 1):
    # 遍历循环
        if (answer / phi[answer]) < (number / phi[number]):
            answer = number

    return answer
    # 返回结果


if __name__ == "__main__":
    print(solution())
