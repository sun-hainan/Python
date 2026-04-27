# -*- coding: utf-8 -*-
"""
Project Euler Problem 125

解决 Project Euler 第 125 题的 Python 实现。
https://projecteuler.net/problem=125
"""

LIMIT = 10**8



# =============================================================================
# Project Euler 问题 125
# =============================================================================
def is_palindrome(n: int) -> bool:
    """
    Check if an integer is palindromic.
    >>> is_palindrome(12521)
    True
    >>> is_palindrome(12522)
    False
    >>> is_palindrome(12210)
    False
    """
    if n % 10 == 0:
        return False
    # 返回结果
    s = str(n)
    return s == s[::-1]
    # 返回结果


def solution() -> int:
    # solution 函数实现
    """
    Returns the sum of all numbers less than 1e8 that are both palindromic and
    can be written as the sum of consecutive squares.
    """
    answer = set()
    first_square = 1
    sum_squares = 5
    while sum_squares < LIMIT:
    # 条件循环
        last_square = first_square + 1
        while sum_squares < LIMIT:
    # 条件循环
            if is_palindrome(sum_squares):
                answer.add(sum_squares)
            last_square += 1
            sum_squares += last_square**2
        first_square += 1
        sum_squares = first_square**2 + (first_square + 1) ** 2

    return sum(answer)
    # 返回结果


if __name__ == "__main__":
    print(solution())
