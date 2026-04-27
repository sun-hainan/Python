# -*- coding: utf-8 -*-
"""
算法实现：activation_functions / scaled_exponential_linear_unit

本文件实现 scaled_exponential_linear_unit 相关的算法功能。
"""

import numpy as np


def scaled_exponential_linear_unit(
    vector: np.ndarray, alpha: float = 1.6732, lambda_: float = 1.0507
) -> np.ndarray:
    """
    Applies the Scaled Exponential Linear Unit function to each element of the vector.
    Parameters :
        vector : np.ndarray
        alpha : float (default = 1.6732)
        lambda_ : float (default = 1.0507)

    Returns : np.ndarray
    Formula : f(x) = lambda_ * x if x > 0
                     lambda_ * alpha * (e**x - 1) if x <= 0
    Examples :
    >>> scaled_exponential_linear_unit(vector=np.array([1.3, 3.7, 2.4]))
    array([1.36591, 3.88759, 2.52168])

    >>> scaled_exponential_linear_unit(vector=np.array([1.3, 4.7, 8.2]))
    array([1.36591, 4.93829, 8.61574])
    """
    return lambda_ * np.where(vector > 0, vector, alpha * (np.exp(vector) - 1))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
