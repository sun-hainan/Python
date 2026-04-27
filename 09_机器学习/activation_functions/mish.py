# -*- coding: utf-8 -*-
"""
算法实现：activation_functions / mish

本文件实现 mish 相关的算法功能。
"""

import numpy as np

from .softplus import softplus


def mish(vector: np.ndarray) -> np.ndarray:
    # mish function

    # mish function
    """
        Implements the Mish activation function.

        Parameters:
            vector (np.ndarray): The input array for Mish activation.

        Returns:
            np.ndarray: The input array after applying the Mish activation.

        Formula:
            f(x) = x * tanh(softplus(x)) = x * tanh(ln(1 + e^x))

    Examples:
    >>> mish(vector=np.array([2.3,0.6,-2,-3.8]))
    array([ 2.26211893,  0.46613649, -0.25250148, -0.08405831])

    >>> mish(np.array([-9.2, -0.3, 0.45, -4.56]))
    array([-0.00092952, -0.15113318,  0.33152014, -0.04745745])

    """
    return vector * np.tanh(softplus(vector))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
