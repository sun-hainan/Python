# -*- coding: utf-8 -*-

"""

Project Euler Problem 097



解决 Project Euler 第 097 题的 Python 实现。

https://projecteuler.net/problem=097

"""



# =============================================================================

# Project Euler 问题 097

# =============================================================================

def solution(n: int = 10) -> str:

    """

    Returns the last n digits of NUMBER.

    >>> solution()

    '8739992577'

    >>> solution(8)

    '39992577'

    >>> solution(1)

    '7'

    >>> solution(-1)

    Traceback (most recent call last):

        ...

    ValueError: Invalid input

    >>> solution(8.3)

    Traceback (most recent call last):

        ...

    ValueError: Invalid input

    >>> solution("a")

    Traceback (most recent call last):

        ...

    ValueError: Invalid input

    """

    if not isinstance(n, int) or n < 0:

        raise ValueError("Invalid input")

    modulus = 10**n

    number = 28433 * (pow(2, 7830457, modulus)) + 1

    return str(number % modulus)

    # 返回结果





if __name__ == "__main__":

    from doctest import testmod



    testmod()

    print(f"{solution(10) = }")

