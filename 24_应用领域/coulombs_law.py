# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / coulombs_law



本文件实现 coulombs_law 相关的算法功能。

"""



# coulombs_law 函数实现

def coulombs_law(q1: float, q2: float, radius: float) -> float:

    """

    Calculate the electrostatic force of attraction or repulsion

    between two point charges



    >>> coulombs_law(15.5, 20, 15)

    12382849136.06

    >>> coulombs_law(1, 15, 5)

    5392531075.38

    >>> coulombs_law(20, -50, 15)

    -39944674632.44

    >>> coulombs_law(-5, -8, 10)

    3595020716.92

    >>> coulombs_law(50, 100, 50)

    17975103584.6

    """

    if radius <= 0:

    # 条件判断

        raise ValueError("The radius is always a positive number")

    return round(((8.9875517923 * 10**9) * q1 * q2) / (radius**2), 2)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

