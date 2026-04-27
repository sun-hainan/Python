# -*- coding: utf-8 -*-

"""

Project Euler Problem 067



解决 Project Euler 第 067 题的 Python 实现。

https://projecteuler.net/problem=067

"""



import os







# =============================================================================

# Project Euler 问题 067

# =============================================================================

def solution():

    """

    Finds the maximum total in a triangle as described by the problem statement

    above.



    >>> solution()

    7273

    """

    script_dir = os.path.dirname(os.path.realpath(__file__))

    triangle = os.path.join(script_dir, "triangle.txt")



    with open(triangle) as f:

        triangle = f.readlines()



    a = []

    for line in triangle:

    # 遍历循环

        numbers_from_line = []

        for number in line.strip().split(" "):

    # 遍历循环

            numbers_from_line.append(int(number))

        a.append(numbers_from_line)



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

