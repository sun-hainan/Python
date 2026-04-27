# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / addition_without_arithmetic



本文件实现 addition_without_arithmetic 相关的算法功能。

"""



# =============================================================================

# 算法模块：add

# =============================================================================

def add(first: int, second: int) -> int:

    # add function



    # add function

    """

    Implementation of addition of integer



    Examples:

    >>> add(3, 5)

    8

    >>> add(13, 5)

    18

    >>> add(-7, 2)

    -5

    >>> add(0, -7)

    -7

    >>> add(-321, 0)

    -321

    """

    while second != 0:

        c = first & second

        first ^= second

        second = c << 1

    return first





if __name__ == "__main__":

    import doctest



    doctest.testmod()



    first = int(input("Enter the first number: ").strip())

    second = int(input("Enter the second number: ").strip())

    print(f"{add(first, second) = }")

