# -*- coding: utf-8 -*-

"""

Project Euler Problem 121



解决 Project Euler 第 121 题的 Python 实现。

https://projecteuler.net/problem=121

"""



from itertools import product







# =============================================================================

# Project Euler 问题 121

# =============================================================================

def solution(num_turns: int = 15) -> int:

    """

    Find the maximum prize fund that should be allocated to a single game in which

    fifteen turns are played.

    >>> solution(4)

    10

    >>> solution(10)

    225

    """

    total_prob: float = 0.0

    prob: float

    num_blue: int

    num_red: int

    ind: int

    col: int

    series: tuple[int, ...]



    for series in product(range(2), repeat=num_turns):

    # 遍历循环

        num_blue = series.count(1)

        num_red = num_turns - num_blue

        if num_red >= num_blue:

            continue

        prob = 1.0

        for ind, col in enumerate(series, 2):

    # 遍历循环

            if col == 0:

                prob *= (ind - 1) / ind

            else:

                prob *= 1 / ind



        total_prob += prob



    return int(1 / total_prob)

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

