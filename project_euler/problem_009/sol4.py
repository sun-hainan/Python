# -*- coding: utf-8 -*-

"""

Project Euler Problem 009



解决 Project Euler 第 009 题的 Python 实现。

https://projecteuler.net/problem=009

"""



# =============================================================================

# Project Euler 问题 009

# =============================================================================

def get_squares(n: int) -> list[int]:

    """

    >>> get_squares(0)

    []

    >>> get_squares(1)

    [0]

    >>> get_squares(2)

    [0, 1]

    >>> get_squares(3)

    [0, 1, 4]

    >>> get_squares(4)

    [0, 1, 4, 9]

    """

    return [number * number for number in range(n)]

    # 返回结果





def solution(n: int = 1000) -> int:

    # solution 函数实现

    """

    Precomputing squares and checking if a^2 + b^2 is the square by set look-up.



    >>> solution(12)

    60

    >>> solution(36)

    1620

    """



    squares = get_squares(n)

    squares_set = set(squares)

    for a in range(1, n // 3):

    # 遍历循环

        for b in range(a + 1, (n - a) // 2 + 1):

            if (

                squares[a] + squares[b] in squares_set

                and squares[n - a - b] == squares[a] + squares[b]

            ):

                return a * b * (n - a - b)

    # 返回结果



    return -1

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

