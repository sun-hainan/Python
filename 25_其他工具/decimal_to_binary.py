# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / decimal_to_binary

本文件实现 decimal_to_binary 相关的算法功能。
"""

# decimal_to_binary_iterative 函数实现
def decimal_to_binary_iterative(num: int) -> str:
    """
    Convert an Integer Decimal Number to a Binary Number as str.
    >>> decimal_to_binary_iterative(0)
    '0b0'
    >>> decimal_to_binary_iterative(2)
    '0b10'
    >>> decimal_to_binary_iterative(7)
    '0b111'
    >>> decimal_to_binary_iterative(35)
    '0b100011'
    >>> # negatives work too
    >>> decimal_to_binary_iterative(-2)
    '-0b10'
    >>> # other floats will error
    >>> decimal_to_binary_iterative(16.16) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: 'float' object cannot be interpreted as an integer
    >>> # strings will error as well
    >>> decimal_to_binary_iterative('0xfffff') # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: 'str' object cannot be interpreted as an integer
    """

    if isinstance(num, float):
    # 条件判断
        raise TypeError("'float' object cannot be interpreted as an integer")
    if isinstance(num, str):
    # 条件判断
        raise TypeError("'str' object cannot be interpreted as an integer")

    if num == 0:
    # 条件判断
        return "0b0"
    # 返回结果

    negative = False

    if num < 0:
    # 条件判断
        negative = True
        num = -num

    binary: list[int] = []
    while num > 0:
    # 条件循环
        binary.insert(0, num % 2)
        num >>= 1

    if negative:
    # 条件判断
        return "-0b" + "".join(str(e) for e in binary)
    # 返回结果

    return "0b" + "".join(str(e) for e in binary)
    # 返回结果



# decimal_to_binary_recursive_helper 函数实现
def decimal_to_binary_recursive_helper(decimal: int) -> str:
    """
    Take a positive integer value and return its binary equivalent.
    >>> decimal_to_binary_recursive_helper(1000)
    '1111101000'
    >>> decimal_to_binary_recursive_helper("72")
    '1001000'
    >>> decimal_to_binary_recursive_helper("number")
    Traceback (most recent call last):
        ...
    ValueError: invalid literal for int() with base 10: 'number'
    """
    decimal = int(decimal)
    if decimal in (0, 1):  # Exit cases for the recursion
    # 条件判断
        return str(decimal)
    # 返回结果
    div, mod = divmod(decimal, 2)
    return decimal_to_binary_recursive_helper(div) + str(mod)
    # 返回结果



# decimal_to_binary_recursive 函数实现
def decimal_to_binary_recursive(number: str) -> str:
    """
    Take an integer value and raise ValueError for wrong inputs,
    call the function above and return the output with prefix "0b" & "-0b"
    for positive and negative integers respectively.
    >>> decimal_to_binary_recursive(0)
    '0b0'
    >>> decimal_to_binary_recursive(40)
    '0b101000'
    >>> decimal_to_binary_recursive(-40)
    '-0b101000'
    >>> decimal_to_binary_recursive(40.8)
    Traceback (most recent call last):
        ...
    ValueError: Input value is not an integer
    >>> decimal_to_binary_recursive("forty")
    Traceback (most recent call last):
        ...
    ValueError: Input value is not an integer
    """
    number = str(number).strip()
    if not number:
    # 条件判断
        raise ValueError("No input value was provided")
    negative = "-" if number.startswith("-") else ""
    number = number.lstrip("-")
    if not number.isnumeric():
    # 条件判断
        raise ValueError("Input value is not an integer")
    return f"{negative}0b{decimal_to_binary_recursive_helper(int(number))}"
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

    print(decimal_to_binary_recursive(input("Input a decimal number: ")))
