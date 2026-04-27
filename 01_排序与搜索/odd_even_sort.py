# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / odd_even_sort

本文件实现 odd_even_sort 相关的算法功能。
"""

# odd_even_sort 函数实现
def odd_even_sort(input_list: list) -> list:
    """
    Sort input with odd even sort.

    This algorithm uses the same idea of bubblesort,
    but by first dividing in two phase (odd and even).
    Originally developed for use on parallel processors
    with local interconnections.
    :param collection: mutable ordered sequence of elements
    :return: same collection in ascending order
    Examples:
    >>> odd_even_sort([5 , 4 ,3 ,2 ,1])
    [1, 2, 3, 4, 5]
    >>> odd_even_sort([])
    []
    >>> odd_even_sort([-10 ,-1 ,10 ,2])
    [-10, -1, 2, 10]
    >>> odd_even_sort([1 ,2 ,3 ,4])
    [1, 2, 3, 4]
    """
    is_sorted = False
    while is_sorted is False:  # Until all the indices are traversed keep looping
    # 条件循环
        is_sorted = True
        for i in range(0, len(input_list) - 1, 2):  # iterating over all even indices
    # 遍历循环
            if input_list[i] > input_list[i + 1]:
    # 条件判断
                input_list[i], input_list[i + 1] = input_list[i + 1], input_list[i]
                # swapping if elements not in order
                is_sorted = False

        for i in range(1, len(input_list) - 1, 2):  # iterating over all odd indices
    # 遍历循环
            if input_list[i] > input_list[i + 1]:
    # 条件判断
                input_list[i], input_list[i + 1] = input_list[i + 1], input_list[i]
                # swapping if elements not in order
                is_sorted = False
    return input_list
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    print("Enter list to be sorted")
    input_list = [int(x) for x in input().split()]
    # inputing elements of the list in one line
    sorted_list = odd_even_sort(input_list)
    print("The sorted list is")
    print(sorted_list)
