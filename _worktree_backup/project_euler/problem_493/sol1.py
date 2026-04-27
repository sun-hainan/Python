# -*- coding: utf-8 -*-
"""
Project Euler Problem 493

解决 Project Euler 第 493 题的 Python 实现。
https://projecteuler.net/problem=493
"""

import math

BALLS_PER_COLOUR = 10
NUM_COLOURS = 7
NUM_BALLS = BALLS_PER_COLOUR * NUM_COLOURS



# =============================================================================
# Project Euler 问题 493
# =============================================================================
def solution(num_picks: int = 20) -> str:
    """
    Calculates the expected number of distinct colours

    >>> solution(10)
    '5.669644129'

    >>> solution(30)
    '6.985042712'
    """
    total = math.comb(NUM_BALLS, num_picks)
    missing_colour = math.comb(NUM_BALLS - BALLS_PER_COLOUR, num_picks)

    result = NUM_COLOURS * (1 - missing_colour / total)

    return f"{result:.9f}"
    # 返回结果


if __name__ == "__main__":
    print(solution(20))
