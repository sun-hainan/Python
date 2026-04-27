# -*- coding: utf-8 -*-

"""

Project Euler Problem 180



解决 Project Euler 第 180 题的 Python 实现。

https://projecteuler.net/problem=180

"""



from __future__ import annotations



"""

Project Euler Problem 180 — 中文注释版

https://projecteuler.net/problem=180



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""









from fractions import Fraction

from math import gcd, sqrt







# =============================================================================

# Project Euler 问题 180

# =============================================================================

def is_sq(number: int) -> bool:

    """

    Check if number is a perfect square.



    >>> is_sq(1)

    True

    >>> is_sq(1000001)

    False

    >>> is_sq(1000000)

    True

    """

    sq: int = int(number**0.5)

    return number == sq * sq

    # 返回结果





def add_three(

    # add_three 函数实现

    x_num: int, x_den: int, y_num: int, y_den: int, z_num: int, z_den: int

) -> tuple[int, int]:

    """

    Given the numerators and denominators of three fractions, return the

    numerator and denominator of their sum in lowest form.

    >>> add_three(1, 3, 1, 3, 1, 3)

    (1, 1)

    >>> add_three(2, 5, 4, 11, 12, 3)

    (262, 55)

    """

    top: int = x_num * y_den * z_den + y_num * x_den * z_den + z_num * x_den * y_den

    bottom: int = x_den * y_den * z_den

    hcf: int = gcd(top, bottom)

    top //= hcf

    bottom //= hcf

    return top, bottom

    # 返回结果





def solution(order: int = 35) -> int:

    # solution 函数实现

    """

    Find the sum of the numerator and denominator of the sum of all s(x,y,z) for

    golden triples (x,y,z) of the given order.



    >>> solution(5)

    296

    >>> solution(10)

    12519

    >>> solution(20)

    19408891927

    """

    unique_s: set = set()

    hcf: int

    total: Fraction = Fraction(0)

    fraction_sum: tuple[int, int]



    for x_num in range(1, order + 1):

    # 遍历循环

        for x_den in range(x_num + 1, order + 1):

            for y_num in range(1, order + 1):

    # 遍历循环

                for y_den in range(y_num + 1, order + 1):

                    # n=1

                    z_num = x_num * y_den + x_den * y_num

                    z_den = x_den * y_den

                    hcf = gcd(z_num, z_den)

                    z_num //= hcf

                    z_den //= hcf

                    if 0 < z_num < z_den <= order:

                        fraction_sum = add_three(

                            x_num, x_den, y_num, y_den, z_num, z_den

                        )

                        unique_s.add(fraction_sum)



                    # n=2

                    z_num = (

                        x_num * x_num * y_den * y_den + x_den * x_den * y_num * y_num

                    )

                    z_den = x_den * x_den * y_den * y_den

                    if is_sq(z_num) and is_sq(z_den):

                        z_num = int(sqrt(z_num))

                        z_den = int(sqrt(z_den))

                        hcf = gcd(z_num, z_den)

                        z_num //= hcf

                        z_den //= hcf

                        if 0 < z_num < z_den <= order:

                            fraction_sum = add_three(

                                x_num, x_den, y_num, y_den, z_num, z_den

                            )

                            unique_s.add(fraction_sum)



                    # n=-1

                    z_num = x_num * y_num

                    z_den = x_den * y_num + x_num * y_den

                    hcf = gcd(z_num, z_den)

                    z_num //= hcf

                    z_den //= hcf

                    if 0 < z_num < z_den <= order:

                        fraction_sum = add_three(

                            x_num, x_den, y_num, y_den, z_num, z_den

                        )

                        unique_s.add(fraction_sum)



                    # n=2

                    z_num = x_num * x_num * y_num * y_num

                    z_den = (

                        x_den * x_den * y_num * y_num + x_num * x_num * y_den * y_den

                    )

                    if is_sq(z_num) and is_sq(z_den):

                        z_num = int(sqrt(z_num))

                        z_den = int(sqrt(z_den))

                        hcf = gcd(z_num, z_den)

                        z_num //= hcf

                        z_den //= hcf

                        if 0 < z_num < z_den <= order:

                            fraction_sum = add_three(

                                x_num, x_den, y_num, y_den, z_num, z_den

                            )

                            unique_s.add(fraction_sum)



    for num, den in unique_s:

    # 遍历循环

        total += Fraction(num, den)



    return total.denominator + total.numerator

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

