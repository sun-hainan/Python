# -*- coding: utf-8 -*-
"""
算法实现：special_numbers / perfect_number

本文件实现 perfect_number 相关的算法功能。
"""

# =============================================================================
# 算法模块：perfect
# =============================================================================
def perfect(number: int) -> bool:
    # perfect function

    # perfect function
    """
    Check if a number is a perfect number.

    A perfect number is a positive integer that is equal to the sum of its proper
    divisors (excluding itself).

    Args:
        number: The number to be checked.

    Returns:
        True if the number is a perfect number, False otherwise.

    Start from 1 because dividing by 0 will raise ZeroDivisionError.
    A number at most can be divisible by the half of the number except the number
    itself. For example, 6 is at most can be divisible by 3 except by 6 itself.

    Examples:
    >>> perfect(27)
    False
    >>> perfect(28)
    True
    >>> perfect(29)
    False
    >>> perfect(6)
    True
    >>> perfect(12)
    False
    >>> perfect(496)
    True
    >>> perfect(8128)
    True
    >>> perfect(0)
    False
    >>> perfect(-1)
    False
    >>> perfect(12.34)
    Traceback (most recent call last):
      ...
    ValueError: number must be an integer
    >>> perfect("Hello")
    Traceback (most recent call last):
      ...
    ValueError: number must be an integer
    """
    if not isinstance(number, int):
        raise ValueError("number must be an integer")
    if number <= 0:
        return False
    return sum(i for i in range(1, number // 2 + 1) if number % i == 0) == number


if __name__ == "__main__":
    from doctest import testmod

    testmod()
    print("Program to check whether a number is a Perfect number or not...")
    try:
        number = int(input("Enter a positive integer: ").strip())
    except ValueError:
        msg = "number must be an integer"
        print(msg)
        raise ValueError(msg)

    print(f"{number} is {'' if perfect(number) else 'not '}a Perfect Number.")
