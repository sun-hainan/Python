# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / title

本文件实现 title 相关的算法功能。
"""

def to_title_case(word: str) -> str:
    # to_title_case function

    # to_title_case function
    # to_title_case 函数实现
    """
    Converts a string to capitalized case, preserving the input as is

    >>> to_title_case("Aakash")
    'Aakash'

    >>> to_title_case("aakash")
    'Aakash'

    >>> to_title_case("AAKASH")
    'Aakash'

    >>> to_title_case("aAkAsH")
    'Aakash'
    """

    """
    Convert the first character to uppercase if it's lowercase
    """
    if "a" <= word[0] <= "z":
        word = chr(ord(word[0]) - 32) + word[1:]

    """
    Convert the remaining characters to lowercase if they are uppercase
    """
    for i in range(1, len(word)):
        if "A" <= word[i] <= "Z":
            word = word[:i] + chr(ord(word[i]) + 32) + word[i + 1 :]

    return word


def sentence_to_title_case(input_str: str) -> str:
    # sentence_to_title_case function

    # sentence_to_title_case function
    # sentence_to_title_case 函数实现
    """
    Converts a string to title case, preserving the input as is

    >>> sentence_to_title_case("Aakash Giri")
    'Aakash Giri'

    >>> sentence_to_title_case("aakash giri")
    'Aakash Giri'

    >>> sentence_to_title_case("AAKASH GIRI")
    'Aakash Giri'

    >>> sentence_to_title_case("aAkAsH gIrI")
    'Aakash Giri'
    """

    return " ".join(to_title_case(word) for word in input_str.split())


if __name__ == "__main__":
    from doctest import testmod

    testmod()
