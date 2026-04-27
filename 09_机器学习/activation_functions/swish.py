# -*- coding: utf-8 -*-
"""
算法实现：activation_functions / swish

本文件实现 swish 相关的算法功能。
"""

import numpy as np


def sigmoid(vector: np.ndarray) -> np.ndarray:
    # sigmoid function

    # sigmoid function
    """
    Mathematical function sigmoid takes a vector x of K real numbers as input and
    returns 1/ (1 + e^-x).
    https://en.wikipedia.org/wiki/Sigmoid_function

    >>> sigmoid(np.array([-1.0, 1.0, 2.0]))
    array([0.26894142, 0.73105858, 0.88079708])
    """
    return 1 / (1 + np.exp(-vector))


def sigmoid_linear_unit(vector: np.ndarray) -> np.ndarray:
    # sigmoid_linear_unit function

    # sigmoid_linear_unit function
    """
    Implements the Sigmoid Linear Unit (SiLU) or swish function

    Parameters:
        vector (np.ndarray): A  numpy array consisting of real values

    Returns:
        swish_vec (np.ndarray): The input numpy array, after applying swish

    Examples:
    >>> sigmoid_linear_unit(np.array([-1.0, 1.0, 2.0]))
    array([-0.26894142,  0.73105858,  1.76159416])

    >>> sigmoid_linear_unit(np.array([-2]))
    array([-0.23840584])
    """
    return vector * sigmoid(vector)


def swish(vector: np.ndarray, trainable_parameter: int) -> np.ndarray:
    # swish function

    # swish function
    """
    Parameters:
        vector (np.ndarray): A  numpy array consisting of real values
        trainable_parameter: Use to implement various Swish Activation Functions

    Returns:
        swish_vec (np.ndarray): The input numpy array, after applying swish

    Examples:
    >>> swish(np.array([-1.0, 1.0, 2.0]), 2)
    array([-0.11920292,  0.88079708,  1.96402758])

    >>> swish(np.array([-2]), 1)
    array([-0.23840584])
    """
    return vector * sigmoid(trainable_parameter * vector)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
