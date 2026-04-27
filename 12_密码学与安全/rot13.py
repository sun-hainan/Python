# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / rot13

本文件实现 rot13 相关的算法功能。
"""

# dencrypt 函数实现
def dencrypt(s: str, n: int = 13) -> str:
    """
    https://en.wikipedia.org/wiki/ROT13

    >>> msg = "My secret bank account number is 173-52946 so don't tell anyone!!"
    >>> s = dencrypt(msg)
    >>> s
    "Zl frperg onax nppbhag ahzore vf 173-52946 fb qba'g gryy nalbar!!"
    >>> dencrypt(s) == msg
    True
    """
    out = ""
    for c in s:
    # 遍历循环
        if "A" <= c <= "Z":
    # 条件判断
            out += chr(ord("A") + (ord(c) - ord("A") + n) % 26)
        elif "a" <= c <= "z":
            out += chr(ord("a") + (ord(c) - ord("a") + n) % 26)
        else:
            out += c
    return out
    # 返回结果



# main 函数实现
def main() -> None:
    s0 = input("Enter message: ")

    s1 = dencrypt(s0, 13)
    print("Encryption:", s1)

    s2 = dencrypt(s1, 13)
    print("Decryption: ", s2)


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    main()
