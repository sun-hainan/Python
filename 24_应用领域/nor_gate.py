# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / nor_gate

本文件实现 nor_gate 相关的算法功能。
"""

from collections.abc import Callable



# nor_gate 函数实现
def nor_gate(input_1: int, input_2: int) -> int:
    """
    >>> nor_gate(0, 0)
    1
    >>> nor_gate(0, 1)
    0
    >>> nor_gate(1, 0)
    0
    >>> nor_gate(1, 1)
    0
    >>> nor_gate(0.0, 0.0)
    1
    >>> nor_gate(0, -7)
    0
    """
    return int(input_1 == input_2 == 0)
    # 返回结果



# truth_table 函数实现
def truth_table(func: Callable) -> str:
    """
    >>> print(truth_table(nor_gate))
    Truth Table of NOR Gate:
    | Input 1  | Input 2  |  Output  |
    |    0     |    0     |    1     |
    |    0     |    1     |    0     |
    |    1     |    0     |    0     |
    |    1     |    1     |    0     |
    """


# make_table_row 函数实现
    def make_table_row(items: list | tuple) -> str:
        """
        >>> make_table_row(("One", "Two", "Three"))
        '|   One    |   Two    |  Three   |'
        """
        return f"| {' | '.join(f'{item:^8}' for item in items)} |"
    # 返回结果

    return "\n".join(
    # 返回结果
        (
            "Truth Table of NOR Gate:",
            make_table_row(("Input 1", "Input 2", "Output")),
            *[make_table_row((i, j, func(i, j))) for i in (0, 1) for j in (0, 1)],
        )
    )


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    print(truth_table(nor_gate))
