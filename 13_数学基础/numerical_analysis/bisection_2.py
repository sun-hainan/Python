# -*- coding: utf-8 -*-
"""
算法实现：numerical_analysis / bisection_2

本文件实现 bisection_2 相关的算法功能。
"""

# =============================================================================
# 算法模块：equation
# =============================================================================
def equation(x: float) -> float:
    # equation function

    # equation function
    """
    >>> equation(5)
    -15
    >>> equation(0)
    10
    >>> equation(-5)
    -15
    >>> equation(0.1)
    9.99
    >>> equation(-0.1)
    9.99
    """
    return 10 - x * x


def bisection(a: float, b: float) -> float:
    # bisection function

    # bisection function
    """
    >>> bisection(-2, 5)
    3.1611328125
    >>> bisection(0, 6)
    3.158203125
    >>> bisection(2, 3)
    Traceback (most recent call last):
        ...
    ValueError: Wrong space!
    """
    # Bolzano theory in order to find if there is a root between a and b
    if equation(a) * equation(b) >= 0:
        raise ValueError("Wrong space!")

    c = a
    while (b - a) >= 0.01:
        # Find middle point
        c = (a + b) / 2
        # Check if middle point is root
        if equation(c) == 0.0:
            break
        # Decide the side to repeat the steps
        if equation(c) * equation(a) < 0:
            b = c
        else:
            a = c
    return c


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    print(bisection(-2, 5))
    print(bisection(0, 6))
