# -*- coding: utf-8 -*-
"""
Project Euler Problem 016

解决 Project Euler 第 016 题的 Python 实现。
https://projecteuler.net/problem=016
"""

# =============================================================================
# Project Euler 问题 016
# =============================================================================
def solution(power: int = 1000) -> int:
    """Returns the sum of the digits of the number 2^power.
    >>> solution(1000)
    1366
    >>> solution(50)
    76
    >>> solution(20)
    31
    >>> solution(15)
    26
    """
    num = 2**power
    string_num = str(num)
    list_num = list(string_num)
    sum_of_num = 0

    for i in list_num:
    # 遍历循环
        sum_of_num += int(i)

    return sum_of_num
    # 返回结果


if __name__ == "__main__":
    power = int(input("Enter the power of 2: ").strip())
    print("2 ^ ", power, " = ", 2**power)
    result = solution(power)
    print("Sum of the digits is: ", result)
