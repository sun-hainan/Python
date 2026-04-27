# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / wheatstone_bridge



本文件实现 wheatstone_bridge 相关的算法功能。

"""



# https://en.wikipedia.org/wiki/Wheatstone_bridge

from __future__ import annotations







# wheatstone_solver 函数实现

def wheatstone_solver(

    resistance_1: float, resistance_2: float, resistance_3: float

) -> float:

    """

    This function can calculate the unknown resistance in an wheatstone network,

    given that the three other resistances in the network are known.

    The formula to calculate the same is:



    ---------------

    |Rx=(R2/R1)*R3|

    ---------------



    Usage examples:

    >>> wheatstone_solver(resistance_1=2, resistance_2=4, resistance_3=5)

    10.0

    >>> wheatstone_solver(resistance_1=356, resistance_2=234, resistance_3=976)

    641.5280898876405

    >>> wheatstone_solver(resistance_1=2, resistance_2=-1, resistance_3=2)

    Traceback (most recent call last):

        ...

    ValueError: All resistance values must be positive

    >>> wheatstone_solver(resistance_1=0, resistance_2=0, resistance_3=2)

    Traceback (most recent call last):

        ...

    ValueError: All resistance values must be positive

    """



    if resistance_1 <= 0 or resistance_2 <= 0 or resistance_3 <= 0:

    # 条件判断

        raise ValueError("All resistance values must be positive")

    else:

        return float((resistance_2 / resistance_1) * resistance_3)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

