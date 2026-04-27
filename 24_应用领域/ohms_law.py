# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / ohms_law

本文件实现 ohms_law 相关的算法功能。
"""

# https://en.wikipedia.org/wiki/Ohm%27s_law
from __future__ import annotations



# ohms_law 函数实现
def ohms_law(voltage: float, current: float, resistance: float) -> dict[str, float]:
    """
    Apply Ohm's Law, on any two given electrical values, which can be voltage, current,
    and resistance, and then in a Python dict return name/value pair of the zero value.

    >>> ohms_law(voltage=10, resistance=5, current=0)
    {'current': 2.0}
    >>> ohms_law(voltage=0, current=0, resistance=10)
    Traceback (most recent call last):
      ...
    ValueError: One and only one argument must be 0
    >>> ohms_law(voltage=0, current=1, resistance=-2)
    Traceback (most recent call last):
      ...
    ValueError: Resistance cannot be negative
    >>> ohms_law(resistance=0, voltage=-10, current=1)
    {'resistance': -10.0}
    >>> ohms_law(voltage=0, current=-1.5, resistance=2)
    {'voltage': -3.0}
    """
    if (voltage, current, resistance).count(0) != 1:
    # 条件判断
        raise ValueError("One and only one argument must be 0")
    if resistance < 0:
    # 条件判断
        raise ValueError("Resistance cannot be negative")
    if voltage == 0:
    # 条件判断
        return {"voltage": float(current * resistance)}
    # 返回结果
    elif current == 0:
        return {"current": voltage / resistance}
    # 返回结果
    elif resistance == 0:
        return {"resistance": voltage / current}
    # 返回结果
    else:
        raise ValueError("Exactly one argument must be 0")


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
