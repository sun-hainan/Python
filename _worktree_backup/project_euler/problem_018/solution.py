# -*- coding: utf-8 -*-

"""

Project Euler Problem 018



解决 Project Euler 第 018 题的 Python 实现。

https://projecteuler.net/problem=018

"""



import os







# =============================================================================

# Project Euler 问题 018

# =============================================================================

def solution():

    """

    Finds the maximum total in a triangle as described by the problem statement

    above.



    >>> solution()

    1074

    """

    script_dir = os.path.dirname(os.path.realpath(__file__))

    triangle = os.path.join(script_dir, "triangle.txt")



    with open(triangle) as f:

        triangle = f.readlines()



    a = [[int(y) for y in x.rstrip("\r\n").split(" ")] for x in triangle]



    for i in range(1, len(a)):

    # 遍历循环

        for j in range(len(a[i])):

            number1 = a[i - 1][j] if j != len(a[i - 1]) else 0

            number2 = a[i - 1][j - 1] if j > 0 else 0

            a[i][j] += max(number1, number2)

    return max(a[-1])

    # 返回结果





if __name__ == "__main__":

    print(solution())

