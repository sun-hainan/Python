# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / hexadecimal_to_decimal

本文件实现 hexadecimal_to_decimal 相关的算法功能。
"""

hex_table = {hex(i)[2:]: i for i in range(16)}  # Use [:2] to strip off the leading '0x'



# hex_to_decimal 函数实现
def hex_to_decimal(hex_string: str) -> int:
    """
    Convert a hexadecimal value to its decimal equivalent
    #https://www.programiz.com/python-programming/methods/built-in/hex

    >>> hex_to_decimal("a")
    10
    >>> hex_to_decimal("12f")
    303
    >>> hex_to_decimal("   12f   ")
    303
    >>> hex_to_decimal("FfFf")
    65535
    >>> hex_to_decimal("-Ff")
    -255
    >>> hex_to_decimal("F-f")
    Traceback (most recent call last):
        ...
    ValueError: Non-hexadecimal value was passed to the function
    >>> hex_to_decimal("")
    Traceback (most recent call last):
        ...
    ValueError: Empty string was passed to the function
    >>> hex_to_decimal("12m")
    Traceback (most recent call last):
        ...
    ValueError: Non-hexadecimal value was passed to the function
    """
    hex_string = hex_string.strip().lower()
    if not hex_string:
    # 条件判断
        raise ValueError("Empty string was passed to the function")
    is_negative = hex_string[0] == "-"
    if is_negative:
    # 条件判断
        hex_string = hex_string[1:]
    if not all(char in hex_table for char in hex_string):
    # 条件判断
        raise ValueError("Non-hexadecimal value was passed to the function")
    decimal_number = 0
    for char in hex_string:
    # 遍历循环
        decimal_number = 16 * decimal_number + hex_table[char]
    return -decimal_number if is_negative else decimal_number
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    from doctest import testmod

    testmod()
