# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / octal_to_decimal



本文件实现 octal_to_decimal 相关的算法功能。

"""



# oct_to_decimal 函数实现

def oct_to_decimal(oct_string: str) -> int:

    """

    Convert a octal value to its decimal equivalent



    >>> oct_to_decimal("")

    Traceback (most recent call last):

        ...

    ValueError: Empty string was passed to the function

    >>> oct_to_decimal("-")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    >>> oct_to_decimal("e")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    >>> oct_to_decimal("8")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    >>> oct_to_decimal("-e")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    >>> oct_to_decimal("-8")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    >>> oct_to_decimal("1")

    1

    >>> oct_to_decimal("-1")

    -1

    >>> oct_to_decimal("12")

    10

    >>> oct_to_decimal(" 12   ")

    10

    >>> oct_to_decimal("-45")

    -37

    >>> oct_to_decimal("-")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    >>> oct_to_decimal("0")

    0

    >>> oct_to_decimal("-4055")

    -2093

    >>> oct_to_decimal("2-0Fm")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    >>> oct_to_decimal("")

    Traceback (most recent call last):

        ...

    ValueError: Empty string was passed to the function

    >>> oct_to_decimal("19")

    Traceback (most recent call last):

        ...

    ValueError: Non-octal value was passed to the function

    """

    oct_string = str(oct_string).strip()

    if not oct_string:

    # 条件判断

        raise ValueError("Empty string was passed to the function")

    is_negative = oct_string[0] == "-"

    if is_negative:

    # 条件判断

        oct_string = oct_string[1:]

    if not oct_string.isdigit() or not all(0 <= int(char) <= 7 for char in oct_string):

    # 条件判断

        raise ValueError("Non-octal value was passed to the function")

    decimal_number = 0

    for char in oct_string:

    # 遍历循环

        decimal_number = 8 * decimal_number + int(char)

    if is_negative:

    # 条件判断

        decimal_number = -decimal_number

    return decimal_number

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    from doctest import testmod



    testmod()

