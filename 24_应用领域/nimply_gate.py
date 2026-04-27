# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / nimply_gate

本文件实现 nimply_gate 相关的算法功能。
"""

# nimply_gate 函数实现
def nimply_gate(input_1: int, input_2: int) -> int:
    """
    Calculate NIMPLY of the input values

    >>> nimply_gate(0, 0)
    0
    >>> nimply_gate(0, 1)
    0
    >>> nimply_gate(1, 0)
    1
    >>> nimply_gate(1, 1)
    0
    """
    return int(input_1 == 1 and input_2 == 0)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
