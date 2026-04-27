# -*- coding: utf-8 -*-

"""

Project Euler Problem 032



解决 Project Euler 第 032 题的 Python 实现。

https://projecteuler.net/problem=032

"""



import itertools







# =============================================================================

# Project Euler 问题 032

# =============================================================================

def is_combination_valid(combination):

    """

    Checks if a combination (a tuple of 9 digits)

    is a valid product equation.



    >>> is_combination_valid(('3', '9', '1', '8', '6', '7', '2', '5', '4'))

    True



    >>> is_combination_valid(('1', '2', '3', '4', '5', '6', '7', '8', '9'))

    False



    """

    return (

    # 返回结果

        int("".join(combination[0:2])) * int("".join(combination[2:5]))

        == int("".join(combination[5:9]))

    ) or (

        int("".join(combination[0])) * int("".join(combination[1:5]))

        == int("".join(combination[5:9]))

    )





def solution():

    # solution 函数实现

    """

    Finds the sum of all products whose multiplicand/multiplier/product identity

    can be written as a 1 through 9 pandigital



    >>> solution()

    45228

    """



    return sum(

    # 返回结果

        {

            int("".join(pandigital[5:9]))

            for pandigital in itertools.permutations("123456789")

    # 遍历循环

            if is_combination_valid(pandigital)

        }

    )





if __name__ == "__main__":

    print(solution())

