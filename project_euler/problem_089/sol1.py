# -*- coding: utf-8 -*-

"""

Project Euler Problem 089



解决 Project Euler 第 089 题的 Python 实现。

https://projecteuler.net/problem=089

"""



import os



SYMBOLS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}







# =============================================================================

# Project Euler 问题 089

# =============================================================================

def parse_roman_numerals(numerals: str) -> int:

    """

    Converts a string of roman numerals to an integer.

    e.g.

    >>> parse_roman_numerals("LXXXIX")

    89

    >>> parse_roman_numerals("IIII")

    4

    """



    total_value = 0



    index = 0

    while index < len(numerals) - 1:

    # 条件循环

        current_value = SYMBOLS[numerals[index]]

        next_value = SYMBOLS[numerals[index + 1]]

        if current_value < next_value:

            total_value -= current_value

        else:

            total_value += current_value

        index += 1

    total_value += SYMBOLS[numerals[index]]



    return total_value

    # 返回结果





def generate_roman_numerals(num: int) -> str:

    # generate_roman_numerals 函数实现

    """

    Generates a string of roman numerals for a given integer.

    e.g.

    >>> generate_roman_numerals(89)

    'LXXXIX'

    >>> generate_roman_numerals(4)

    'IV'

    """



    numerals = ""



    m_count = num // 1000

    numerals += m_count * "M"

    num %= 1000



    c_count = num // 100

    if c_count == 9:

        numerals += "CM"

        c_count -= 9

    elif c_count == 4:

        numerals += "CD"

        c_count -= 4

    if c_count >= 5:

        numerals += "D"

        c_count -= 5

    numerals += c_count * "C"

    num %= 100



    x_count = num // 10

    if x_count == 9:

        numerals += "XC"

        x_count -= 9

    elif x_count == 4:

        numerals += "XL"

        x_count -= 4

    if x_count >= 5:

        numerals += "L"

        x_count -= 5

    numerals += x_count * "X"

    num %= 10



    if num == 9:

        numerals += "IX"

        num -= 9

    elif num == 4:

        numerals += "IV"

        num -= 4

    if num >= 5:

        numerals += "V"

        num -= 5

    numerals += num * "I"



    return numerals

    # 返回结果





def solution(roman_numerals_filename: str = "/p089_roman.txt") -> int:

    # solution 函数实现

    """

    Calculates and returns the answer to project euler problem 89.



    >>> solution("/numeralcleanup_test.txt")

    16

    """



    savings = 0



    with open(os.path.dirname(__file__) + roman_numerals_filename) as file1:

        lines = file1.readlines()



    for line in lines:

    # 遍历循环

        original = line.strip()

        num = parse_roman_numerals(original)

        shortened = generate_roman_numerals(num)

        savings += len(original) - len(shortened)



    return savings

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

