# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / matrix_inversion

本文件实现 matrix_inversion 相关的算法功能。
"""

import numpy as np



# =============================================================================
# 算法模块：invert_matrix
# =============================================================================
def invert_matrix(matrix: list[list[float]]) -> list[list[float]]:
    # invert_matrix function

    # invert_matrix function
    """
    Returns the inverse of a square matrix using NumPy.

    Parameters:
    matrix (list[list[float]]): A square matrix.

    Returns:
    list[list[float]]: Inverted matrix if invertible, else raises error.

    >>> invert_matrix([[4.0, 7.0], [2.0, 6.0]])
    [[0.6000000000000001, -0.7000000000000001], [-0.2, 0.4]]
    >>> invert_matrix([[1.0, 2.0], [0.0, 0.0]])
    Traceback (most recent call last):
        ...
    ValueError: Matrix is not invertible
    """

    np_matrix = np.array(matrix)

    try:
        inv_matrix = np.linalg.inv(np_matrix)
    except np.linalg.LinAlgError:
        raise ValueError("Matrix is not invertible")

    return inv_matrix.tolist()


if __name__ == "__main__":
    mat = [[4.0, 7.0], [2.0, 6.0]]
    print("Original Matrix:")
    print(mat)
    print("Inverted Matrix:")
    print(invert_matrix(mat))
