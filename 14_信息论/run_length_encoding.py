# -*- coding: utf-8 -*-
"""
算法实现：14_信息论 / run_length_encoding

本文件实现 run_length_encoding 相关的算法功能。
"""

run_length_encoding.py
"""


def length_encode(text: str) -> list:
    """游程编码：将连续相同字符压缩为(字符, 次数)对"""
    encoded = []
    count = 1
    for i in range(len(text)):
        if i + 1 < len(text) and text[i] == text[i + 1]:
            count += 1
        else:
            encoded.append((text[i], count))
            count = 1
    return encoded


def length_decode(encoded: list) -> str:
    """游程解码：将(字符, 次数)对还原为字符串"""
    return "".join(char * length for char, length in encoded)


if __name__ == "__main__":
    from doctest import testmod
    testmod(name="run_length_encode", verbose=True)
    testmod(name="run_length_decode", verbose=True)
