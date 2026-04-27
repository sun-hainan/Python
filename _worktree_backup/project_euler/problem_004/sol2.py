# -*- coding: utf-8 -*-

"""

Project Euler Problem 004



解决 Project Euler 第 004 题的 Python 实现。

https://projecteuler.net/problem=004

"""



# =============================================================================

# Project Euler 问题 004

# =============================================================================

def solution(n: int = 998001) -> int:

    """

    Returns the largest palindrome made from the product of two 3-digit

    numbers which is less than n.



    >>> solution(20000)

    19591

    >>> solution(30000)

    29992

    >>> solution(40000)

    39893

    """



    answer = 0

    for i in range(999, 99, -1):  # 3 digit numbers range from 999 down to 100

        for j in range(999, 99, -1):

    # 遍历循环

            product_string = str(i * j)

            if product_string == product_string[::-1] and i * j < n:

                answer = max(answer, i * j)

    return answer

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

