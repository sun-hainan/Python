# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / length_conversion



本文件实现 length_conversion 相关的算法功能。

"""



from typing import NamedTuple





class FromTo(NamedTuple):

    from_factor: float

    to_factor: float





TYPE_CONVERSION = {

    "millimeter": "mm",

    "centimeter": "cm",

    "meter": "m",

    "kilometer": "km",

    "inch": "in",

    "inche": "in",  # Trailing 's' has been stripped off

    "feet": "ft",

    "foot": "ft",

    "yard": "yd",

    "mile": "mi",

}



METRIC_CONVERSION = {

    "mm": FromTo(0.001, 1000),

    "cm": FromTo(0.01, 100),

    "m": FromTo(1, 1),

    "km": FromTo(1000, 0.001),

    "in": FromTo(0.0254, 39.3701),

    "ft": FromTo(0.3048, 3.28084),

    "yd": FromTo(0.9144, 1.09361),

    "mi": FromTo(1609.34, 0.000621371),

}







# length_conversion 函数实现

def length_conversion(value: float, from_type: str, to_type: str) -> float:

    """

    Conversion between length units.



    >>> length_conversion(4, "METER", "FEET")

    13.12336

    >>> length_conversion(4, "M", "FT")

    13.12336

    >>> length_conversion(1, "meter", "kilometer")

    0.001

    >>> length_conversion(1, "kilometer", "inch")

    39370.1

    >>> length_conversion(3, "kilometer", "mile")

    1.8641130000000001

    >>> length_conversion(2, "feet", "meter")

    0.6096

    >>> length_conversion(4, "feet", "yard")

    1.333329312

    >>> length_conversion(1, "inch", "meter")

    0.0254

    >>> length_conversion(2, "inch", "mile")

    3.15656468e-05

    >>> length_conversion(2, "centimeter", "millimeter")

    20.0

    >>> length_conversion(2, "centimeter", "yard")

    0.0218722

    >>> length_conversion(4, "yard", "meter")

    3.6576

    >>> length_conversion(4, "yard", "kilometer")

    0.0036576

    >>> length_conversion(3, "foot", "meter")

    0.9144000000000001

    >>> length_conversion(3, "foot", "inch")

    36.00001944

    >>> length_conversion(4, "mile", "kilometer")

    6.43736

    >>> length_conversion(2, "miles", "InChEs")

    126719.753468

    >>> length_conversion(3, "millimeter", "centimeter")

    0.3

    >>> length_conversion(3, "mm", "in")

    0.1181103

    >>> length_conversion(4, "wrongUnit", "inch")

    Traceback (most recent call last):

      ...

    ValueError: Invalid 'from_type' value: 'wrongUnit'.

    Conversion abbreviations are: mm, cm, m, km, in, ft, yd, mi

    """

    new_from = from_type.lower().rstrip("s")

    new_from = TYPE_CONVERSION.get(new_from, new_from)

    new_to = to_type.lower().rstrip("s")

    new_to = TYPE_CONVERSION.get(new_to, new_to)

    if new_from not in METRIC_CONVERSION:

    # 条件判断

        msg = (

            f"Invalid 'from_type' value: {from_type!r}.\n"

            f"Conversion abbreviations are: {', '.join(METRIC_CONVERSION)}"

        )

        raise ValueError(msg)

    if new_to not in METRIC_CONVERSION:

    # 条件判断

        msg = (

            f"Invalid 'to_type' value: {to_type!r}.\n"

            f"Conversion abbreviations are: {', '.join(METRIC_CONVERSION)}"

        )

        raise ValueError(msg)

    return (

    # 返回结果

        value

        * METRIC_CONVERSION[new_from].from_factor

        * METRIC_CONVERSION[new_to].to_factor

    )





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

