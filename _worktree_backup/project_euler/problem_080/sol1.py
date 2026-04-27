# -*- coding: utf-8 -*-
"""
Project Euler Problem 080

解决 Project Euler 第 080 题的 Python 实现。
https://projecteuler.net/problem=080
"""

import decimal



# =============================================================================
# Project Euler 问题 080
# =============================================================================
def solution() -> int:
    """
    To evaluate the sum, Used decimal python module to calculate the decimal
    places up to 100, the most important thing would be take calculate
    a few extra places for decimal otherwise there will be rounding
    error.

    >>> solution()
    40886
    """
    answer = 0
    decimal_context = decimal.Context(prec=105)
    for i in range(2, 100):
    # 遍历循环
        number = decimal.Decimal(i)
        sqrt_number = number.sqrt(decimal_context)
        if len(str(sqrt_number)) > 1:
            answer += int(str(sqrt_number)[0])
            sqrt_number_str = str(sqrt_number)[2:101]
            answer += sum(int(x) for x in sqrt_number_str)
    return answer
    # 返回结果


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    print(f"{solution() = }")
