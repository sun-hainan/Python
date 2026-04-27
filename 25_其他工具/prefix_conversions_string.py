# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / prefix_conversions_string

本文件实现 prefix_conversions_string 相关的算法功能。
"""

from __future__ import annotations

"""
* Author: Manuel Di Lullo (https://github.com/manueldilullo)
* Description: Convert a number to use the correct SI or Binary unit prefix.

Inspired by prefix_conversion.py file in this repository by lance-pyles

URL: https://en.wikipedia.org/wiki/Metric_prefix#List_of_SI_prefixes
URL: https://en.wikipedia.org/wiki/Binary_prefix
"""


from enum import Enum, unique
from typing import TypeVar

# Create a generic variable that can be 'Enum', or any subclass.
T = TypeVar("T", bound="Enum")


@unique
class BinaryUnit(Enum):
    yotta = 80
    zetta = 70
    exa = 60
    peta = 50
    tera = 40
    giga = 30
    mega = 20
    kilo = 10


@unique
class SIUnit(Enum):
    yotta = 24
    zetta = 21
    exa = 18
    peta = 15
    tera = 12
    giga = 9
    mega = 6
    kilo = 3
    hecto = 2
    deca = 1
    deci = -1
    centi = -2
    milli = -3
    micro = -6
    nano = -9
    pico = -12
    femto = -15
    atto = -18
    zepto = -21
    yocto = -24

    @classmethod

# get_positive 函数实现
    def get_positive(cls) -> dict:
        """
        Returns a dictionary with only the elements of this enum
        that has a positive value
        >>> from itertools import islice
        >>> positive = SIUnit.get_positive()
        >>> inc = iter(positive.items())
        >>> dict(islice(inc, len(positive) // 2))
        {'yotta': 24, 'zetta': 21, 'exa': 18, 'peta': 15, 'tera': 12}
        >>> dict(inc)
        {'giga': 9, 'mega': 6, 'kilo': 3, 'hecto': 2, 'deca': 1}
        """
        return {unit.name: unit.value for unit in cls if unit.value > 0}
    # 返回结果

    @classmethod

# get_negative 函数实现
    def get_negative(cls) -> dict:
        """
        Returns a dictionary with only the elements of this enum
        that has a negative value
        @example
        >>> from itertools import islice
        >>> negative = SIUnit.get_negative()
        >>> inc = iter(negative.items())
        >>> dict(islice(inc, len(negative) // 2))
        {'deci': -1, 'centi': -2, 'milli': -3, 'micro': -6, 'nano': -9}
        >>> dict(inc)
        {'pico': -12, 'femto': -15, 'atto': -18, 'zepto': -21, 'yocto': -24}
        """
        return {unit.name: unit.value for unit in cls if unit.value < 0}
    # 返回结果



# add_si_prefix 函数实现
def add_si_prefix(value: float) -> str:
    """
    Function that converts a number to his version with SI prefix
    @input value (an integer)
    @example:
    >>> add_si_prefix(10000)
    '10.0 kilo'
    """
    prefixes = SIUnit.get_positive() if value > 0 else SIUnit.get_negative()
    for name_prefix, value_prefix in prefixes.items():
    # 遍历循环
        numerical_part = value / (10**value_prefix)
        if numerical_part > 1:
    # 条件判断
            return f"{numerical_part!s} {name_prefix}"
    # 返回结果
    return str(value)
    # 返回结果



# add_binary_prefix 函数实现
def add_binary_prefix(value: float) -> str:
    """
    Function that converts a number to his version with Binary prefix
    @input value (an integer)
    @example:
    >>> add_binary_prefix(65536)
    '64.0 kilo'
    """
    for prefix in BinaryUnit:
    # 遍历循环
        numerical_part = value / (2**prefix.value)
        if numerical_part > 1:
    # 条件判断
            return f"{numerical_part!s} {prefix.name}"
    # 返回结果
    return str(value)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
