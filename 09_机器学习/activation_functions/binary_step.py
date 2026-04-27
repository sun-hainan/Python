# -*- coding: utf-8 -*-
"""
算法实现：activation_functions / binary_step

本文件实现 binary_step 相关的算法功能。
"""

import numpy as np


def binary_step(vector: np.ndarray) -> np.ndarray:
    """
    Implements the binary step function

    Parameters:
        vector (ndarray): A vector that consists of numeric values

    Returns:
        vector (ndarray): Input vector after applying binary step function

    >>> vector = np.array([-1.2, 0, 2, 1.45, -3.7, 0.3])
    >>> binary_step(vector)
    array([0, 1, 1, 1, 0, 1])
    """

    return np.where(vector >= 0, 1, 0)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
