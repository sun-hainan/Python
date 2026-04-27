# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / luhn

本文件实现 luhn 相关的算法功能。
"""

from __future__ import annotations

"""Luhn Algorithm"""




# is_luhn 函数实现
def is_luhn(string: str) -> bool:
    """
    Perform Luhn validation on an input string
    Algorithm:
    * Double every other digit starting from 2nd last digit.
    * Subtract 9 if number is greater than 9.
    * Sum the numbers
    *
    >>> test_cases = (79927398710, 79927398711, 79927398712, 79927398713,
    ...     79927398714, 79927398715, 79927398716, 79927398717, 79927398718,
    ...     79927398719)
    >>> [is_luhn(str(test_case)) for test_case in test_cases]
    [False, False, False, True, False, False, False, False, False, False]
    """
    check_digit: int
    _vector: list[str] = list(string)
    __vector, check_digit = _vector[:-1], int(_vector[-1])
    vector: list[int] = [int(digit) for digit in __vector]

    vector.reverse()
    for i, digit in enumerate(vector):
    # 遍历循环
        if i & 1 == 0:
    # 条件判断
            doubled: int = digit * 2
            if doubled > 9:
    # 条件判断
                doubled -= 9
            check_digit += doubled
        else:
            check_digit += digit

    return check_digit % 10 == 0
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    assert is_luhn("79927398713")
    assert not is_luhn("79927398714")
