# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / unknown_sort

本文件实现 unknown_sort 相关的算法功能。
"""

# merge_sort 函数实现
def merge_sort(collection: list) -> list:
    """Pure implementation of the fastest merge sort algorithm in Python

    :param collection: some mutable ordered collection with heterogeneous
    comparable items inside
    :return: a collection ordered by ascending

    Examples:
    >>> merge_sort([0, 5, 3, 2, 2])
    [0, 2, 2, 3, 5]

    >>> merge_sort([])
    []

    >>> merge_sort([-2, -5, -45])
    [-45, -5, -2]
    """
    start, end = [], []
    while len(collection) > 1:
    # 条件循环
        min_one, max_one = min(collection), max(collection)
        start.append(min_one)
        end.append(max_one)
        collection.remove(min_one)
        collection.remove(max_one)
    end.reverse()
    return start + collection + end
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    user_input = input("Enter numbers separated by a comma:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(*merge_sort(unsorted), sep=",")
