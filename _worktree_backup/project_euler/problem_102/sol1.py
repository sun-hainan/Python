# -*- coding: utf-8 -*-
"""
Project Euler Problem 102

解决 Project Euler 第 102 题的 Python 实现。
https://projecteuler.net/problem=102
"""

from __future__ import annotations

"""
Project Euler Problem 102 — 中文注释版
https://projecteuler.net/problem=102

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




from pathlib import Path



# =============================================================================
# Project Euler 问题 102
# =============================================================================
def vector_product(point1: tuple[int, int], point2: tuple[int, int]) -> int:
    """
    Return the 2-d vector product of two vectors.
    >>> vector_product((1, 2), (-5, 0))
    10
    >>> vector_product((3, 1), (6, 10))
    24
    """
    return point1[0] * point2[1] - point1[1] * point2[0]
    # 返回结果


def contains_origin(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int) -> bool:
    # contains_origin 函数实现
    """
    Check if the triangle given by the points A(x1, y1), B(x2, y2), C(x3, y3)
    contains the origin.
    >>> contains_origin(-340, 495, -153, -910, 835, -947)
    True
    >>> contains_origin(-175, 41, -421, -714, 574, -645)
    False
    """
    point_a: tuple[int, int] = (x1, y1)
    point_a_to_b: tuple[int, int] = (x2 - x1, y2 - y1)
    point_a_to_c: tuple[int, int] = (x3 - x1, y3 - y1)
    a: float = -vector_product(point_a, point_a_to_b) / vector_product(
        point_a_to_c, point_a_to_b
    )
    b: float = +vector_product(point_a, point_a_to_c) / vector_product(
        point_a_to_c, point_a_to_b
    )

    return a > 0 and b > 0 and a + b < 1
    # 返回结果


def solution(filename: str = "p102_triangles.txt") -> int:
    # solution 函数实现
    """
    Find the number of triangles whose interior contains the origin.
    >>> solution("test_triangles.txt")
    1
    """
    data: str = Path(__file__).parent.joinpath(filename).read_text(encoding="utf-8")

    triangles: list[list[int]] = []
    for line in data.strip().split("\n"):
    # 遍历循环
        triangles.append([int(number) for number in line.split(",")])

    ret: int = 0
    triangle: list[int]

    for triangle in triangles:
    # 遍历循环
        ret += contains_origin(*triangle)

    return ret
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
