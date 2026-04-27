# -*- coding: utf-8 -*-

"""

Project Euler Problem 022



解决 Project Euler 第 022 题的 Python 实现。

https://projecteuler.net/problem=022

"""



import os







# =============================================================================

# Project Euler 问题 022

# =============================================================================

def solution():

    """Returns the total of all the name scores in the file.



    >>> solution()

    871198282

    """

    total_sum = 0

    temp_sum = 0

    with open(os.path.dirname(__file__) + "/p022_names.txt") as file:

        name = str(file.readlines()[0])

        name = name.replace('"', "").split(",")



    name.sort()

    for i in range(len(name)):

    # 遍历循环

        for j in name[i]:

            temp_sum += ord(j) - ord("A") + 1

        total_sum += (i + 1) * temp_sum

        temp_sum = 0

    return total_sum

    # 返回结果





if __name__ == "__main__":

    print(solution())

