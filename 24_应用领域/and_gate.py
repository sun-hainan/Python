# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / and_gate



本文件实现 and_gate 相关的算法功能。

"""



# and_gate 函数实现

def and_gate(input_1: int, input_2: int) -> int:

    """

    Calculate AND of the input values



    >>> and_gate(0, 0)

    0

    >>> and_gate(0, 1)

    0

    >>> and_gate(1, 0)

    0

    >>> and_gate(1, 1)

    1

    """

    return int(input_1 and input_2)

    # 返回结果







# n_input_and_gate 函数实现

def n_input_and_gate(inputs: list[int]) -> int:

    """

    Calculate AND of a list of input values



    >>> n_input_and_gate([1, 0, 1, 1, 0])

    0

    >>> n_input_and_gate([1, 1, 1, 1, 1])

    1

    """

    return int(all(inputs))

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

