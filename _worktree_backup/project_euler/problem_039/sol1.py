# -*- coding: utf-8 -*-

"""

Project Euler Problem 039



解决 Project Euler 第 039 题的 Python 实现。

https://projecteuler.net/problem=039

"""



from __future__ import annotations



"""

Project Euler Problem 039 — 中文注释版

https://projecteuler.net/problem=039



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""









import typing

from collections import Counter







# =============================================================================

# Project Euler 问题 039

# =============================================================================

def pythagorean_triple(max_perimeter: int) -> typing.Counter[int]:

    """

    Returns a dictionary with keys as the perimeter of a right angled triangle

    and value as the number of corresponding triplets.

    >>> pythagorean_triple(15)

    Counter({12: 1})

    >>> pythagorean_triple(40)

    Counter({12: 1, 30: 1, 24: 1, 40: 1, 36: 1})

    >>> pythagorean_triple(50)

    Counter({12: 1, 30: 1, 24: 1, 40: 1, 36: 1, 48: 1})

    """

    triplets: typing.Counter[int] = Counter()

    for base in range(1, max_perimeter + 1):

    # 遍历循环

        for perpendicular in range(base, max_perimeter + 1):

            hypotenuse = (base * base + perpendicular * perpendicular) ** 0.5

            if hypotenuse == int(hypotenuse):

                perimeter = int(base + perpendicular + hypotenuse)

                if perimeter > max_perimeter:

                    continue

                triplets[perimeter] += 1

    return triplets

    # 返回结果





def solution(n: int = 1000) -> int:

    # solution 函数实现

    """

    Returns perimeter with maximum solutions.

    >>> solution(100)

    90

    >>> solution(200)

    180

    >>> solution(1000)

    840

    """

    triplets = pythagorean_triple(n)

    return triplets.most_common(1)[0][0]

    # 返回结果





if __name__ == "__main__":

    print(f"Perimeter {solution()} has maximum solutions")

