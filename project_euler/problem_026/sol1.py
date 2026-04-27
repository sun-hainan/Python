# -*- coding: utf-8 -*-

"""

Project Euler Problem 026



解决 Project Euler 第 026 题的 Python 实现。

https://projecteuler.net/problem=026

"""



# =============================================================================

# Project Euler 问题 026

# =============================================================================

def solution(numerator: int = 1, digit: int = 1000) -> int:

    """

    Considering any range can be provided,

    because as per the problem, the digit d < 1000

    >>> solution(1, 10)

    7

    >>> solution(10, 100)

    97

    >>> solution(10, 1000)

    983

    """

    the_digit = 1

    longest_list_length = 0



    for divide_by_number in range(numerator, digit + 1):

    # 遍历循环

        has_been_divided: list[int] = []

        now_divide = numerator

        for _ in range(1, digit + 1):

    # 遍历循环

            if now_divide in has_been_divided:

                if longest_list_length < len(has_been_divided):

                    longest_list_length = len(has_been_divided)

                    the_digit = divide_by_number

            else:

                has_been_divided.append(now_divide)

                now_divide = now_divide * 10 % divide_by_number



    return the_digit

    # 返回结果





# Tests

if __name__ == "__main__":

    import doctest



    doctest.testmod()

