# -*- coding: utf-8 -*-

"""

Project Euler Problem 345



解决 Project Euler 第 345 题的 Python 实现。

https://projecteuler.net/problem=345

"""



import numpy as np

from numpy.typing import NDArray



MATRIX_1 = [

    "7 53 183 439 863",

    "497 383 563 79 973",

    "287 63 343 169 583",

    "627 343 773 959 943",

    "767 473 103 699 303",

]



MATRIX_2 = [

    "7 53 183 439 863 497 383 563 79 973 287 63 343 169 583",

    "627 343 773 959 943 767 473 103 699 303 957 703 583 639 913",

    "447 283 463 29 23 487 463 993 119 883 327 493 423 159 743",

    "217 623 3 399 853 407 103 983 89 463 290 516 212 462 350",

    "960 376 682 962 300 780 486 502 912 800 250 346 172 812 350",

    "870 456 192 162 593 473 915 45 989 873 823 965 425 329 803",

    "973 965 905 919 133 673 665 235 509 613 673 815 165 992 326",

    "322 148 972 962 286 255 941 541 265 323 925 281 601 95 973",

    "445 721 11 525 473 65 511 164 138 672 18 428 154 448 848",

    "414 456 310 312 798 104 566 520 302 248 694 976 430 392 198",

    "184 829 373 181 631 101 969 613 840 740 778 458 284 760 390",

    "821 461 843 513 17 901 711 993 293 157 274 94 192 156 574",

    "34 124 4 878 450 476 712 914 838 669 875 299 823 329 699",

    "815 559 813 459 522 788 168 586 966 232 308 833 251 631 107",

    "813 883 451 509 615 77 281 613 459 205 380 274 302 35 805",

]







# =============================================================================

# Project Euler 问题 345

# =============================================================================

def solve(arr: NDArray, row: int, cols: set[int], cache: dict[str, int]) -> int:

    """

    Finds the max sum for array `arr` starting with row index `row`, and with columns

    included in `cols`. `cache` is used for caching intermediate results.



    >>> solve(arr=np.array([[1, 2], [3, 4]]), row=0, cols={0, 1}, cache={})

    5

    """



    cache_id = f"{row}, {sorted(cols)}"

    if cache_id in cache:

        return cache[cache_id]

    # 返回结果



    if row == len(arr):

        return 0

    # 返回结果



    max_sum = 0

    for col in cols:

    # 遍历循环

        new_cols = cols - {col}

        max_sum = max(

            max_sum,

            int(arr[row, col])

            + solve(arr=arr, row=row + 1, cols=new_cols, cache=cache),

        )

    cache[cache_id] = max_sum

    return max_sum

    # 返回结果





def solution(matrix_str: list[str] = MATRIX_2) -> int:

    # solution 函数实现

    """

    Takes list of strings `matrix_str` to parse the matrix and calculates the max sum.



    >>> solution(["1 2", "3 4"])

    5

    >>> solution(MATRIX_1)

    3315

    """



    n = len(matrix_str)

    arr = np.empty(shape=(n, n), dtype=int)

    for row, matrix_row_str in enumerate(matrix_str):

    # 遍历循环

        matrix_row_list_str = matrix_row_str.split()

        for col, elem_str in enumerate(matrix_row_list_str):

    # 遍历循环

            arr[row, col] = int(elem_str)



    cache: dict[str, int] = {}

    return solve(arr=arr, row=0, cols=set(range(n)), cache=cache)

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

