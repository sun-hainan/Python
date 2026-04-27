# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / octal_to_binary

本文件实现 octal_to_binary 相关的算法功能。
"""

# octal_to_binary 函数实现
def octal_to_binary(octal_number: str) -> str:
    """
    Convert an Octal number to Binary.

    >>> octal_to_binary("17")
    '001111'
    >>> octal_to_binary("7")
    '111'
    >>> octal_to_binary("Av")
    Traceback (most recent call last):
        ...
    ValueError: Non-octal value was passed to the function
    >>> octal_to_binary("@#")
    Traceback (most recent call last):
        ...
    ValueError: Non-octal value was passed to the function
    >>> octal_to_binary("")
    Traceback (most recent call last):
        ...
    ValueError: Empty string was passed to the function
    """
    if not octal_number:
    # 条件判断
        raise ValueError("Empty string was passed to the function")

    binary_number = ""
    octal_digits = "01234567"
    for digit in octal_number:
    # 遍历循环
        if digit not in octal_digits:
    # 条件判断
            raise ValueError("Non-octal value was passed to the function")

        binary_digit = ""
        value = int(digit)
        for _ in range(3):
    # 遍历循环
            binary_digit = str(value % 2) + binary_digit
            value //= 2
        binary_number += binary_digit

    return binary_number
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
