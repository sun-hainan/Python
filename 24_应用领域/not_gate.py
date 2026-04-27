# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / not_gate



本文件实现 not_gate 相关的算法功能。

"""



# not_gate 函数实现

def not_gate(input_1: int) -> int:

    """

    Calculate NOT of the input values

    >>> not_gate(0)

    1

    >>> not_gate(1)

    0

    """



    return 1 if input_1 == 0 else 0

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

