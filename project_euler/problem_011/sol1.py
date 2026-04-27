# -*- coding: utf-8 -*-

"""

Project Euler Problem 011



解决 Project Euler 第 011 题的 Python 实现。

https://projecteuler.net/problem=011

"""



import os







# =============================================================================

# Project Euler 问题 011

# =============================================================================

def largest_product(grid):

    n_columns = len(grid[0])

    n_rows = len(grid)



    largest = 0

    lr_diag_product = 0

    rl_diag_product = 0



    # Check vertically, horizontally, diagonally at the same time (only works

    # for nxn grid)

    for i in range(n_columns):

    # 遍历循环

        for j in range(n_rows - 3):

            vert_product = grid[j][i] * grid[j + 1][i] * grid[j + 2][i] * grid[j + 3][i]

            horz_product = grid[i][j] * grid[i][j + 1] * grid[i][j + 2] * grid[i][j + 3]



            # Left-to-right diagonal (\) product

            if i < n_columns - 3:

                lr_diag_product = (

                    grid[i][j]

                    * grid[i + 1][j + 1]

                    * grid[i + 2][j + 2]

                    * grid[i + 3][j + 3]

                )



            # Right-to-left diagonal(/) product

            if i > 2:

                rl_diag_product = (

                    grid[i][j]

                    * grid[i - 1][j + 1]

                    * grid[i - 2][j + 2]

                    * grid[i - 3][j + 3]

                )



            max_product = max(

                vert_product, horz_product, lr_diag_product, rl_diag_product

            )

            largest = max(largest, max_product)



    return largest

    # 返回结果





def solution():

    # solution 函数实现

    """Returns the greatest product of four adjacent numbers (horizontally,

    vertically, or diagonally).



    >>> solution()

    70600674

    """

    grid = []

    with open(os.path.dirname(__file__) + "/grid.txt") as file:

        for line in file:

    # 遍历循环

            grid.append(line.strip("\n").split(" "))



    grid = [[int(i) for i in grid[j]] for j in range(len(grid))]



    return largest_product(grid)

    # 返回结果





if __name__ == "__main__":

    print(solution())

