# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / reynolds_number

本文件实现 reynolds_number 相关的算法功能。
"""

# reynolds_number 函数实现
def reynolds_number(
    density: float, velocity: float, diameter: float, viscosity: float
) -> float:
    """
    >>> reynolds_number(900, 2.5, 0.05, 0.4)
    281.25
    >>> reynolds_number(450, 3.86, 0.078, 0.23)
    589.0695652173912
    >>> reynolds_number(234, -4.5, 0.3, 0.44)
    717.9545454545454
    >>> reynolds_number(-90, 2, 0.045, 1)
    Traceback (most recent call last):
        ...
    ValueError: please ensure that density, diameter and viscosity are positive
    >>> reynolds_number(0, 2, -0.4, -2)
    Traceback (most recent call last):
        ...
    ValueError: please ensure that density, diameter and viscosity are positive
    """

    if density <= 0 or diameter <= 0 or viscosity <= 0:
    # 条件判断
        raise ValueError(
            "please ensure that density, diameter and viscosity are positive"
        )
    return (density * abs(velocity) * diameter) / viscosity
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
