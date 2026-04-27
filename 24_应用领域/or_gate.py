# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / or_gate

本文件实现 or_gate 相关的算法功能。
"""

# or_gate 函数实现
def or_gate(input_1: int, input_2: int) -> int:
    """
    Calculate OR of the input values
    >>> or_gate(0, 0)
    0
    >>> or_gate(0, 1)
    1
    >>> or_gate(1, 0)
    1
    >>> or_gate(1, 1)
    1
    """
    return int((input_1, input_2).count(1) != 0)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
