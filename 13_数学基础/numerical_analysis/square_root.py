# -*- coding: utf-8 -*-

"""

算法实现：numerical_analysis / square_root



本文件实现 square_root 相关的算法功能。

"""



import math







# =============================================================================

# 算法模块：fx

# =============================================================================

def fx(x: float, a: float) -> float:

    # fx function



    # fx function

    return math.pow(x, 2) - a





def fx_derivative(x: float) -> float:

    # fx_derivative function



    # fx_derivative function

    return 2 * x





def get_initial_point(a: float) -> float:

    # get_initial_point function



    # get_initial_point function

    start = 2.0



    while start <= a:

        start = math.pow(start, 2)



    return start





def square_root_iterative(

    # square_root_iterative function



    # square_root_iterative function

    a: float, max_iter: int = 9999, tolerance: float = 1e-14

) -> float:

    """

    Square root approximated using Newton's method.

    https://en.wikipedia.org/wiki/Newton%27s_method



    >>> all(abs(square_root_iterative(i) - math.sqrt(i)) <= 1e-14 for i in range(500))

    True



    >>> square_root_iterative(-1)

    Traceback (most recent call last):

        ...

    ValueError: math domain error



    >>> square_root_iterative(4)

    2.0



    >>> square_root_iterative(3.2)

    1.788854381999832



    >>> square_root_iterative(140)

    11.832159566199232

    """





    if a < 0:

        raise ValueError("math domain error")



    value = get_initial_point(a)



    for _ in range(max_iter):

        prev_value = value

        value = value - fx(value, a) / fx_derivative(value)

        if abs(prev_value - value) < tolerance:

            return value



    return value





if __name__ == "__main__":

    from doctest import testmod



    testmod()

