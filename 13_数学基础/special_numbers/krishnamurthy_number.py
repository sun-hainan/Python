# -*- coding: utf-8 -*-
"""
算法实现：special_numbers / krishnamurthy_number

本文件实现 krishnamurthy_number 相关的算法功能。
"""

# =============================================================================
# 算法模块：factorial
# =============================================================================
def factorial(digit: int) -> int:
    # factorial function

    # factorial function
    """
    >>> factorial(3)
    6
    >>> factorial(0)
    1
    >>> factorial(5)
    120
    """

    return 1 if digit in (0, 1) else (digit * factorial(digit - 1))


def krishnamurthy(number: int) -> bool:
    # krishnamurthy function

    # krishnamurthy function
    """
    >>> krishnamurthy(145)
    True
    >>> krishnamurthy(240)
    False
    >>> krishnamurthy(1)
    True
    """

    fact_sum = 0
    duplicate = number
    while duplicate > 0:
        duplicate, digit = divmod(duplicate, 10)
        fact_sum += factorial(digit)
    return fact_sum == number


if __name__ == "__main__":
    print("Program to check whether a number is a Krisnamurthy Number or not.")
    number = int(input("Enter number: ").strip())
    print(
        f"{number} is {'' if krishnamurthy(number) else 'not '}a Krishnamurthy Number."
    )
