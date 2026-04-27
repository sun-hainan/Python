# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / sigmoid

本文件实现 sigmoid 相关的算法功能。
"""

import numpy as np



# =============================================================================
# 算法模块：sigmoid
# =============================================================================
def sigmoid(vector: np.ndarray) -> np.ndarray:
    # sigmoid function

    # sigmoid function
    """
    Implements the sigmoid function

    Parameters:
        vector (np.array): A  numpy array of shape (1,n)
        consisting of real values

    Returns:
        sigmoid_vec (np.array): The input numpy array, after applying
        sigmoid.

    Examples:
    >>> sigmoid(np.array([-1.0, 1.0, 2.0]))
    array([0.26894142, 0.73105858, 0.88079708])

    >>> sigmoid(np.array([0.0]))
    array([0.5])
    """
    return 1 / (1 + np.exp(-vector))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
