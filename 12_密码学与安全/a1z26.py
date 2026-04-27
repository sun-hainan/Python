# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / a1z26



本文件实现 a1z26 相关的算法功能。

"""



from __future__ import annotations



"""

Convert a string of characters to a sequence of numbers

corresponding to the character's position in the alphabet.



https://www.dcode.fr/letter-number-cipher

http://bestcodes.weebly.com/a1z26.html

"""









# encode 函数实现

def encode(plain: str) -> list[int]:

    """

    >>> encode("myname")

    [13, 25, 14, 1, 13, 5]

    """

    return [ord(elem) - 96 for elem in plain]

    # 返回结果







# decode 函数实现

def decode(encoded: list[int]) -> str:

    """

    >>> decode([13, 25, 14, 1, 13, 5])

    'myname'

    """

    return "".join(chr(elem + 96) for elem in encoded)

    # 返回结果







# main 函数实现

def main() -> None:

    encoded = encode(input("-> ").strip().lower())

    print("Encoded: ", encoded)

    print("Decoded:", decode(encoded))





if __name__ == "__main__":

    # 条件判断

    main()

