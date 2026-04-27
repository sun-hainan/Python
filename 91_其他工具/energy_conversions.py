# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / energy_conversions



本文件实现 energy_conversions 相关的算法功能。

"""



ENERGY_CONVERSION: dict[str, float] = {

    "joule": 1.0,

    "kilojoule": 1_000,

    "megajoule": 1_000_000,

    "gigajoule": 1_000_000_000,

    "wattsecond": 1.0,

    "watthour": 3_600,

    "kilowatthour": 3_600_000,

    "newtonmeter": 1.0,

    "calorie_nutr": 4_186.8,

    "kilocalorie_nutr": 4_186_800.00,

    "electronvolt": 1.602_176_634e-19,

    "britishthermalunit_it": 1_055.055_85,

    "footpound": 1.355_818,

}







# energy_conversion 函数实现

def energy_conversion(from_type: str, to_type: str, value: float) -> float:

    """

    Conversion of energy units.

    >>> energy_conversion("joule", "joule", 1)

    1.0

    >>> energy_conversion("joule", "kilojoule", 1)

    0.001

    >>> energy_conversion("joule", "megajoule", 1)

    1e-06

    >>> energy_conversion("joule", "gigajoule", 1)

    1e-09

    >>> energy_conversion("joule", "wattsecond", 1)

    1.0

    >>> energy_conversion("joule", "watthour", 1)

    0.0002777777777777778

    >>> energy_conversion("joule", "kilowatthour", 1)

    2.7777777777777776e-07

    >>> energy_conversion("joule", "newtonmeter", 1)

    1.0

    >>> energy_conversion("joule", "calorie_nutr", 1)

    0.00023884589662749592

    >>> energy_conversion("joule", "kilocalorie_nutr", 1)

    2.388458966274959e-07

    >>> energy_conversion("joule", "electronvolt", 1)

    6.241509074460763e+18

    >>> energy_conversion("joule", "britishthermalunit_it", 1)

    0.0009478171226670134

    >>> energy_conversion("joule", "footpound", 1)

    0.7375621211696556

    >>> energy_conversion("joule", "megajoule", 1000)

    0.001

    >>> energy_conversion("calorie_nutr", "kilocalorie_nutr", 1000)

    1.0

    >>> energy_conversion("kilowatthour", "joule", 10)

    36000000.0

    >>> energy_conversion("britishthermalunit_it", "footpound", 1)

    778.1692306784539

    >>> energy_conversion("watthour", "joule", "a") # doctest: +ELLIPSIS

    Traceback (most recent call last):

      ...

    TypeError: unsupported operand type(s) for /: 'str' and 'float'

    >>> energy_conversion("wrongunit", "joule", 1) # doctest: +ELLIPSIS

    Traceback (most recent call last):

      ...

    ValueError: Incorrect 'from_type' or 'to_type' value: 'wrongunit', 'joule'

    Valid values are: joule, ... footpound

    >>> energy_conversion("joule", "wrongunit", 1) # doctest: +ELLIPSIS

    Traceback (most recent call last):

      ...

    ValueError: Incorrect 'from_type' or 'to_type' value: 'joule', 'wrongunit'

    Valid values are: joule, ... footpound

    >>> energy_conversion("123", "abc", 1) # doctest: +ELLIPSIS

    Traceback (most recent call last):

      ...

    ValueError: Incorrect 'from_type' or 'to_type' value: '123', 'abc'

    Valid values are: joule, ... footpound

    """

    if to_type not in ENERGY_CONVERSION or from_type not in ENERGY_CONVERSION:

    # 条件判断

        msg = (

            f"Incorrect 'from_type' or 'to_type' value: {from_type!r}, {to_type!r}\n"

            f"Valid values are: {', '.join(ENERGY_CONVERSION)}"

        )

        raise ValueError(msg)

    return value * ENERGY_CONVERSION[from_type] / ENERGY_CONVERSION[to_type]

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

