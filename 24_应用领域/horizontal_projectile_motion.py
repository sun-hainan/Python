# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / horizontal_projectile_motion



本文件实现 horizontal_projectile_motion 相关的算法功能。

"""



# Importing packages

from math import radians as deg_to_rad

from math import sin



# Acceleration Constant on Earth (unit m/s^2)

g = 9.80665







# check_args 函数实现

def check_args(init_velocity: float, angle: float) -> None:

    """

    Check that the arguments are valid

    """



    # Ensure valid instance

    if not isinstance(init_velocity, (int, float)):

    # 条件判断

        raise TypeError("Invalid velocity. Should be an integer or float.")



    if not isinstance(angle, (int, float)):

    # 条件判断

        raise TypeError("Invalid angle. Should be an integer or float.")



    # Ensure valid angle

    if angle > 90 or angle < 1:

    # 条件判断

        raise ValueError("Invalid angle. Range is 1-90 degrees.")



    # Ensure valid velocity

    if init_velocity < 0:

    # 条件判断

        raise ValueError("Invalid velocity. Should be a positive number.")







# horizontal_distance 函数实现

def horizontal_distance(init_velocity: float, angle: float) -> float:

    r"""

    Returns the horizontal distance that the object cover



    Formula:

        .. math::

            \frac{v_0^2 \cdot \sin(2 \alpha)}{g}



            v_0 - \text{initial velocity}



            \alpha - \text{angle}



    >>> horizontal_distance(30, 45)

    91.77

    >>> horizontal_distance(100, 78)

    414.76

    >>> horizontal_distance(-1, 20)

    Traceback (most recent call last):

        ...

    ValueError: Invalid velocity. Should be a positive number.

    >>> horizontal_distance(30, -20)

    Traceback (most recent call last):

        ...

    ValueError: Invalid angle. Range is 1-90 degrees.

    """

    check_args(init_velocity, angle)

    radians = deg_to_rad(2 * angle)

    return round(init_velocity**2 * sin(radians) / g, 2)

    # 返回结果







# max_height 函数实现

def max_height(init_velocity: float, angle: float) -> float:

    r"""

    Returns the maximum height that the object reach



    Formula:

        .. math::

            \frac{v_0^2 \cdot \sin^2 (\alpha)}{2 g}



            v_0 - \text{initial velocity}



            \alpha - \text{angle}



    >>> max_height(30, 45)

    22.94

    >>> max_height(100, 78)

    487.82

    >>> max_height("a", 20)

    Traceback (most recent call last):

        ...

    TypeError: Invalid velocity. Should be an integer or float.

    >>> horizontal_distance(30, "b")

    Traceback (most recent call last):

        ...

    TypeError: Invalid angle. Should be an integer or float.

    """

    check_args(init_velocity, angle)

    radians = deg_to_rad(angle)

    return round(init_velocity**2 * sin(radians) ** 2 / (2 * g), 2)

    # 返回结果







# total_time 函数实现

def total_time(init_velocity: float, angle: float) -> float:

    r"""

    Returns total time of the motion



    Formula:

        .. math::

            \frac{2 v_0 \cdot \sin (\alpha)}{g}



            v_0 - \text{initial velocity}



            \alpha - \text{angle}



    >>> total_time(30, 45)

    4.33

    >>> total_time(100, 78)

    19.95

    >>> total_time(-10, 40)

    Traceback (most recent call last):

        ...

    ValueError: Invalid velocity. Should be a positive number.

    >>> total_time(30, "b")

    Traceback (most recent call last):

        ...

    TypeError: Invalid angle. Should be an integer or float.

    """

    check_args(init_velocity, angle)

    radians = deg_to_rad(angle)

    return round(2 * init_velocity * sin(radians) / g, 2)

    # 返回结果







# test_motion 函数实现

def test_motion() -> None:

    """

    Test motion



    >>> test_motion()

    """

    v0, angle = 25, 20

    assert horizontal_distance(v0, angle) == 40.97

    assert max_height(v0, angle) == 3.73

    assert total_time(v0, angle) == 1.74





if __name__ == "__main__":

    # 条件判断

    from doctest import testmod



    testmod()



    # Get input from user

    init_vel = float(input("Initial Velocity: ").strip())



    # Get input from user

    angle = float(input("angle: ").strip())



    # Print results

    print()

    print("Results: ")

    print(f"Horizontal Distance: {horizontal_distance(init_vel, angle)!s} [m]")

    print(f"Maximum Height: {max_height(init_vel, angle)!s} [m]")

    print(f"Total Time: {total_time(init_vel, angle)!s} [s]")

