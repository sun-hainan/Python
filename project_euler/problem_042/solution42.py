# -*- coding: utf-8 -*-

"""

Project Euler Problem 042



解决 Project Euler 第 042 题的 Python 实现。

https://projecteuler.net/problem=042

"""



import os



# Precomputes a list of the 100 first triangular numbers

TRIANGULAR_NUMBERS = [int(0.5 * n * (n + 1)) for n in range(1, 101)]







# =============================================================================

# Project Euler 问题 042

# =============================================================================

def solution():

    """

    Finds the amount of triangular words in the words file.



    >>> solution()

    162

    """

    script_dir = os.path.dirname(os.path.realpath(__file__))

    words_file_path = os.path.join(script_dir, "words.txt")



    words = ""

    with open(words_file_path) as f:

        words = f.readline()



    words = [word.strip('"') for word in words.strip("\r\n").split(",")]

    words = [

        word

        for word in [sum(ord(x) - 64 for x in word) for word in words]

    # 遍历循环

        if word in TRIANGULAR_NUMBERS

    ]

    return len(words)

    # 返回结果





if __name__ == "__main__":

    print(solution())

