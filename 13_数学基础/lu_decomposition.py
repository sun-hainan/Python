# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / lu_decomposition

本文件实现 lu_decomposition 相关的算法功能。
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




import numpy as np



# =============================================================================
# 算法模块：lower_upper_decomposition
# =============================================================================
def lower_upper_decomposition(table: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # lower_upper_decomposition function

    # lower_upper_decomposition function
    """
    Perform LU decomposition on a given matrix and raises an error if the matrix
    isn't square or if no such decomposition exists

    >>> matrix = np.array([[2, -2, 1], [0, 1, 2], [5, 3, 1]])
    >>> lower_mat, upper_mat = lower_upper_decomposition(matrix)
    >>> lower_mat
    array([[1. , 0. , 0. ],
           [0. , 1. , 0. ],
           [2.5, 8. , 1. ]])
    >>> upper_mat
    array([[  2. ,  -2. ,   1. ],
           [  0. ,   1. ,   2. ],
           [  0. ,   0. , -17.5]])

    >>> matrix = np.array([[4, 3], [6, 3]])
    >>> lower_mat, upper_mat = lower_upper_decomposition(matrix)
    >>> lower_mat
    array([[1. , 0. ],
           [1.5, 1. ]])
    >>> upper_mat
    array([[ 4. ,  3. ],
           [ 0. , -1.5]])

    >>> # Matrix is not square
    >>> matrix = np.array([[2, -2, 1], [0, 1, 2]])
    >>> lower_mat, upper_mat = lower_upper_decomposition(matrix)
    Traceback (most recent call last):
        ...
    ValueError: 'table' has to be of square shaped array but got a 2x3 array:
    [[ 2 -2  1]
     [ 0  1  2]]

    >>> # Matrix is invertible, but its first leading principal minor is 0
    >>> matrix = np.array([[0, 1], [1, 0]])
    >>> lower_mat, upper_mat = lower_upper_decomposition(matrix)
    Traceback (most recent call last):
    ...
    ArithmeticError: No LU decomposition exists

    >>> # Matrix is singular, but its first leading principal minor is 1
    >>> matrix = np.array([[1, 0], [1, 0]])
    >>> lower_mat, upper_mat = lower_upper_decomposition(matrix)
    >>> lower_mat
    array([[1., 0.],
           [1., 1.]])
    >>> upper_mat
    array([[1., 0.],
           [0., 0.]])

    >>> # Matrix is singular, but its first leading principal minor is 0
    >>> matrix = np.array([[0, 1], [0, 1]])
    >>> lower_mat, upper_mat = lower_upper_decomposition(matrix)
    Traceback (most recent call last):
    ...
    ArithmeticError: No LU decomposition exists
    """
    # Ensure that table is a square array
    rows, columns = np.shape(table)
    if rows != columns:
        msg = (
            "'table' has to be of square shaped array but got a "
            f"{rows}x{columns} array:\n{table}"
        )
        raise ValueError(msg)

    lower = np.zeros((rows, columns))
    upper = np.zeros((rows, columns))

    # in 'total', the necessary data is extracted through slices
    # and the sum of the products is obtained.

    for i in range(columns):
        for j in range(i):
            total = np.sum(lower[i, :i] * upper[:i, j])
            if upper[j][j] == 0:
                raise ArithmeticError("No LU decomposition exists")
            lower[i][j] = (table[i][j] - total) / upper[j][j]
        lower[i][i] = 1
        for j in range(i, columns):
            total = np.sum(lower[i, :i] * upper[:i, j])
            upper[i][j] = table[i][j] - total
    return lower, upper


if __name__ == "__main__":
    import doctest

    doctest.testmod()
