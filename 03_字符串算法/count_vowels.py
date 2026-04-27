# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / count_vowels

本文件实现 count_vowels 相关的算法功能。
"""

def count_vowels(s: str) -> int:
    # count_vowels function

    # count_vowels function
    # count_vowels 函数实现
    """
    Count the number of vowels in a given string.

    :param s: Input string to count vowels in.
    :return: Number of vowels in the input string.

    Examples:
    >>> count_vowels("hello world")
    3
    >>> count_vowels("HELLO WORLD")
    3
    >>> count_vowels("123 hello world")
    3
    >>> count_vowels("")
    0
    >>> count_vowels("a quick brown fox")
    5
    >>> count_vowels("the quick BROWN fox")
    5
    >>> count_vowels("PYTHON")
    1
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    vowels = "aeiouAEIOU"
    return sum(1 for char in s if char in vowels)


if __name__ == "__main__":
    from doctest import testmod

    testmod()
