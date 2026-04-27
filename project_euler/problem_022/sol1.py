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

    with open(os.path.dirname(__file__) + "/p022_names.txt") as file:

        names = str(file.readlines()[0])

        names = names.replace('"', "").split(",")



    names.sort()



    name_score = 0

    total_score = 0



    for i, name in enumerate(names):

    # 遍历循环

        for letter in name:

            name_score += ord(letter) - 64



        total_score += (i + 1) * name_score

        name_score = 0

    return total_score

    # 返回结果





if __name__ == "__main__":

    print(solution())

