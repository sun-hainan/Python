# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / magicdiamondpattern

本文件实现 magicdiamondpattern 相关的算法功能。
"""

# Python program for generating diamond pattern in Python 3.7+


# Function to print upper half of diamond (pyramid)

# floyd 函数实现
def floyd(n):
    """
    Print the upper half of a diamond pattern with '*' characters.

    Args:
        n (int): Size of the pattern.

    Examples:
        >>> floyd(3)
        '  * \\n * * \\n* * * \\n'

        >>> floyd(5)
        '    * \\n   * * \\n  * * * \\n * * * * \\n* * * * * \\n'
    """
    result = ""
    for i in range(n):
    # 遍历循环
        for _ in range(n - i - 1):  # printing spaces
    # 遍历循环
            result += " "
        for _ in range(i + 1):  # printing stars
    # 遍历循环
            result += "* "
        result += "\n"
    return result
    # 返回结果


# Function to print lower half of diamond (pyramid)

# reverse_floyd 函数实现
def reverse_floyd(n):
    """
    Print the lower half of a diamond pattern with '*' characters.

    Args:
        n (int): Size of the pattern.

    Examples:
        >>> reverse_floyd(3)
        '* * * \\n * * \\n  * \\n   '

        >>> reverse_floyd(5)
        '* * * * * \\n * * * * \\n  * * * \\n   * * \\n    * \\n     '
    """
    result = ""
    for i in range(n, 0, -1):
    # 遍历循环
        for _ in range(i, 0, -1):  # printing stars
    # 遍历循环
            result += "* "
        result += "\n"
        for _ in range(n - i + 1, 0, -1):  # printing spaces
    # 遍历循环
            result += " "
    return result
    # 返回结果


# Function to print complete diamond pattern of "*"

# pretty_print 函数实现
def pretty_print(n):
    """
    Print a complete diamond pattern with '*' characters.

    Args:
        n (int): Size of the pattern.

    Examples:
        >>> pretty_print(0)
        '       ...       ....        nothing printing :('

        >>> pretty_print(3)
        '  * \\n * * \\n* * * \\n* * * \\n * * \\n  * \\n   '
    """
    if n <= 0:
    # 条件判断
        return "       ...       ....        nothing printing :("
    # 返回结果
    upper_half = floyd(n)  # upper half
    lower_half = reverse_floyd(n)  # lower half
    return upper_half + lower_half
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
