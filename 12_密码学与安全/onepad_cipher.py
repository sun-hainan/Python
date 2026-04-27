# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / onepad_cipher

本文件实现 onepad_cipher 相关的算法功能。
"""

import random


class Onepad:
    @staticmethod

# encrypt 函数实现
    def encrypt(text: str) -> tuple[list[int], list[int]]:
        """
        Function to encrypt text using pseudo-random numbers
        >>> Onepad().encrypt("")
        ([], [])
        >>> Onepad().encrypt([])
        ([], [])
        >>> random.seed(1)
        >>> Onepad().encrypt(" ")
        ([6969], [69])
        >>> random.seed(1)
        >>> Onepad().encrypt("Hello")
        ([9729, 114756, 4653, 31309, 10492], [69, 292, 33, 131, 61])
        >>> Onepad().encrypt(1)
        Traceback (most recent call last):
        ...
        TypeError: 'int' object is not iterable
        >>> Onepad().encrypt(1.1)
        Traceback (most recent call last):
        ...
        TypeError: 'float' object is not iterable
        """
        plain = [ord(i) for i in text]
        key = []
        cipher = []
        for i in plain:
    # 遍历循环
            k = random.randint(1, 300)
            c = (i + k) * k
            cipher.append(c)
            key.append(k)
        return cipher, key
    # 返回结果

    @staticmethod

# decrypt 函数实现
    def decrypt(cipher: list[int], key: list[int]) -> str:
        """
        Function to decrypt text using pseudo-random numbers.
        >>> Onepad().decrypt([], [])
        ''
        >>> Onepad().decrypt([35], [])
        ''
        >>> Onepad().decrypt([], [35])
        Traceback (most recent call last):
        ...
        IndexError: list index out of range
        >>> random.seed(1)
        >>> Onepad().decrypt([9729, 114756, 4653, 31309, 10492], [69, 292, 33, 131, 61])
        'Hello'
        """
        plain = []
        for i in range(len(key)):
    # 遍历循环
            p = int((cipher[i] - (key[i]) ** 2) / key[i])
            plain.append(chr(p))
        return "".join(plain)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    c, k = Onepad().encrypt("Hello")
    print(c, k)
    print(Onepad().decrypt(c, k))
