# -*- coding: utf-8 -*-
"""
Project Euler Problem 033

解决 Project Euler 第 033 题的 Python 实现。
https://projecteuler.net/problem=033
"""

from __future__ import annotations

"""
Project Euler Problem 033 — 中文注释版
https://projecteuler.net/problem=033

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




from fractions import Fraction



# =============================================================================
# Project Euler 问题 033
# =============================================================================
def is_digit_cancelling(num: int, den: int) -> bool:
    return (
    # 返回结果
        num != den and num % 10 == den // 10 and (num // 10) / (den % 10) == num / den
    )


def fraction_list(digit_len: int) -> list[str]:
    # fraction_list 函数实现
    """
    >>> fraction_list(2)
    ['16/64', '19/95', '26/65', '49/98']
    >>> fraction_list(3)
    ['16/64', '19/95', '26/65', '49/98']
    >>> fraction_list(4)
    ['16/64', '19/95', '26/65', '49/98']
    >>> fraction_list(0)
    []
    >>> fraction_list(5)
    ['16/64', '19/95', '26/65', '49/98']
    """
    solutions = []
    den = 11
    last_digit = int("1" + "0" * digit_len)
    for num in range(den, last_digit):
    # 遍历循环
        while den <= 99:
            if (
                (num != den)
                and (num % 10 == den // 10)
                and (den % 10 != 0)
                and is_digit_cancelling(num, den)
            ):
                solutions.append(f"{num}/{den}")
            den += 1
        num += 1
        den = 10
    return solutions
    # 返回结果


def solution(n: int = 2) -> int:
    # solution 函数实现
    """
    Return the solution to the problem
    """
    result = 1.0
    for fraction in fraction_list(n):
    # 遍历循环
        frac = Fraction(fraction)
        result *= frac.denominator / frac.numerator
    return int(result)
    # 返回结果


if __name__ == "__main__":
    print(solution())
