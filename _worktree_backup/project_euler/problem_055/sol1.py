# -*- coding: utf-8 -*-
"""
Project Euler Problem 055

解决 Project Euler 第 055 题的 Python 实现。
https://projecteuler.net/problem=055
"""

# =============================================================================
# Project Euler 问题 055
# =============================================================================
def is_palindrome(n: int) -> bool:
    """
    Returns True if a number is palindrome.
    >>> is_palindrome(12567321)
    False
    >>> is_palindrome(1221)
    True
    >>> is_palindrome(9876789)
    True
    """
    return str(n) == str(n)[::-1]
    # 返回结果


def sum_reverse(n: int) -> int:
    # sum_reverse 函数实现
    """
    Returns the sum of n and reverse of n.
    >>> sum_reverse(123)
    444
    >>> sum_reverse(3478)
    12221
    >>> sum_reverse(12)
    33
    """
    return int(n) + int(str(n)[::-1])
    # 返回结果


def solution(limit: int = 10000) -> int:
    # solution 函数实现
    """
    Returns the count of all lychrel numbers below limit.
    >>> solution(10000)
    249
    >>> solution(5000)
    76
    >>> solution(1000)
    13
    """
    lychrel_nums = []
    for num in range(1, limit):
    # 遍历循环
        iterations = 0
        a = num
        while iterations < 50:
    # 条件循环
            num = sum_reverse(num)
            iterations += 1
            if is_palindrome(num):
                break
        else:
            lychrel_nums.append(a)
    return len(lychrel_nums)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
