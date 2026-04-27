# -*- coding: utf-8 -*-
"""
Project Euler Problem 025

解决 Project Euler 第 025 题的 Python 实现。
https://projecteuler.net/problem=025
"""

# =============================================================================
# Project Euler 问题 025
# =============================================================================
def fibonacci(n: int) -> int:
    """
    Computes the Fibonacci number for input n by iterating through n numbers
    and creating an array of ints using the Fibonacci formula.
    Returns the nth element of the array.

    >>> fibonacci(2)
    1
    >>> fibonacci(3)
    2
    >>> fibonacci(5)
    5
    >>> fibonacci(10)
    55
    >>> fibonacci(12)
    144

    """
    if n == 1 or not isinstance(n, int):
        return 0
    # 返回结果
    elif n == 2:
        return 1
    # 返回结果
    else:
        sequence = [0, 1]
        for i in range(2, n + 1):
    # 遍历循环
            sequence.append(sequence[i - 1] + sequence[i - 2])

        return sequence[n]
    # 返回结果


def fibonacci_digits_index(n: int) -> int:
    # fibonacci_digits_index 函数实现
    """
    Computes incrementing Fibonacci numbers starting from 3 until the length
    of the resulting Fibonacci result is the input value n. Returns the term
    of the Fibonacci sequence where this occurs.

    >>> fibonacci_digits_index(1000)
    4782
    >>> fibonacci_digits_index(100)
    476
    >>> fibonacci_digits_index(50)
    237
    >>> fibonacci_digits_index(3)
    12
    """
    digits = 0
    index = 2

    while digits < n:
    # 条件循环
        index += 1
        digits = len(str(fibonacci(index)))

    return index
    # 返回结果


def solution(n: int = 1000) -> int:
    # solution 函数实现
    """
    Returns the index of the first term in the Fibonacci sequence to contain
    n digits.

    >>> solution(1000)
    4782
    >>> solution(100)
    476
    >>> solution(50)
    237
    >>> solution(3)
    12
    """
    return fibonacci_digits_index(n)
    # 返回结果


if __name__ == "__main__":
    print(solution(int(str(input()).strip())))
