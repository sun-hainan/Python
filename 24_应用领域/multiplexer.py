# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / multiplexer

本文件实现 multiplexer 相关的算法功能。
"""

# mux 函数实现
def mux(input0: int, input1: int, select: int) -> int:
    """
    Implement a 2-to-1 Multiplexer.

    :param input0: The first input value (0 or 1).
    :param input1: The second input value (0 or 1).
    :param select: The select signal (0 or 1) to choose between input0 and input1.
    :return: The output based on the select signal.  input1 if select else input0.

    https://www.electrically4u.com/solved-problems-on-multiplexer
    https://en.wikipedia.org/wiki/Multiplexer

    >>> mux(0, 1, 0)
    0
    >>> mux(0, 1, 1)
    1
    >>> mux(1, 0, 0)
    1
    >>> mux(1, 0, 1)
    0
    >>> mux(2, 1, 0)
    Traceback (most recent call last):
        ...
    ValueError: Inputs and select signal must be 0 or 1
    >>> mux(0, -1, 0)
    Traceback (most recent call last):
        ...
    ValueError: Inputs and select signal must be 0 or 1
    >>> mux(0, 1, 1.1)
    Traceback (most recent call last):
        ...
    ValueError: Inputs and select signal must be 0 or 1
    """
    if all(i in (0, 1) for i in (input0, input1, select)):
    # 条件判断
        return input1 if select else input0
    # 返回结果
    raise ValueError("Inputs and select signal must be 0 or 1")


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
