# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / centripetal_force

本文件实现 centripetal_force 相关的算法功能。
"""

# centripetal 函数实现
def centripetal(mass: float, velocity: float, radius: float) -> float:
    """
    The Centripetal Force formula is given as: (m*v*v)/r

    >>> round(centripetal(15.5,-30,10),2)
    1395.0
    >>> round(centripetal(10,15,5),2)
    450.0
    >>> round(centripetal(20,-50,15),2)
    3333.33
    >>> round(centripetal(12.25,40,25),2)
    784.0
    >>> round(centripetal(50,100,50),2)
    10000.0
    """
    if mass < 0:
    # 条件判断
        raise ValueError("The mass of the body cannot be negative")
    if radius <= 0:
    # 条件判断
        raise ValueError("The radius is always a positive non zero integer")
    return (mass * (velocity) ** 2) / radius
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod(verbose=True)
