# -*- coding: utf-8 -*-

"""

Project Euler Problem 119



解决 Project Euler 第 119 题的 Python 实现。

https://projecteuler.net/problem=119

"""



import math







# =============================================================================

# Project Euler 问题 119

# =============================================================================

def digit_sum(n: int) -> int:

    """

    Returns the sum of the digits of the number.

    >>> digit_sum(123)

    6

    >>> digit_sum(456)

    15

    >>> digit_sum(78910)

    25

    """

    return sum(int(digit) for digit in str(n))

    # 返回结果





def solution(n: int = 30) -> int:

    # solution 函数实现

    """

    Returns the value of 30th digit power sum.

    >>> solution(2)

    512

    >>> solution(5)

    5832

    >>> solution(10)

    614656

    """

    digit_to_powers = []

    for digit in range(2, 100):

    # 遍历循环

        for power in range(2, 100):

            number = int(math.pow(digit, power))

            if digit == digit_sum(number):

                digit_to_powers.append(number)



    digit_to_powers.sort()

    return digit_to_powers[n - 1]

    # 返回结果





if __name__ == "__main__":

    print(solution())

