# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / present_value



本文件实现 present_value 相关的算法功能。

"""



# present_value 函数实现

def present_value(discount_rate: float, cash_flows: list[float]) -> float:

    """

    >>> present_value(0.13, [10, 20.70, -293, 297])

    4.69

    >>> present_value(0.07, [-109129.39, 30923.23, 15098.93, 29734,39])

    -42739.63

    >>> present_value(0.07, [109129.39, 30923.23, 15098.93, 29734,39])

    175519.15

    >>> present_value(-1, [109129.39, 30923.23, 15098.93, 29734,39])

    Traceback (most recent call last):

        ...

    ValueError: Discount rate cannot be negative

    >>> present_value(0.03, [])

    Traceback (most recent call last):

        ...

    ValueError: Cash flows list cannot be empty

    """

    if discount_rate < 0:

    # 条件判断

        raise ValueError("Discount rate cannot be negative")

    if not cash_flows:

    # 条件判断

        raise ValueError("Cash flows list cannot be empty")

    present_value = sum(

        cash_flow / ((1 + discount_rate) ** i) for i, cash_flow in enumerate(cash_flows)

    )

    return round(present_value, ndigits=2)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

