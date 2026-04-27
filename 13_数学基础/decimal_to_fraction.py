# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / decimal_to_fraction

本文件实现 decimal_to_fraction 相关的算法功能。
"""

# =============================================================================
# 算法模块：decimal_to_fraction
# =============================================================================
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

def decimal_to_fraction(decimal: float | str) -> tuple[int, int]:
    # decimal_to_fraction function

    # decimal_to_fraction function
    """
    Return a decimal number in its simplest fraction form
    >>> decimal_to_fraction(2)
    (2, 1)
    >>> decimal_to_fraction(89.)
    (89, 1)
    >>> decimal_to_fraction("67")
    (67, 1)
    >>> decimal_to_fraction("45.0")
    (45, 1)
    >>> decimal_to_fraction(1.5)
    (3, 2)
    >>> decimal_to_fraction("6.25")
    (25, 4)
    >>> decimal_to_fraction("78td")
    Traceback (most recent call last):
    ValueError: Please enter a valid number
    >>> decimal_to_fraction(0)
    (0, 1)
    >>> decimal_to_fraction(-2.5)
    (-5, 2)
    >>> decimal_to_fraction(0.125)
    (1, 8)
    >>> decimal_to_fraction(1000000.25)
    (4000001, 4)
    >>> decimal_to_fraction(1.3333)
    (13333, 10000)
    >>> decimal_to_fraction("1.23e2")
    (123, 1)
    >>> decimal_to_fraction("0.500")
    (1, 2)
    """

    try:
        decimal = float(decimal)
    except ValueError:
        raise ValueError("Please enter a valid number")
    fractional_part = decimal - int(decimal)
    if fractional_part == 0:
        return int(decimal), 1
    else:
        number_of_frac_digits = len(str(decimal).split(".")[1])
        numerator = int(decimal * (10**number_of_frac_digits))
        denominator = 10**number_of_frac_digits
        divisor, dividend = denominator, numerator
        while True:
            remainder = dividend % divisor
            if remainder == 0:
                break
            dividend, divisor = divisor, remainder
        numerator, denominator = numerator // divisor, denominator // divisor
        return numerator, denominator


if __name__ == "__main__":
    print(f"{decimal_to_fraction(2) = }")
    print(f"{decimal_to_fraction(89.0) = }")
    print(f"{decimal_to_fraction('67') = }")
    print(f"{decimal_to_fraction('45.0') = }")
    print(f"{decimal_to_fraction(1.5) = }")
    print(f"{decimal_to_fraction('6.25') = }")
    print(f"{decimal_to_fraction('78td') = }")
