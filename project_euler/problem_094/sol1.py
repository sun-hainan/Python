# -*- coding: utf-8 -*-

"""

Project Euler Problem 094



解决 Project Euler 第 094 题的 Python 实现。

https://projecteuler.net/problem=094

"""



# =============================================================================

# Project Euler 问题 094

# =============================================================================

def solution(max_perimeter: int = 10**9) -> int:

    """

    Returns the sum of the perimeters of all almost equilateral triangles with integral

    side lengths and area and whose perimeters do not exceed max_perimeter



    >>> solution(20)

    16

    """



    prev_value = 1

    value = 2



    perimeters_sum = 0

    i = 0

    perimeter = 0

    while perimeter <= max_perimeter:

    # 条件循环

        perimeters_sum += perimeter



        prev_value += 2 * value

        value += prev_value



        perimeter = 2 * value + 2 if i % 2 == 0 else 2 * value - 2

        i += 1



    return perimeters_sum

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

