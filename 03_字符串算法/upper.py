# -*- coding: utf-8 -*-

"""

算法实现：03_字符串算法 / upper



本文件实现 upper 相关的算法功能。

"""



def upper(word: str) -> str:

    # upper function



    # upper function

    # upper 函数实现

    """

    Convert an entire string to ASCII uppercase letters by looking for lowercase ASCII

    letters and subtracting 32 from their integer representation to get the uppercase

    letter.



    >>> upper("wow")

    'WOW'

    >>> upper("Hello")

    'HELLO'

    >>> upper("WHAT")

    'WHAT'

    >>> upper("wh[]32")

    'WH[]32'

    """

    return "".join(chr(ord(char) - 32) if "a" <= char <= "z" else char for char in word)





if __name__ == "__main__":

    from doctest import testmod



    testmod()

