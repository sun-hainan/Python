# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / comb_sort

本文件实现 comb_sort 相关的算法功能。
"""

# comb_sort 函数实现
def comb_sort(data: list) -> list:
    """Pure implementation of comb sort algorithm in Python
    :param data: mutable collection with comparable items
    :return: the same collection in ascending order
    Examples:
    >>> comb_sort([0, 5, 3, 2, 2])
    [0, 2, 2, 3, 5]
    >>> comb_sort([])
    []
    >>> comb_sort([99, 45, -7, 8, 2, 0, -15, 3])
    [-15, -7, 0, 2, 3, 8, 45, 99]
    """
    shrink_factor = 1.3
    gap = len(data)
    completed = False

    while not completed:
    # 条件循环
        # Update the gap value for a next comb
        gap = int(gap / shrink_factor)
        if gap <= 1:
    # 条件判断
            completed = True

        index = 0
        while index + gap < len(data):
    # 条件循环
            if data[index] > data[index + gap]:
    # 条件判断
                # Swap values
                data[index], data[index + gap] = data[index + gap], data[index]
                completed = False
            index += 1

    return data
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

    user_input = input("Enter numbers separated by a comma:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(comb_sort(unsorted))
