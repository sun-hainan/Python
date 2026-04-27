# -*- coding: utf-8 -*-

"""

Project Euler Problem 100



解决 Project Euler 第 100 题的 Python 实现。

https://projecteuler.net/problem=100

"""



# =============================================================================

# Project Euler 问题 100

# =============================================================================

def solution(min_total: int = 10**12) -> int:

    """

    Returns the number of blue discs for the first arrangement to contain

    over min_total discs in total



    >>> solution(2)

    3



    >>> solution(4)

    15



    >>> solution(21)

    85

    """



    prev_numerator = 1

    prev_denominator = 0



    numerator = 1

    denominator = 1



    while numerator <= 2 * min_total - 1:

    # 条件循环

        prev_numerator += 2 * numerator

        numerator += 2 * prev_numerator



        prev_denominator += 2 * denominator

        denominator += 2 * prev_denominator



    return (denominator + 1) // 2

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

