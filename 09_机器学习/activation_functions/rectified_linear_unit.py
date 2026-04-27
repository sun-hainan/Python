# -*- coding: utf-8 -*-
"""
算法实现：activation_functions / rectified_linear_unit

本文件实现 rectified_linear_unit 相关的算法功能。
"""

from __future__ import annotations

import numpy as np


def relu(vector: list[float]):
    """
    Implements the relu function

    Parameters:
        vector (np.array,list,tuple): A  numpy array of shape (1,n)
        consisting of real values or a similar list,tuple


    Returns:
        relu_vec (np.array): The input numpy array, after applying
        relu.

    >>> vec = np.array([-1, 0, 5])
    >>> relu(vec)
    array([0, 0, 5])
    """

    # compare two arrays and then return element-wise maxima.
    return np.maximum(0, vector)


if __name__ == "__main__":
    print(np.array(relu([-1, 0, 5])))  # --> [0, 0, 5]
