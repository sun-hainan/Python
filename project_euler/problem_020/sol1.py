# -*- coding: utf-8 -*-

"""

Project Euler Problem 020



解决 Project Euler 第 020 题的 Python 实现。

https://projecteuler.net/problem=020

"""



# =============================================================================

# Project Euler 问题 020

# =============================================================================

def factorial(num: int) -> int:

    """Find the factorial of a given number n"""

    fact = 1

    for i in range(1, num + 1):

    # 遍历循环

        fact *= i

    return fact

    # 返回结果





def split_and_add(number: int) -> int:

    # split_and_add 函数实现

    """Split number digits and add them."""

    sum_of_digits = 0

    while number > 0:

    # 条件循环

        last_digit = number % 10

        sum_of_digits += last_digit

        number = number // 10  # Removing the last_digit from the given number

    return sum_of_digits

    # 返回结果





def solution(num: int = 100) -> int:

    # solution 函数实现

    """Returns the sum of the digits in the factorial of num

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

    """

    nfact = factorial(num)

    result = split_and_add(nfact)

    return result

    # 返回结果





if __name__ == "__main__":

    print(solution(int(input("Enter the Number: ").strip())))

