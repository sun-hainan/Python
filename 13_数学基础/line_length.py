# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / line_length



本文件实现 line_length 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""









import math

from collections.abc import Callable







# =============================================================================

# 算法模块：line_length

# =============================================================================

def line_length(

    # line_length function



    # line_length function

    fnc: Callable[[float], float],

    x_start: float,

    x_end: float,

    steps: int = 100,

) -> float:

    """

    Approximates the arc length of a line segment by treating the curve as a

    sequence of linear lines and summing their lengths

    :param fnc: a function which defines a curve

    :param x_start: left end point to indicate the start of line segment

    :param x_end: right end point to indicate end of line segment

    :param steps: an accuracy gauge; more steps increases accuracy

    :return: a float representing the length of the curve



    >>> def f(x):

    ...    return x

    >>> f"{line_length(f, 0, 1, 10):.6f}"

    '1.414214'



    >>> def f(x):

    ...    return 1

    >>> f"{line_length(f, -5.5, 4.5):.6f}"

    '10.000000'



    >>> def f(x):

    ...    return math.sin(5 * x) + math.cos(10 * x) + x * x/10

    >>> f"{line_length(f, 0.0, 10.0, 10000):.6f}"

    '69.534930'

    """





    x1 = x_start

    fx1 = fnc(x_start)

    length = 0.0



    for _ in range(steps):

        # Approximates curve as a sequence of linear lines and sums their length

        x2 = (x_end - x_start) / steps + x1

        fx2 = fnc(x2)

        length += math.hypot(x2 - x1, fx2 - fx1)



        # Increment step

        x1 = x2

        fx1 = fx2



    return length





if __name__ == "__main__":



    def f(x):

    # f function



    # f function

        return math.sin(10 * x)



    print("f(x) = sin(10 * x)")

    print("The length of the curve from x = -10 to x = 10 is:")

    i = 10

    while i <= 100000:

        print(f"With {i} steps: {line_length(f, -10, 10, i)}")

        i *= 10

