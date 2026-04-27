# -*- coding: utf-8 -*-

"""

Project Euler Problem 190



解决 Project Euler 第 190 题的 Python 实现。

https://projecteuler.net/problem=190

"""



# =============================================================================

# Project Euler 问题 190

# =============================================================================

def solution(n: int = 15) -> int:

    """

    Calculate sum of |_ P_m _| for m from 2 to n.



    >>> solution(2)

    1

    >>> solution(3)

    2

    >>> solution(4)

    4

    >>> solution(5)

    10

    """

    total = 0

    for m in range(2, n + 1):

    # 遍历循环

        x1 = 2 / (m + 1)

        p = 1.0

        for i in range(1, m + 1):

    # 遍历循环

            xi = i * x1

            p *= xi**i

        total += int(p)

    return total

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

