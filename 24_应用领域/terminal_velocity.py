# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / terminal_velocity



本文件实现 terminal_velocity 相关的算法功能。

"""



from scipy.constants import g







# terminal_velocity 函数实现

def terminal_velocity(

    mass: float, density: float, area: float, drag_coefficient: float

) -> float:

    """

    >>> terminal_velocity(1, 25, 0.6, 0.77)

    1.3031197996044768

    >>> terminal_velocity(2, 100, 0.45, 0.23)

    1.9467947148674276

    >>> terminal_velocity(5, 50, 0.2, 0.5)

    4.428690551393267

    >>> terminal_velocity(-5, 50, -0.2, -2)

    Traceback (most recent call last):

        ...

    ValueError: mass, density, area and the drag coefficient all need to be positive

    >>> terminal_velocity(3, -20, -1, 2)

    Traceback (most recent call last):

        ...

    ValueError: mass, density, area and the drag coefficient all need to be positive

    >>> terminal_velocity(-2, -1, -0.44, -1)

    Traceback (most recent call last):

        ...

    ValueError: mass, density, area and the drag coefficient all need to be positive

    """

    if mass <= 0 or density <= 0 or area <= 0 or drag_coefficient <= 0:

    # 条件判断

        raise ValueError(

            "mass, density, area and the drag coefficient all need to be positive"

        )

    return ((2 * mass * g) / (density * area * drag_coefficient)) ** 0.5

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

