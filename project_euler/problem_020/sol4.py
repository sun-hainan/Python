# -*- coding: utf-8 -*-

"""

Project Euler Problem 020



解决 Project Euler 第 020 题的 Python 实现。

https://projecteuler.net/problem=020

"""



# =============================================================================

# Project Euler 问题 020

# =============================================================================

def solution(num: int = 100) -> int:

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

    fact = 1

    result = 0

    for i in range(1, num + 1):

    # 遍历循环

        fact *= i



    for j in str(fact):

    # 遍历循环

        result += int(j)



    return result

    # 返回结果





if __name__ == "__main__":

    print(solution(int(input("Enter the Number: ").strip())))

