# -*- coding: utf-8 -*-
"""
Project Euler Problem 085

解决 Project Euler 第 085 题的 Python 实现。
https://projecteuler.net/problem=085
"""

from __future__ import annotations

"""
Project Euler Problem 085 — 中文注释版
https://projecteuler.net/problem=085

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




from math import ceil, floor, sqrt



# =============================================================================
# Project Euler 问题 085
# =============================================================================
def solution(target: int = 2000000) -> int:
    """
    Find the area of the grid which contains as close to two million rectangles
    as possible.
    >>> solution(20)
    6
    >>> solution(2000)
    72
    >>> solution(2000000000)
    86595
    """
    triangle_numbers: list[int] = [0]
    idx: int

    for idx in range(1, ceil(sqrt(target * 2) * 1.1)):
    # 遍历循环
        triangle_numbers.append(triangle_numbers[-1] + idx)

    # we want this to be as close as possible to target
    best_product: int = 0
    # the area corresponding to the grid that gives the product closest to target
    area: int = 0
    # an estimate of b, using the quadratic formula
    b_estimate: float
    # the largest integer less than b_estimate
    b_floor: int
    # the largest integer less than b_estimate
    b_ceil: int
    # the triangle number corresponding to b_floor
    triangle_b_first_guess: int
    # the triangle number corresponding to b_ceil
    triangle_b_second_guess: int

    for idx_a, triangle_a in enumerate(triangle_numbers[1:], 1):
    # 遍历循环
        b_estimate = (-1 + sqrt(1 + 8 * target / triangle_a)) / 2
        b_floor = floor(b_estimate)
        b_ceil = ceil(b_estimate)
        triangle_b_first_guess = triangle_numbers[b_floor]
        triangle_b_second_guess = triangle_numbers[b_ceil]

        if abs(target - triangle_b_first_guess * triangle_a) < abs(
            target - best_product
        ):
            best_product = triangle_b_first_guess * triangle_a
            area = idx_a * b_floor

        if abs(target - triangle_b_second_guess * triangle_a) < abs(
            target - best_product
        ):
            best_product = triangle_b_second_guess * triangle_a
            area = idx_a * b_ceil

    return area
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
