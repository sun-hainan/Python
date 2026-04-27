# -*- coding: utf-8 -*-
"""
Project Euler Problem 112

解决 Project Euler 第 112 题的 Python 实现。
https://projecteuler.net/problem=112
"""

# =============================================================================
# Project Euler 问题 112
# =============================================================================
def check_bouncy(n: int) -> bool:
    """
    Returns True if number is bouncy, False otherwise
    >>> check_bouncy(6789)
    False
    >>> check_bouncy(-12345)
    False
    >>> check_bouncy(0)
    False
    >>> check_bouncy(6.74)
    Traceback (most recent call last):
        ...
    ValueError: check_bouncy() accepts only integer arguments
    >>> check_bouncy(132475)
    True
    >>> check_bouncy(34)
    False
    >>> check_bouncy(341)
    True
    >>> check_bouncy(47)
    False
    >>> check_bouncy(-12.54)
    Traceback (most recent call last):
        ...
    ValueError: check_bouncy() accepts only integer arguments
    >>> check_bouncy(-6548)
    True
    """
    if not isinstance(n, int):
        raise ValueError("check_bouncy() accepts only integer arguments")
    str_n = str(n)
    sorted_str_n = "".join(sorted(str_n))
    return str_n not in {sorted_str_n, sorted_str_n[::-1]}
    # 返回结果


def solution(percent: float = 99) -> int:
    # solution 函数实现
    """
    Returns the least number for which the proportion of bouncy numbers is
    exactly 'percent'
    >>> solution(50)
    538
    >>> solution(90)
    21780
    >>> solution(80)
    4770
    >>> solution(105)
    Traceback (most recent call last):
        ...
    ValueError: solution() only accepts values from 0 to 100
    >>> solution(100.011)
    Traceback (most recent call last):
        ...
    ValueError: solution() only accepts values from 0 to 100
    """
    if not 0 < percent < 100:
        raise ValueError("solution() only accepts values from 0 to 100")
    bouncy_num = 0
    num = 1

    while True:
    # 条件循环
        if check_bouncy(num):
            bouncy_num += 1
        if (bouncy_num / num) * 100 >= percent:
            return num
    # 返回结果
        num += 1


if __name__ == "__main__":
    from doctest import testmod

    testmod()
    print(f"{solution(99)}")
