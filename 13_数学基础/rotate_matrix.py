# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / rotate_matrix

本文件实现 rotate_matrix 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""


"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""






# =============================================================================
# 算法模块：make_matrix
# =============================================================================
def make_matrix(row_size: int = 4) -> list[list[int]]:
    # make_matrix function

    # make_matrix function
    """
    >>> make_matrix()
    [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
    >>> make_matrix(1)
    [[1]]
    >>> make_matrix(-2)
    [[1, 2], [3, 4]]
    >>> make_matrix(3)
    [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    >>> make_matrix() == make_matrix(4)
    True
    """
    row_size = abs(row_size) or 4
    return [[1 + x + y * row_size for x in range(row_size)] for y in range(row_size)]


def rotate_90(matrix: list[list[int]]) -> list[list[int]]:
    # rotate_90 function

    # rotate_90 function
    """
    >>> rotate_90(make_matrix())
    [[4, 8, 12, 16], [3, 7, 11, 15], [2, 6, 10, 14], [1, 5, 9, 13]]
    >>> rotate_90(make_matrix()) == transpose(reverse_column(make_matrix()))
    True
    """

    return reverse_row(transpose(matrix))
    # OR.. transpose(reverse_column(matrix))


def rotate_180(matrix: list[list[int]]) -> list[list[int]]:
    # rotate_180 function

    # rotate_180 function
    """
    >>> rotate_180(make_matrix())
    [[16, 15, 14, 13], [12, 11, 10, 9], [8, 7, 6, 5], [4, 3, 2, 1]]
    >>> rotate_180(make_matrix()) == reverse_column(reverse_row(make_matrix()))
    True
    """

    return reverse_row(reverse_column(matrix))
    # OR.. reverse_column(reverse_row(matrix))


def rotate_270(matrix: list[list[int]]) -> list[list[int]]:
    # rotate_270 function

    # rotate_270 function
    """
    >>> rotate_270(make_matrix())
    [[13, 9, 5, 1], [14, 10, 6, 2], [15, 11, 7, 3], [16, 12, 8, 4]]
    >>> rotate_270(make_matrix()) == transpose(reverse_row(make_matrix()))
    True
    """

    return reverse_column(transpose(matrix))
    # OR.. transpose(reverse_row(matrix))


def transpose(matrix: list[list[int]]) -> list[list[int]]:
    # transpose function

    # transpose function
    matrix[:] = [list(x) for x in zip(*matrix)]
    return matrix


def reverse_row(matrix: list[list[int]]) -> list[list[int]]:
    # reverse_row function

    # reverse_row function
    matrix[:] = matrix[::-1]
    return matrix


def reverse_column(matrix: list[list[int]]) -> list[list[int]]:
    # reverse_column function

    # reverse_column function
    matrix[:] = [x[::-1] for x in matrix]
    return matrix


def print_matrix(matrix: list[list[int]]) -> None:
    # print_matrix function

    # print_matrix function
    for i in matrix:
        print(*i)


if __name__ == "__main__":
    matrix = make_matrix()
    print("\norigin:\n")
    print_matrix(matrix)
    print("\nrotate 90 counterclockwise:\n")
    print_matrix(rotate_90(matrix))

    matrix = make_matrix()
    print("\norigin:\n")
    print_matrix(matrix)
    print("\nrotate 180:\n")
    print_matrix(rotate_180(matrix))

    matrix = make_matrix()
    print("\norigin:\n")
    print_matrix(matrix)
    print("\nrotate 270 counterclockwise:\n")
    print_matrix(rotate_270(matrix))
