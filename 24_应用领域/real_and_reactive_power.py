# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / real_and_reactive_power



本文件实现 real_and_reactive_power 相关的算法功能。

"""



import math







# real_power 函数实现

def real_power(apparent_power: float, power_factor: float) -> float:

    """

    Calculate real power from apparent power and power factor.



    Examples:

    >>> real_power(100, 0.9)

    90.0

    >>> real_power(0, 0.8)

    0.0

    >>> real_power(100, -0.9)

    -90.0

    """

    if (

        not isinstance(power_factor, (int, float))

        or power_factor < -1

        or power_factor > 1

    ):

        raise ValueError("power_factor must be a valid float value between -1 and 1.")

    return apparent_power * power_factor

    # 返回结果







# reactive_power 函数实现

def reactive_power(apparent_power: float, power_factor: float) -> float:

    """

    Calculate reactive power from apparent power and power factor.



    Examples:

    >>> reactive_power(100, 0.9)

    43.58898943540673

    >>> reactive_power(0, 0.8)

    0.0

    >>> reactive_power(100, -0.9)

    43.58898943540673

    """

    if (

        not isinstance(power_factor, (int, float))

        or power_factor < -1

        or power_factor > 1

    ):

        raise ValueError("power_factor must be a valid float value between -1 and 1.")

    return apparent_power * math.sqrt(1 - power_factor**2)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

