# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / softmax

本文件实现 softmax 相关的算法功能。
"""

import numpy as np



# =============================================================================
# 算法模块：softmax
# =============================================================================
def softmax(vector):
    # softmax function

    # softmax function
    """
    Implements the softmax function

    Parameters:
        vector (np.array,list,tuple): A  numpy array of shape (1,n)
        consisting of real values or a similar list,tuple


    Returns:
        softmax_vec (np.array): The input numpy array  after applying
        softmax.

    The softmax vector adds up to one. We need to ceil to mitigate for
    precision
    >>> float(np.ceil(np.sum(softmax([1,2,3,4]))))
    1.0

    >>> vec = np.array([5,5])
    >>> softmax(vec)
    array([0.5, 0.5])

    >>> softmax([0])
    array([1.])
    """

    # Calculate e^x for each x in your vector where e is Euler's
    # number (approximately 2.718)
    exponent_vector = np.exp(vector)

    # Add up the all the exponentials
    sum_of_exponents = np.sum(exponent_vector)

    # Divide every exponent by the sum of all exponents
    softmax_vector = exponent_vector / sum_of_exponents

    return softmax_vector


if __name__ == "__main__":
    print(softmax((0,)))
