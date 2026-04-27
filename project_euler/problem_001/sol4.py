# -*- coding: utf-8 -*-

"""

Project Euler Problem 001



解决 Project Euler 第 001 题的 Python 实现。

https://projecteuler.net/problem=001

"""



# =============================================================================

# Project Euler 问题 001

# =============================================================================

def solution(n: int = 1000) -> int:

    """

    Returns the sum of all the multiples of 3 or 5 below n.



    >>> solution(3)

    0

    >>> solution(4)

    3

    >>> solution(10)

    23

    >>> solution(600)

    83700

    """



    xmulti = []

    zmulti = []

    z = 3

    x = 5

    temp = 1

    while True:

    # 条件循环

        result = z * temp

        if result < n:

            zmulti.append(result)

            temp += 1

        else:

            temp = 1

            break

    while True:

    # 条件循环

        result = x * temp

        if result < n:

            xmulti.append(result)

            temp += 1

        else:

            break

    collection = list(set(xmulti + zmulti))

    return sum(collection)

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

