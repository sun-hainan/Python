# -*- coding: utf-8 -*-

"""

Project Euler Problem 044



解决 Project Euler 第 044 题的 Python 实现。

https://projecteuler.net/problem=044

"""



# =============================================================================

# Project Euler 问题 044

# =============================================================================

def is_pentagonal(n: int) -> bool:

    """

    Returns True if n is pentagonal, False otherwise.

    >>> is_pentagonal(330)

    True

    >>> is_pentagonal(7683)

    False

    >>> is_pentagonal(2380)

    True

    """

    root = (1 + 24 * n) ** 0.5

    return ((1 + root) / 6) % 1 == 0

    # 返回结果





def solution(limit: int = 5000) -> int:

    # solution 函数实现

    """

    Returns the minimum difference of two pentagonal numbers P1 and P2 such that

    P1 + P2 is pentagonal and P2 - P1 is pentagonal.

    >>> solution(5000)

    5482660

    """

    pentagonal_nums = [(i * (3 * i - 1)) // 2 for i in range(1, limit)]

    for i, pentagonal_i in enumerate(pentagonal_nums):

    # 遍历循环

        for j in range(i, len(pentagonal_nums)):

            pentagonal_j = pentagonal_nums[j]

            a = pentagonal_i + pentagonal_j

            b = pentagonal_j - pentagonal_i

            if is_pentagonal(a) and is_pentagonal(b):

                return b

    # 返回结果



    return -1

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

