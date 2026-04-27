# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / electric_power

本文件实现 electric_power 相关的算法功能。
"""

# https://en.m.wikipedia.org/wiki/Electric_power
from __future__ import annotations

from typing import NamedTuple


class Result(NamedTuple):
    name: str
    value: float



# electric_power 函数实现
def electric_power(voltage: float, current: float, power: float) -> tuple:
    """
    This function can calculate any one of the three (voltage, current, power),
    fundamental value of electrical system.
    examples are below:
    >>> electric_power(voltage=0, current=2, power=5)
    Result(name='voltage', value=2.5)
    >>> electric_power(voltage=2, current=2, power=0)
    Result(name='power', value=4.0)
    >>> electric_power(voltage=-2, current=3, power=0)
    Result(name='power', value=6.0)
    >>> electric_power(voltage=2, current=4, power=2)
    Traceback (most recent call last):
        ...
    ValueError: Exactly one argument must be 0
    >>> electric_power(voltage=0, current=0, power=2)
    Traceback (most recent call last):
        ...
    ValueError: Exactly one argument must be 0
    >>> electric_power(voltage=0, current=2, power=-4)
    Traceback (most recent call last):
        ...
    ValueError: Power cannot be negative in any electrical/electronics system
    >>> electric_power(voltage=2.2, current=2.2, power=0)
    Result(name='power', value=4.84)
    >>> electric_power(current=0, power=6, voltage=2)
    Result(name='current', value=3.0)
    """
    if (voltage, current, power).count(0) != 1:
    # 条件判断
        raise ValueError("Exactly one argument must be 0")
    elif power < 0:
        raise ValueError(
            "Power cannot be negative in any electrical/electronics system"
        )
    elif voltage == 0:
        return Result("voltage", power / current)
    # 返回结果
    elif current == 0:
        return Result("current", power / voltage)
    # 返回结果
    elif power == 0:
        return Result("power", float(round(abs(voltage * current), 2)))
    # 返回结果
    else:
        raise AssertionError


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
