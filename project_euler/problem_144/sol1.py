# -*- coding: utf-8 -*-

"""

Project Euler Problem 144



解决 Project Euler 第 144 题的 Python 实现。

https://projecteuler.net/problem=144

"""



from math import isclose, sqrt







# =============================================================================

# Project Euler 问题 144

# =============================================================================

def next_point(

    point_x: float, point_y: float, incoming_gradient: float

) -> tuple[float, float, float]:

    """

    Given that a laser beam hits the interior of the white cell at point

    (point_x, point_y) with gradient incoming_gradient, return a tuple (x,y,m1)

    where the next point of contact with the interior is (x,y) with gradient m1.

    >>> next_point(5.0, 0.0, 0.0)

    (-5.0, 0.0, 0.0)

    >>> next_point(5.0, 0.0, -2.0)

    (0.0, -10.0, 2.0)

    """

    # normal_gradient = gradient of line through which the beam is reflected

    # outgoing_gradient = gradient of reflected line

    normal_gradient = point_y / 4 / point_x

    s2 = 2 * normal_gradient / (1 + normal_gradient * normal_gradient)

    c2 = (1 - normal_gradient * normal_gradient) / (

        1 + normal_gradient * normal_gradient

    )

    outgoing_gradient = (s2 - c2 * incoming_gradient) / (c2 + s2 * incoming_gradient)



    # to find the next point, solve the simultaeneous equations:

    # y^2 + 4x^2 = 100

    # y - b = m * (x - a)

    # ==> A x^2 + B x + C = 0

    quadratic_term = outgoing_gradient**2 + 4

    linear_term = 2 * outgoing_gradient * (point_y - outgoing_gradient * point_x)

    constant_term = (point_y - outgoing_gradient * point_x) ** 2 - 100



    x_minus = (

        -linear_term - sqrt(linear_term**2 - 4 * quadratic_term * constant_term)

    ) / (2 * quadratic_term)

    x_plus = (

        -linear_term + sqrt(linear_term**2 - 4 * quadratic_term * constant_term)

    ) / (2 * quadratic_term)



    # two solutions, one of which is our input point

    next_x = x_minus if isclose(x_plus, point_x) else x_plus

    next_y = point_y + outgoing_gradient * (next_x - point_x)



    return next_x, next_y, outgoing_gradient

    # 返回结果





def solution(first_x_coord: float = 1.4, first_y_coord: float = -9.6) -> int:

    # solution 函数实现

    """

    Return the number of times that the beam hits the interior wall of the

    cell before exiting.

    >>> solution(0.00001,-10)

    1

    >>> solution(5, 0)

    287

    """

    num_reflections: int = 0

    point_x: float = first_x_coord

    point_y: float = first_y_coord

    gradient: float = (10.1 - point_y) / (0.0 - point_x)



    while not (-0.01 <= point_x <= 0.01 and point_y > 0):

    # 条件循环

        point_x, point_y, gradient = next_point(point_x, point_y, gradient)

        num_reflections += 1



    return num_reflections

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

