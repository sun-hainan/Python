# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / is_isogram

本文件实现 is_isogram 相关的算法功能。
"""

def is_isogram(string: str) -> bool:
    # is_isogram function

    # is_isogram function
    # is_isogram 函数实现
    """
    An isogram is a word in which no letter is repeated.
    Examples of isograms are uncopyrightable and ambidextrously.
    >>> is_isogram('Uncopyrightable')
    True
    >>> is_isogram('allowance')
    False
    >>> is_isogram('copy1')
    Traceback (most recent call last):
     ...
    ValueError: String must only contain alphabetic characters.
    """
    if not all(x.isalpha() for x in string):
        raise ValueError("String must only contain alphabetic characters.")

    letters = sorted(string.lower())
    return len(letters) == len(set(letters))


if __name__ == "__main__":
    input_str = input("Enter a string ").strip()

    isogram = is_isogram(input_str)
    print(f"{input_str} is {'an' if isogram else 'not an'} isogram.")
