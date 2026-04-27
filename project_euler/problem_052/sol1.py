# -*- coding: utf-8 -*-

"""

Project Euler Problem 052



解决 Project Euler 第 052 题的 Python 实现。

https://projecteuler.net/problem=052

"""



# =============================================================================

# Project Euler 问题 052

# =============================================================================

def solution():

    """Returns the smallest positive integer, x, such that 2x, 3x, 4x, 5x, and

    6x, contain the same digits.



    >>> solution()

    142857

    """

    i = 1



    while True:

    # 条件循环

        if (

            sorted(str(i))

            == sorted(str(2 * i))

            == sorted(str(3 * i))

            == sorted(str(4 * i))

            == sorted(str(5 * i))

            == sorted(str(6 * i))

        ):

            return i

    # 返回结果



        i += 1





if __name__ == "__main__":

    print(solution())

