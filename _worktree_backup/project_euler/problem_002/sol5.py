# -*- coding: utf-8 -*-
"""
Project Euler Problem 002

解决 Project Euler 第 002 题的 Python 实现。
https://projecteuler.net/problem=002
"""

# =============================================================================
# Project Euler 问题 002
# =============================================================================
def solution(n: int = 4000000) -> int:
    """
    Returns the sum of all even fibonacci sequence elements that are lower
    or equal to n.

    >>> solution(10)
    10
    >>> solution(15)
    10
    >>> solution(2)
    2
    >>> solution(1)
    0
    >>> solution(34)
    44
    """

    fib = [0, 1]
    i = 0
    while fib[i] <= n:
    # 条件循环
        fib.append(fib[i] + fib[i + 1])
        if fib[i + 2] > n:
            break
        i += 1
    total = 0
    for j in range(len(fib) - 1):
    # 遍历循环
        if fib[j] % 2 == 0:
            total += fib[j]

    return total
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
