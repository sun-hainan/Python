# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / capacitor_equivalence



本文件实现 capacitor_equivalence 相关的算法功能。

"""



# https://farside.ph.utexas.edu/teaching/316/lectures/node46.html



from __future__ import annotations







# capacitor_parallel 函数实现

def capacitor_parallel(capacitors: list[float]) -> float:

    """

    Ceq = C1 + C2 + ... + Cn

    Calculate the equivalent resistance for any number of capacitors in parallel.

    >>> capacitor_parallel([5.71389, 12, 3])

    20.71389

    >>> capacitor_parallel([5.71389, 12, -3])

    Traceback (most recent call last):

        ...

    ValueError: Capacitor at index 2 has a negative value!

    """

    sum_c = 0.0

    for index, capacitor in enumerate(capacitors):

    # 遍历循环

        if capacitor < 0:

    # 条件判断

            msg = f"Capacitor at index {index} has a negative value!"

            raise ValueError(msg)

        sum_c += capacitor

    return sum_c

    # 返回结果







# capacitor_series 函数实现

def capacitor_series(capacitors: list[float]) -> float:

    """

    Ceq = 1/ (1/C1 + 1/C2 + ... + 1/Cn)

    >>> capacitor_series([5.71389, 12, 3])

    1.6901062252507735

    >>> capacitor_series([5.71389, 12, -3])

    Traceback (most recent call last):

        ...

    ValueError: Capacitor at index 2 has a negative or zero value!

    >>> capacitor_series([5.71389, 12, 0.000])

    Traceback (most recent call last):

        ...

    ValueError: Capacitor at index 2 has a negative or zero value!

    """



    first_sum = 0.0

    for index, capacitor in enumerate(capacitors):

    # 遍历循环

        if capacitor <= 0:

    # 条件判断

            msg = f"Capacitor at index {index} has a negative or zero value!"

            raise ValueError(msg)

        first_sum += 1 / capacitor

    return 1 / first_sum

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

