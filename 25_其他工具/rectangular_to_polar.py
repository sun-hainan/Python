# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / rectangular_to_polar



本文件实现 rectangular_to_polar 相关的算法功能。

"""



import math







# rectangular_to_polar 函数实现

def rectangular_to_polar(real: float, img: float) -> tuple[float, float]:

    """

    https://en.wikipedia.org/wiki/Polar_coordinate_system



    >>> rectangular_to_polar(5,-5)

    (7.07, -45.0)

    >>> rectangular_to_polar(-1,1)

    (1.41, 135.0)

    >>> rectangular_to_polar(-1,-1)

    (1.41, -135.0)

    >>> rectangular_to_polar(1e-10,1e-10)

    (0.0, 45.0)

    >>> rectangular_to_polar(-1e-10,1e-10)

    (0.0, 135.0)

    >>> rectangular_to_polar(9.75,5.93)

    (11.41, 31.31)

    >>> rectangular_to_polar(10000,99999)

    (100497.76, 84.29)

    """



    mod = round(math.sqrt((real**2) + (img**2)), 2)

    ang = round(math.degrees(math.atan2(img, real)), 2)

    return (mod, ang)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

