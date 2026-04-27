# -*- coding: utf-8 -*-
"""
Project Euler Problem 082

解决 Project Euler 第 082 题的 Python 实现。
https://projecteuler.net/problem=082
"""

import os



# =============================================================================
# Project Euler 问题 082
# =============================================================================
def solution(filename: str = "input.txt") -> int:
    """
    Returns the minimal path sum in the matrix from the file, by starting in any cell
    in the left column and finishing in any cell in the right column,
    and only moving up, down, and right

    >>> solution("test_matrix.txt")
    994
    """

    with open(os.path.join(os.path.dirname(__file__), filename)) as input_file:
        matrix = [
            [int(element) for element in line.split(",")]
            for line in input_file.readlines()
    # 遍历循环
        ]

    rows = len(matrix)
    cols = len(matrix[0])

    minimal_path_sums = [[-1 for _ in range(cols)] for _ in range(rows)]
    for i in range(rows):
    # 遍历循环
        minimal_path_sums[i][0] = matrix[i][0]

    for j in range(1, cols):
    # 遍历循环
        for i in range(rows):
            minimal_path_sums[i][j] = minimal_path_sums[i][j - 1] + matrix[i][j]

        for i in range(1, rows):
    # 遍历循环
            minimal_path_sums[i][j] = min(
                minimal_path_sums[i][j], minimal_path_sums[i - 1][j] + matrix[i][j]
            )

        for i in range(rows - 2, -1, -1):
    # 遍历循环
            minimal_path_sums[i][j] = min(
                minimal_path_sums[i][j], minimal_path_sums[i + 1][j] + matrix[i][j]
            )

    return min(minimal_path_sums_row[-1] for minimal_path_sums_row in minimal_path_sums)


if __name__ == "__main__":
    print(f"{solution() = }")
