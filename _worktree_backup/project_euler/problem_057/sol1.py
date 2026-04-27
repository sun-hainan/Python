# -*- coding: utf-8 -*-

"""

Project Euler Problem 057



解决 Project Euler 第 057 题的 Python 实现。

https://projecteuler.net/problem=057

"""



# =============================================================================

# Project Euler 问题 057

# =============================================================================

def solution(n: int = 1000) -> int:

    """

    returns number of fractions containing a numerator with more digits than

    the denominator in the first n expansions.

    >>> solution(14)

    2

    >>> solution(100)

    15

    >>> solution(10000)

    1508

    """

    prev_numerator, prev_denominator = 1, 1

    result = []

    for i in range(1, n + 1):

    # 遍历循环

        numerator = prev_numerator + 2 * prev_denominator

        denominator = prev_numerator + prev_denominator

        if len(str(numerator)) > len(str(denominator)):

            result.append(i)

        prev_numerator = numerator

        prev_denominator = denominator



    return len(result)

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

