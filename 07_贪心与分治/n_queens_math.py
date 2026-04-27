# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / n_queens_math

本文件实现 n_queens_math 相关的算法功能。
"""

def n_queens_solution(n: int) -> None:
    boards: list[list[str]] = []
    depth_first_search([], [], [], boards, n)

    # Print all the boards
    for board in boards:
        for column in board:
            print(column)
        print("")

    print(len(boards), "solutions were found.")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    n_queens_solution(4)
