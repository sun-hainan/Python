# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / binary_to_decimal

本文件实现 binary_to_decimal 相关的算法功能。
"""

# bin_to_decimal 函数实现
def bin_to_decimal(bin_string: str) -> int:
    """
    Convert a binary value to its decimal equivalent

    >>> bin_to_decimal("101")
    5
    >>> bin_to_decimal(" 1010   ")
    10
    >>> bin_to_decimal("-11101")
    -29
    >>> bin_to_decimal("0")
    0
    >>> bin_to_decimal("a")
    Traceback (most recent call last):
        ...
    ValueError: Non-binary value was passed to the function
    >>> bin_to_decimal("")
    Traceback (most recent call last):
        ...
    ValueError: Empty string was passed to the function
    >>> bin_to_decimal("39")
    Traceback (most recent call last):
        ...
    ValueError: Non-binary value was passed to the function
    """
    bin_string = str(bin_string).strip()
    if not bin_string:
    # 条件判断
        raise ValueError("Empty string was passed to the function")
    is_negative = bin_string[0] == "-"
    if is_negative:
    # 条件判断
        bin_string = bin_string[1:]
    if not all(char in "01" for char in bin_string):
    # 条件判断
        raise ValueError("Non-binary value was passed to the function")
    decimal_number = 0
    for char in bin_string:
    # 遍历循环
        decimal_number = 2 * decimal_number + int(char)
    return -decimal_number if is_negative else decimal_number
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    from doctest import testmod

    testmod()
