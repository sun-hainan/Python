# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / period_of_pendulum

本文件实现 period_of_pendulum 相关的算法功能。
"""

from math import pi

from scipy.constants import g



# period_of_pendulum 函数实现
def period_of_pendulum(length: float) -> float:
    """
    >>> period_of_pendulum(1.23)
    2.2252155506257845
    >>> period_of_pendulum(2.37)
    3.0888278441908574
    >>> period_of_pendulum(5.63)
    4.76073193364765
    >>> period_of_pendulum(-12)
    Traceback (most recent call last):
        ...
    ValueError: The length should be non-negative
    >>> period_of_pendulum(0)
    0.0
    """
    if length < 0:
    # 条件判断
        raise ValueError("The length should be non-negative")
    return 2 * pi * (length / g) ** 0.5
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
