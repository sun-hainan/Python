# -*- coding: utf-8 -*-
"""
算法实现：numerical_analysis / numerical_integration

本文件实现 numerical_integration 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""


"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""




from collections.abc import Callable



# =============================================================================
# 算法模块：trapezoidal_area
# =============================================================================
def trapezoidal_area(
    # trapezoidal_area function

    # trapezoidal_area function
    fnc: Callable[[float], float],
    x_start: float,
    x_end: float,
    steps: int = 100,
) -> float:
    """
    Treats curve as a collection of linear lines and sums the area of the
    trapezium shape they form
    :param fnc: a function which defines a curve
    :param x_start: left end point to indicate the start of line segment
    :param x_end: right end point to indicate end of line segment
    :param steps: an accuracy gauge; more steps increases the accuracy
    :return: a float representing the length of the curve

    >>> def f(x):
    ...    return 5
    >>> '%.3f' % trapezoidal_area(f, 12.0, 14.0, 1000)
    '10.000'

    >>> def f(x):
    ...    return 9*x**2
    >>> '%.4f' % trapezoidal_area(f, -4.0, 0, 10000)
    '192.0000'

    >>> '%.4f' % trapezoidal_area(f, -4.0, 4.0, 10000)
    '384.0000'
    """
    x1 = x_start
    fx1 = fnc(x_start)
    area = 0.0

    for _ in range(steps):
        # Approximates small segments of curve as linear and solve
        # for trapezoidal area
        x2 = (x_end - x_start) / steps + x1
        fx2 = fnc(x2)
        area += abs(fx2 + fx1) * (x2 - x1) / 2

        # Increment step
        x1 = x2
        fx1 = fx2
    return area


if __name__ == "__main__":

    def f(x):
    # f function

    # f function
        return x**3

    print("f(x) = x^3")
    print("The area between the curve, x = -10, x = 10 and the x axis is:")
    i = 10
    while i <= 100000:
        area = trapezoidal_area(f, -5, 5, i)
        print(f"with {i} steps: {area}")
        i *= 10
