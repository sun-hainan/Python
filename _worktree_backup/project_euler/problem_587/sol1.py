# -*- coding: utf-8 -*-
"""
Project Euler Problem 587

解决 Project Euler 第 587 题的 Python 实现。
https://projecteuler.net/problem=587
"""

from itertools import count
from math import asin, pi, sqrt



# =============================================================================
# Project Euler 问题 587
# =============================================================================
def circle_bottom_arc_integral(point: float) -> float:
    """
    Returns integral of circle bottom arc y = 1 / 2 - sqrt(1 / 4 - (x - 1 / 2) ^ 2)

    >>> circle_bottom_arc_integral(0)
    0.39269908169872414

    >>> circle_bottom_arc_integral(1 / 2)
    0.44634954084936207

    >>> circle_bottom_arc_integral(1)
    0.5
    """

    return (
    # 返回结果
        (1 - 2 * point) * sqrt(point - point**2) + 2 * point + asin(sqrt(1 - point))
    ) / 4


def concave_triangle_area(circles_number: int) -> float:
    # concave_triangle_area 函数实现
    """
    Returns area of concave triangle

    >>> concave_triangle_area(1)
    0.026825229575318944

    >>> concave_triangle_area(2)
    0.01956236140083944
    """

    intersection_y = (circles_number + 1 - sqrt(2 * circles_number)) / (
        2 * (circles_number**2 + 1)
    )
    intersection_x = circles_number * intersection_y

    triangle_area = intersection_x * intersection_y / 2
    concave_region_area = circle_bottom_arc_integral(
        1 / 2
    ) - circle_bottom_arc_integral(intersection_x)

    return triangle_area + concave_region_area
    # 返回结果


def solution(fraction: float = 1 / 1000) -> int:
    # solution 函数实现
    """
    Returns least value of n
    for which the concave triangle occupies less than fraction of the L-section
    # 遍历循环

    >>> solution(1 / 10)
    15
    """

    l_section_area = (1 - pi / 4) / 4

    for n in count(1):
    # 遍历循环
        if concave_triangle_area(n) / l_section_area < fraction:
            return n
    # 返回结果

    return -1
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
