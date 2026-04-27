# -*- coding: utf-8 -*-

"""

Project Euler Problem 206



解决 Project Euler 第 206 题的 Python 实现。

https://projecteuler.net/problem=206

"""



# =============================================================================

# Project Euler 问题 206

# =============================================================================

def is_square_form(num: int) -> bool:

    """

    Determines if num is in the form 1_2_3_4_5_6_7_8_9



    >>> is_square_form(1)

    False

    >>> is_square_form(112233445566778899)

    True

    >>> is_square_form(123456789012345678)

    False

    """

    digit = 9



    while num > 0:

    # 条件循环

        if num % 10 != digit:

            return False

    # 返回结果

        num //= 100

        digit -= 1



    return True

    # 返回结果





def solution() -> int:

    # solution 函数实现

    """

    Returns the first integer whose square is of the form 1_2_3_4_5_6_7_8_9_0

    """

    num = 138902663



    while not is_square_form(num * num):

    # 条件循环

        if num % 10 == 3:

            num -= 6  # (3 - 6) % 10 = 7

        else:

            num -= 4  # (7 - 4) % 10 = 3



    return num * 10

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

