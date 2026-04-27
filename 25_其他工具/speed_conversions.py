# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / speed_conversions

本文件实现 speed_conversions 相关的算法功能。
"""

speed_chart: dict[str, float] = {
    "km/h": 1.0,
    "m/s": 3.6,
    "mph": 1.609344,
    "knot": 1.852,
}

speed_chart_inverse: dict[str, float] = {
    "km/h": 1.0,
    "m/s": 0.277777778,
    "mph": 0.621371192,
    "knot": 0.539956803,
}



# convert_speed 函数实现
def convert_speed(speed: float, unit_from: str, unit_to: str) -> float:
    """
    Convert speed from one unit to another using the speed_chart above.

    "km/h": 1.0,
    "m/s": 3.6,
    "mph": 1.609344,
    "knot": 1.852,

    >>> convert_speed(100, "km/h", "m/s")
    27.778
    >>> convert_speed(100, "km/h", "mph")
    62.137
    >>> convert_speed(100, "km/h", "knot")
    53.996
    >>> convert_speed(100, "m/s", "km/h")
    360.0
    >>> convert_speed(100, "m/s", "mph")
    223.694
    >>> convert_speed(100, "m/s", "knot")
    194.384
    >>> convert_speed(100, "mph", "km/h")
    160.934
    >>> convert_speed(100, "mph", "m/s")
    44.704
    >>> convert_speed(100, "mph", "knot")
    86.898
    >>> convert_speed(100, "knot", "km/h")
    185.2
    >>> convert_speed(100, "knot", "m/s")
    51.444
    >>> convert_speed(100, "knot", "mph")
    115.078
    """
    if unit_to not in speed_chart or unit_from not in speed_chart_inverse:
    # 条件判断
        msg = (
            f"Incorrect 'from_type' or 'to_type' value: {unit_from!r}, {unit_to!r}\n"
            f"Valid values are: {', '.join(speed_chart_inverse)}"
        )
        raise ValueError(msg)
    return round(speed * speed_chart[unit_from] * speed_chart_inverse[unit_to], 3)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
