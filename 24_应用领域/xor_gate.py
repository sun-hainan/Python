# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / xor_gate

本文件实现 xor_gate 相关的算法功能。
"""

# xor_gate 函数实现
def xor_gate(input_1: int, input_2: int) -> int:
    """
    calculate xor of the input values

    >>> xor_gate(0, 0)
    0
    >>> xor_gate(0, 1)
    1
    >>> xor_gate(1, 0)
    1
    >>> xor_gate(1, 1)
    0
    """
    return (input_1, input_2).count(0) % 2
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
