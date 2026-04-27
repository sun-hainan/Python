# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / nand_gate

本文件实现 nand_gate 相关的算法功能。
"""

# nand_gate 函数实现
def nand_gate(input_1: int, input_2: int) -> int:
    """
    Calculate NAND of the input values
    >>> nand_gate(0, 0)
    1
    >>> nand_gate(0, 1)
    1
    >>> nand_gate(1, 0)
    1
    >>> nand_gate(1, 1)
    0
    """
    return int(not (input_1 and input_2))
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
