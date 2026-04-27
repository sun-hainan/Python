# -*- coding: utf-8 -*-

"""

Project Euler Problem 012



解决 Project Euler 第 012 题的 Python 实现。

https://projecteuler.net/problem=012

"""



# =============================================================================

# Project Euler 问题 012

# =============================================================================

def triangle_number_generator():

    for n in range(1, 1000000):

    # 遍历循环

        yield n * (n + 1) // 2





def count_divisors(n):

    # count_divisors 函数实现

    divisors_count = 1

    i = 2

    while i * i <= n:

    # 条件循环

        multiplicity = 0

        while n % i == 0:

    # 条件循环

            n //= i

            multiplicity += 1

        divisors_count *= multiplicity + 1

        i += 1

    if n > 1:

        divisors_count *= 2

    return divisors_count

    # 返回结果





def solution():

    # solution 函数实现

    """Returns the value of the first triangle number to have over five hundred

    divisors.



    >>> solution()

    76576500

    """

    return next(i for i in triangle_number_generator() if count_divisors(i) > 500)

    # 返回结果





if __name__ == "__main__":

    print(solution())

