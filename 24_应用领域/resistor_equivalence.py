# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / resistor_equivalence



本文件实现 resistor_equivalence 相关的算法功能。

"""



# https://byjus.com/equivalent-resistance-formula/



from __future__ import annotations







# resistor_parallel 函数实现

def resistor_parallel(resistors: list[float]) -> float:

    """

    Req = 1/ (1/R1 + 1/R2 + ... + 1/Rn)



    >>> resistor_parallel([3.21389, 2, 3])

    0.8737571620498019

    >>> resistor_parallel([3.21389, 2, -3])

    Traceback (most recent call last):

        ...

    ValueError: Resistor at index 2 has a negative or zero value!

    >>> resistor_parallel([3.21389, 2, 0.000])

    Traceback (most recent call last):

        ...

    ValueError: Resistor at index 2 has a negative or zero value!

    """



    first_sum = 0.00

    for index, resistor in enumerate(resistors):

    # 遍历循环

        if resistor <= 0:

    # 条件判断

            msg = f"Resistor at index {index} has a negative or zero value!"

            raise ValueError(msg)

        first_sum += 1 / float(resistor)

    return 1 / first_sum

    # 返回结果







# resistor_series 函数实现

def resistor_series(resistors: list[float]) -> float:

    """

    Req = R1 + R2 + ... + Rn



    Calculate the equivalent resistance for any number of resistors in parallel.



    >>> resistor_series([3.21389, 2, 3])

    8.21389

    >>> resistor_series([3.21389, 2, -3])

    Traceback (most recent call last):

        ...

    ValueError: Resistor at index 2 has a negative value!

    """

    sum_r = 0.00

    for index, resistor in enumerate(resistors):

    # 遍历循环

        sum_r += resistor

        if resistor < 0:

    # 条件判断

            msg = f"Resistor at index {index} has a negative value!"

            raise ValueError(msg)

    return sum_r

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

