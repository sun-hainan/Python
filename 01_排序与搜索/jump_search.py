# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / jump_search



本文件实现 jump_search 相关的算法功能。

"""



import math

from collections.abc import Sequence

from typing import Any, Protocol





class Comparable(Protocol):



# __lt__ 函数实现

    def __lt__(self, other: Any, /) -> bool: ...







# jump_search 函数实现

def jump_search[T: Comparable](arr: Sequence[T], item: T) -> int:

    """

    Python implementation of the jump search algorithm.

    Return the index if the `item` is found, otherwise return -1.



    Examples:

    >>> jump_search([0, 1, 2, 3, 4, 5], 3)

    3

    >>> jump_search([-5, -2, -1], -1)

    2

    >>> jump_search([0, 5, 10, 20], 8)

    -1

    >>> jump_search([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610], 55)

    10

    >>> jump_search(["aa", "bb", "cc", "dd", "ee", "ff"], "ee")

    4

    """



    arr_size = len(arr)

    block_size = int(math.sqrt(arr_size))



    prev = 0

    step = block_size

    while arr[min(step, arr_size) - 1] < item:

    # 条件循环

        prev = step

        step += block_size

        if prev >= arr_size:

    # 条件判断

            return -1

    # 返回结果



    while arr[prev] < item:

    # 条件循环

        prev += 1

        if prev == min(step, arr_size):

    # 条件判断

            return -1

    # 返回结果

    if arr[prev] == item:

    # 条件判断

        return prev

    # 返回结果

    return -1

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    user_input = input("Enter numbers separated by a comma:\n").strip()

    array = [int(item) for item in user_input.split(",")]

    x = int(input("Enter the number to be searched:\n"))



    res = jump_search(array, x)

    if res == -1:

    # 条件判断

        print("Number not found!")

    else:

        print(f"Number {x} is at index {res}")

