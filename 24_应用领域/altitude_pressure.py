# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / altitude_pressure



本文件实现 altitude_pressure 相关的算法功能。

"""



# get_altitude_at_pressure 函数实现

def get_altitude_at_pressure(pressure: float) -> float:

    """

    This method calculates the altitude from Pressure wrt to

    Sea level pressure as reference .Pressure is in Pascals

    https://en.wikipedia.org/wiki/Pressure_altitude

    https://community.bosch-sensortec.com/t5/Question-and-answers/How-to-calculate-the-altitude-from-the-pressure-sensor-data/qaq-p/5702



    H = 44330 * [1 - (P/p0)^(1/5.255) ]



    Where :

    H = altitude (m)

    P = measured pressure

    p0 = reference pressure at sea level 101325 Pa



    Examples:

    >>> get_altitude_at_pressure(pressure=100_000)

    105.47836610778828

    >>> get_altitude_at_pressure(pressure=101_325)

    0.0

    >>> get_altitude_at_pressure(pressure=80_000)

    1855.873388064995

    >>> get_altitude_at_pressure(pressure=201_325)

    Traceback (most recent call last):

      ...

    ValueError: Value Higher than Pressure at Sea Level !

    >>> get_altitude_at_pressure(pressure=-80_000)

    Traceback (most recent call last):

      ...

    ValueError: Atmospheric Pressure can not be negative !

    """



    if pressure > 101325:

    # 条件判断

        raise ValueError("Value Higher than Pressure at Sea Level !")

    if pressure < 0:

    # 条件判断

        raise ValueError("Atmospheric Pressure can not be negative !")

    return 44_330 * (1 - (pressure / 101_325) ** (1 / 5.5255))

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

