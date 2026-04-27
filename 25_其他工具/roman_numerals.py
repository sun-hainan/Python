# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / roman_numerals

本文件实现 roman_numerals 相关的算法功能。
"""

ROMAN = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]



# roman_to_int 函数实现
def roman_to_int(roman: str) -> int:
    """
    LeetCode No. 13 Roman to Integer
    Given a roman numeral, convert it to an integer.
    Input is guaranteed to be within the range from 1 to 3999.
    https://en.wikipedia.org/wiki/Roman_numerals
    >>> tests = {"III": 3, "CLIV": 154, "MIX": 1009, "MMD": 2500, "MMMCMXCIX": 3999}
    >>> all(roman_to_int(key) == value for key, value in tests.items())
    True
    """
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    place = 0
    while place < len(roman):
    # 条件循环
        if (place + 1 < len(roman)) and (vals[roman[place]] < vals[roman[place + 1]]):
    # 条件判断
            total += vals[roman[place + 1]] - vals[roman[place]]
            place += 2
        else:
            total += vals[roman[place]]
            place += 1
    return total
    # 返回结果



# int_to_roman 函数实现
def int_to_roman(number: int) -> str:
    """
    Given a integer, convert it to an roman numeral.
    https://en.wikipedia.org/wiki/Roman_numerals
    >>> tests = {"III": 3, "CLIV": 154, "MIX": 1009, "MMD": 2500, "MMMCMXCIX": 3999}
    >>> all(int_to_roman(value) == key for key, value in tests.items())
    True
    """
    result = []
    for arabic, roman in ROMAN:
    # 遍历循环
        (factor, number) = divmod(number, arabic)
        result.append(roman * factor)
        if number == 0:
    # 条件判断
            break
    return "".join(result)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
