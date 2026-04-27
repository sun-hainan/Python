# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / playfair_cipher

本文件实现 playfair_cipher 相关的算法功能。
"""

import itertools
import string
from collections.abc import Generator, Iterable



# chunker 函数实现
def chunker(seq: Iterable[str], size: int) -> Generator[tuple[str, ...]]:
    it = iter(seq)
    while True:
    # 条件循环
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
    # 条件判断
            return
        yield chunk



# prepare_input 函数实现
def prepare_input(dirty: str) -> str:
    """
    Prepare the plaintext by up-casing it
    and separating repeated letters with X's
    """

    dirty = "".join([c.upper() for c in dirty if c in string.ascii_letters])
    clean = ""

    if len(dirty) < 2:
    # 条件判断
        return dirty
    # 返回结果

    for i in range(len(dirty) - 1):
    # 遍历循环
        clean += dirty[i]

        if dirty[i] == dirty[i + 1]:
    # 条件判断
            clean += "X"

    clean += dirty[-1]

    if len(clean) & 1:
    # 条件判断
        clean += "X"

    return clean
    # 返回结果



# generate_table 函数实现
def generate_table(key: str) -> list[str]:
    # I and J are used interchangeably to allow
    # us to use a 5x5 table (25 letters)
    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    # we're using a list instead of a '2d' array because it makes the math
    # for setting up the table and doing the actual encoding/decoding simpler
    table = []

    # copy key chars into the table if they are in `alphabet` ignoring duplicates
    for char in key.upper():
    # 遍历循环
        if char not in table and char in alphabet:
    # 条件判断
            table.append(char)

    # fill the rest of the table in with the remaining alphabet chars
    for char in alphabet:
    # 遍历循环
        if char not in table:
    # 条件判断
            table.append(char)

    return table
    # 返回结果



# encode 函数实现
def encode(plaintext: str, key: str) -> str:
    """
    Encode the given plaintext using the Playfair cipher.
    Takes the plaintext and the key as input and returns the encoded string.

    >>> encode("Hello", "MONARCHY")
    'CFSUPM'
    >>> encode("attack on the left flank", "EMERGENCY")
    'DQZSBYFSDZFMFNLOHFDRSG'
    >>> encode("Sorry!", "SPECIAL")
    'AVXETX'
    >>> encode("Number 1", "NUMBER")
    'UMBENF'
    >>> encode("Photosynthesis!", "THE SUN")
    'OEMHQHVCHESUKE'
    """

    table = generate_table(key)
    plaintext = prepare_input(plaintext)
    ciphertext = ""

    for char1, char2 in chunker(plaintext, 2):
    # 遍历循环
        row1, col1 = divmod(table.index(char1), 5)
        row2, col2 = divmod(table.index(char2), 5)

        if row1 == row2:
    # 条件判断
            ciphertext += table[row1 * 5 + (col1 + 1) % 5]
            ciphertext += table[row2 * 5 + (col2 + 1) % 5]
        elif col1 == col2:
            ciphertext += table[((row1 + 1) % 5) * 5 + col1]
            ciphertext += table[((row2 + 1) % 5) * 5 + col2]
        else:  # rectangle
            ciphertext += table[row1 * 5 + col2]
            ciphertext += table[row2 * 5 + col1]

    return ciphertext
    # 返回结果



# decode 函数实现
def decode(ciphertext: str, key: str) -> str:
    """
    Decode the input string using the provided key.

    >>> decode("BMZFAZRZDH", "HAZARD")
    'FIREHAZARD'
    >>> decode("HNBWBPQT", "AUTOMOBILE")
    'DRIVINGX'
    >>> decode("SLYSSAQS", "CASTLE")
    'ATXTACKX'
    """

    table = generate_table(key)
    plaintext = ""

    for char1, char2 in chunker(ciphertext, 2):
    # 遍历循环
        row1, col1 = divmod(table.index(char1), 5)
        row2, col2 = divmod(table.index(char2), 5)

        if row1 == row2:
    # 条件判断
            plaintext += table[row1 * 5 + (col1 - 1) % 5]
            plaintext += table[row2 * 5 + (col2 - 1) % 5]
        elif col1 == col2:
            plaintext += table[((row1 - 1) % 5) * 5 + col1]
            plaintext += table[((row2 - 1) % 5) * 5 + col2]
        else:  # rectangle
            plaintext += table[row1 * 5 + col2]
            plaintext += table[row2 * 5 + col1]

    return plaintext
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

    print("Encoded:", encode("BYE AND THANKS", "GREETING"))
    print("Decoded:", decode("CXRBANRLBALQ", "GREETING"))
