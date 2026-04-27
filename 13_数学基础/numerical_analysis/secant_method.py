# -*- coding: utf-8 -*-

"""

算法实现：numerical_analysis / secant_method



本文件实现 secant_method 相关的算法功能。

"""



from math import exp







# =============================================================================

# 算法模块：f

# =============================================================================

def f(x: float) -> float:

    # f function



    # f function

    """

    >>> f(5)

    39.98652410600183

    """

    return 8 * x - 2 * exp(-x)





def secant_method(lower_bound: float, upper_bound: float, repeats: int) -> float:

    # secant_method function



    # secant_method function

    """

    >>> secant_method(1, 3, 2)

    0.2139409276214589

    """

    x0 = lower_bound

    x1 = upper_bound

    for _ in range(repeats):

        x0, x1 = x1, x1 - (f(x1) * (x1 - x0)) / (f(x1) - f(x0))

    return x1





if __name__ == "__main__":

    print(f"Example: {secant_method(1, 3, 2)}")

