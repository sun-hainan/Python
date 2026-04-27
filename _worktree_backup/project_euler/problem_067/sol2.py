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

def solution() -> int:

    """

    Finds the maximum total in a triangle as described by the problem statement

    above.

    >>> solution()

    7273

    """

    script_dir = os.path.dirname(os.path.realpath(__file__))

    triangle_path = os.path.join(script_dir, "triangle.txt")



    with open(triangle_path) as in_file:

        triangle = [[int(i) for i in line.split()] for line in in_file]



    while len(triangle) != 1:

    # 条件循环

        last_row = triangle.pop()

        curr_row = triangle[-1]

        for j in range(len(last_row) - 1):

    # 遍历循环

            curr_row[j] += max(last_row[j], last_row[j + 1])

    return triangle[0][0]

    # 返回结果





if __name__ == "__main__":

    print(solution())

