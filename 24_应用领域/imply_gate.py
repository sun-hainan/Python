# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / imply_gate

本文件实现 imply_gate 相关的算法功能。
"""

# imply_gate 函数实现
def imply_gate(input_1: int, input_2: int) -> int:
    """
    Calculate IMPLY of the input values

    >>> imply_gate(0, 0)
    1
    >>> imply_gate(0, 1)
    1
    >>> imply_gate(1, 0)
    0
    >>> imply_gate(1, 1)
    1
    """
    return int(input_1 == 0 or input_2 == 1)
    # 返回结果



# recursive_imply_list 函数实现
def recursive_imply_list(input_list: list[int]) -> int:
    """
    Recursively calculates the implication of a list.
    Strictly the implication is applied consecutively left to right:
    ( (a -> b) -> c ) -> d ...

    >>> recursive_imply_list([])
    Traceback (most recent call last):
        ...
    ValueError: Input list must contain at least two elements
    >>> recursive_imply_list([0])
    Traceback (most recent call last):
        ...
    ValueError: Input list must contain at least two elements
    >>> recursive_imply_list([1])
    Traceback (most recent call last):
        ...
    ValueError: Input list must contain at least two elements
    >>> recursive_imply_list([0, 0])
    1
    >>> recursive_imply_list([0, 1])
    1
    >>> recursive_imply_list([1, 0])
    0
    >>> recursive_imply_list([1, 1])
    1
    >>> recursive_imply_list([0, 0, 0])
    0
    >>> recursive_imply_list([0, 0, 1])
    1
    >>> recursive_imply_list([0, 1, 0])
    0
    >>> recursive_imply_list([0, 1, 1])
    1
    >>> recursive_imply_list([1, 0, 0])
    1
    >>> recursive_imply_list([1, 0, 1])
    1
    >>> recursive_imply_list([1, 1, 0])
    0
    >>> recursive_imply_list([1, 1, 1])
    1
    """
    if len(input_list) < 2:
    # 条件判断
        raise ValueError("Input list must contain at least two elements")
    first_implication = imply_gate(input_list[0], input_list[1])
    if len(input_list) == 2:
    # 条件判断
        return first_implication
    # 返回结果
    new_list = [first_implication, *input_list[2:]]
    return recursive_imply_list(new_list)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
