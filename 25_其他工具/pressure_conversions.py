# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / pressure_conversions

本文件实现 pressure_conversions 相关的算法功能。
"""

from typing import NamedTuple


class FromTo(NamedTuple):
    from_factor: float
    to_factor: float


PRESSURE_CONVERSION = {
    "atm": FromTo(1, 1),
    "pascal": FromTo(0.0000098, 101325),
    "bar": FromTo(0.986923, 1.01325),
    "kilopascal": FromTo(0.00986923, 101.325),
    "megapascal": FromTo(9.86923, 0.101325),
    "psi": FromTo(0.068046, 14.6959),
    "inHg": FromTo(0.0334211, 29.9213),
    "torr": FromTo(0.00131579, 760),
}



# pressure_conversion 函数实现
def pressure_conversion(value: float, from_type: str, to_type: str) -> float:
    """
    Conversion between pressure units.
    >>> pressure_conversion(4, "atm", "pascal")
    405300
    >>> pressure_conversion(1, "pascal", "psi")
    0.00014401981999999998
    >>> pressure_conversion(1, "bar", "atm")
    0.986923
    >>> pressure_conversion(3, "kilopascal", "bar")
    0.029999991892499998
    >>> pressure_conversion(2, "megapascal", "psi")
    290.074434314
    >>> pressure_conversion(4, "psi", "torr")
    206.85984
    >>> pressure_conversion(1, "inHg", "atm")
    0.0334211
    >>> pressure_conversion(1, "torr", "psi")
    0.019336718261000002
    >>> pressure_conversion(4, "wrongUnit", "atm")
    Traceback (most recent call last):
        ...
    ValueError: Invalid 'from_type' value: 'wrongUnit'  Supported values are:
    atm, pascal, bar, kilopascal, megapascal, psi, inHg, torr
    """
    if from_type not in PRESSURE_CONVERSION:
    # 条件判断
        raise ValueError(
            f"Invalid 'from_type' value: {from_type!r}  Supported values are:\n"
            + ", ".join(PRESSURE_CONVERSION)
        )
    if to_type not in PRESSURE_CONVERSION:
    # 条件判断
        raise ValueError(
            f"Invalid 'to_type' value: {to_type!r}.  Supported values are:\n"
            + ", ".join(PRESSURE_CONVERSION)
        )
    return (
    # 返回结果
        value
        * PRESSURE_CONVERSION[from_type].from_factor
        * PRESSURE_CONVERSION[to_type].to_factor
    )


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
