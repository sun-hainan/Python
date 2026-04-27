# -*- coding: utf-8 -*-

"""

Project Euler Problem 013



解决 Project Euler 第 013 题的 Python 实现。

https://projecteuler.net/problem=013

"""



import os







# =============================================================================

# Project Euler 问题 013

# =============================================================================

def solution():

    """

    Returns the first ten digits of the sum of the array elements

    from the file num.txt



    >>> solution()

    '5537376230'

    """

    file_path = os.path.join(os.path.dirname(__file__), "num.txt")

    with open(file_path) as file_hand:

        return str(sum(int(line) for line in file_hand))[:10]

    # 返回结果





if __name__ == "__main__":

    print(solution())

