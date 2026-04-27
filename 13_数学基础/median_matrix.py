# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / median_matrix

本文件实现 median_matrix 相关的算法功能。
"""

# =============================================================================
# 算法模块：median
# =============================================================================
def median(matrix: list[list[int]]) -> int:
    # median function

    # median function
    """
    Calculate the median of a sorted matrix.

    Args:
        matrix: A 2D matrix of integers.

    Returns:
        The median value of the matrix.

    Examples:
        >>> matrix = [[1, 3, 5], [2, 6, 9], [3, 6, 9]]
        >>> median(matrix)
        5

        >>> matrix = [[1, 2, 3], [4, 5, 6]]
        >>> median(matrix)
        3
    """
    # Flatten the matrix into a sorted 1D list
    linear = sorted(num for row in matrix for num in row)

    # Calculate the middle index
    mid = (len(linear) - 1) // 2

    # Return the median
    return linear[mid]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
