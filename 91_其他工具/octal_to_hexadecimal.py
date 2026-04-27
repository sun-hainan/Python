# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / octal_to_hexadecimal



本文件实现 octal_to_hexadecimal 相关的算法功能。

"""



# octal_to_hex 函数实现

def octal_to_hex(octal: str) -> str:

    """

    Convert an Octal number to Hexadecimal number.

    For more information: https://en.wikipedia.org/wiki/Octal



    >>> octal_to_hex("100")

    '0x40'

    >>> octal_to_hex("235")

    '0x9D'

    >>> octal_to_hex(17)

    Traceback (most recent call last):

        ...

    TypeError: Expected a string as input

    >>> octal_to_hex("Av")

    Traceback (most recent call last):

        ...

    ValueError: Not a Valid Octal Number

    >>> octal_to_hex("")

    Traceback (most recent call last):

        ...

    ValueError: Empty string was passed to the function

    """



    if not isinstance(octal, str):

    # 条件判断

        raise TypeError("Expected a string as input")

    if octal.startswith("0o"):

    # 条件判断

        octal = octal[2:]

    if octal == "":

    # 条件判断

        raise ValueError("Empty string was passed to the function")

    if any(char not in "01234567" for char in octal):

    # 条件判断

        raise ValueError("Not a Valid Octal Number")



    decimal = 0

    for char in octal:

    # 遍历循环

        decimal <<= 3

        decimal |= int(char)



    hex_char = "0123456789ABCDEF"



    revhex = ""

    while decimal:

    # 条件循环

        revhex += hex_char[decimal & 15]

        decimal >>= 4



    return "0x" + revhex[::-1]

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()



    nums = ["030", "100", "247", "235", "007"]



    ## Main Tests



    for num in nums:

    # 遍历循环

        hexadecimal = octal_to_hex(num)

        expected = "0x" + hex(int(num, 8))[2:].upper()



        assert hexadecimal == expected



        print(f"Hex of '0o{num}' is: {hexadecimal}")

        print(f"Expected was: {expected}")

        print("---")

