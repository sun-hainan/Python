# -*- coding: utf-8 -*-

"""

算法实现：activation_functions / softplus



本文件实现 softplus 相关的算法功能。

"""



import numpy as np





def softplus(vector: np.ndarray) -> np.ndarray:

    # softplus function



    # softplus function

    """

    Implements the Softplus activation function.



    Parameters:

        vector (np.ndarray): The input array for the Softplus activation.



    Returns:

        np.ndarray: The input array after applying the Softplus activation.



    Formula: f(x) = ln(1 + e^x)



    Examples:

    >>> softplus(np.array([2.3, 0.6, -2, -3.8]))

    array([2.39554546, 1.03748795, 0.12692801, 0.02212422])



    >>> softplus(np.array([-9.2, -0.3, 0.45, -4.56]))

    array([1.01034298e-04, 5.54355244e-01, 9.43248946e-01, 1.04077103e-02])

    """

    return np.log(1 + np.exp(vector))





if __name__ == "__main__":

    import doctest



    doctest.testmod()

