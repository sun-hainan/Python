# -*- coding: utf-8 -*-
"""
Project Euler Problem 203

解决 Project Euler 第 203 题的 Python 实现。
https://projecteuler.net/problem=203
"""

from __future__ import annotations

"""
Project Euler Problem 203 — 中文注释版
https://projecteuler.net/problem=203

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""






# =============================================================================
# Project Euler 问题 203
# =============================================================================
def get_pascal_triangle_unique_coefficients(depth: int) -> set[int]:
    """
    Returns the unique coefficients of a Pascal's triangle of depth "depth".

    The coefficients of this triangle are symmetric. A further improvement to this
    method could be to calculate the coefficients once per level. Nonetheless,
    the current implementation is fast enough for the original problem.

    >>> get_pascal_triangle_unique_coefficients(1)
    {1}
    >>> get_pascal_triangle_unique_coefficients(2)
    {1}
    >>> get_pascal_triangle_unique_coefficients(3)
    {1, 2}
    >>> get_pascal_triangle_unique_coefficients(8)
    {1, 2, 3, 4, 5, 6, 7, 35, 10, 15, 20, 21}
    """
    coefficients = {1}
    previous_coefficients = [1]
    for _ in range(2, depth + 1):
    # 遍历循环
        coefficients_begins_one = [*previous_coefficients, 0]
        coefficients_ends_one = [0, *previous_coefficients]
        previous_coefficients = []
        for x, y in zip(coefficients_begins_one, coefficients_ends_one):
    # 遍历循环
            coefficients.add(x + y)
            previous_coefficients.append(x + y)
    return coefficients
    # 返回结果


def get_squarefrees(unique_coefficients: set[int]) -> set[int]:
    # get_squarefrees 函数实现
    """
    Calculates the squarefree numbers inside unique_coefficients.

    Based on the definition of a non-squarefree number, then any non-squarefree
    n can be decomposed as n = p*p*r, where p is positive prime number and r
    is a positive integer.

    Under the previous formula, any coefficient that is lower than p*p is
    squarefree as r cannot be negative. On the contrary, if any r exists such
    that n = p*p*r, then the number is non-squarefree.

    >>> get_squarefrees({1})
    {1}
    >>> get_squarefrees({1, 2})
    {1, 2}
    >>> get_squarefrees({1, 2, 3, 4, 5, 6, 7, 35, 10, 15, 20, 21})
    {1, 2, 3, 5, 6, 7, 35, 10, 15, 21}
    """

    non_squarefrees = set()
    for number in unique_coefficients:
    # 遍历循环
        divisor = 2
        copy_number = number
        while divisor**2 <= copy_number:
    # 条件循环
            multiplicity = 0
            while copy_number % divisor == 0:
    # 条件循环
                copy_number //= divisor
                multiplicity += 1
            if multiplicity >= 2:
                non_squarefrees.add(number)
                break
            divisor += 1

    return unique_coefficients.difference(non_squarefrees)
    # 返回结果


def solution(n: int = 51) -> int:
    # solution 函数实现
    """
    Returns the sum of squarefrees for a given Pascal's Triangle of depth n.

    >>> solution(1)
    1
    >>> solution(8)
    105
    >>> solution(9)
    175
    """
    unique_coefficients = get_pascal_triangle_unique_coefficients(n)
    squarefrees = get_squarefrees(unique_coefficients)
    return sum(squarefrees)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
