# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / xnor_gate

本文件实现 xnor_gate 相关的算法功能。
"""

# xnor_gate 函数实现
def xnor_gate(input_1: int, input_2: int) -> int:
    """
    Calculate XOR of the input values
    >>> xnor_gate(0, 0)
    1
    >>> xnor_gate(0, 1)
    0
    >>> xnor_gate(1, 0)
    0
    >>> xnor_gate(1, 1)
    1
    """
    return 1 if input_1 == input_2 else 0
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
