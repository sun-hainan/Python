# -*- coding: utf-8 -*-

"""

Project Euler Problem 020



解决 Project Euler 第 020 题的 Python 实现。

https://projecteuler.net/problem=020

"""



from math import factorial







# =============================================================================

# Project Euler 问题 020

# =============================================================================

def solution(num: int = 100) -> int:

    """Returns the sum of the digits in the factorial of num

    >>> solution(1000)

    10539

    >>> solution(200)

    1404

    >>> solution(100)

    648

    >>> solution(50)

    216

    >>> solution(10)

    27

    >>> solution(5)

    3

    >>> solution(3)

    6

    >>> solution(2)

    2

    >>> solution(1)

    1

    >>> solution(0)

    1

    """

    return sum(map(int, str(factorial(num))))

    # 返回结果





if __name__ == "__main__":

    print(solution(int(input("Enter the Number: ").strip())))

