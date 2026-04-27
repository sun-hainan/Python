# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / double_linear_search

本文件实现 double_linear_search 相关的算法功能。
"""

from __future__ import annotations



# double_linear_search 函数实现
def double_linear_search(array: list[int], search_item: int) -> int:
    """
    Iterate through the array from both sides to find the index of search_item.

    :param array: the array to be searched
    :param search_item: the item to be searched
    :return the index of search_item, if search_item is in array, else -1

    Examples:
    >>> double_linear_search([1, 5, 5, 10], 1)
    0
    >>> double_linear_search([1, 5, 5, 10], 5)
    1
    >>> double_linear_search([1, 5, 5, 10], 100)
    -1
    >>> double_linear_search([1, 5, 5, 10], 10)
    3
    """
    # define the start and end index of the given array
    start_ind, end_ind = 0, len(array) - 1
    while start_ind <= end_ind:
    # 条件循环
        if array[start_ind] == search_item:
    # 条件判断
            return start_ind
    # 返回结果
        elif array[end_ind] == search_item:
            return end_ind
    # 返回结果
        else:
            start_ind += 1
            end_ind -= 1
    # returns -1 if search_item is not found in array
    return -1
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    print(double_linear_search(list(range(100)), 40))
