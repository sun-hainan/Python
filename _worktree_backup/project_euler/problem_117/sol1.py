# -*- coding: utf-8 -*-

"""

Project Euler Problem 117



解决 Project Euler 第 117 题的 Python 实现。

https://projecteuler.net/problem=117

"""



# =============================================================================

# Project Euler 问题 117

# =============================================================================

def solution(length: int = 50) -> int:

    """

    Returns the number of ways can a row of the given length be tiled



    >>> solution(5)

    15

    """



    ways_number = [1] * (length + 1)



    for row_length in range(length + 1):

    # 遍历循环

        for tile_length in range(2, 5):

            for tile_start in range(row_length - tile_length + 1):

    # 遍历循环

                ways_number[row_length] += ways_number[

                    row_length - tile_start - tile_length

                ]



    return ways_number[length]

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

