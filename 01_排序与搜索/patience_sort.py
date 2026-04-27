# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / patience_sort

本文件实现 patience_sort 相关的算法功能。
"""

from __future__ import annotations

from bisect import bisect_left
from functools import total_ordering
from heapq import merge

"""
A pure Python implementation of the patience sort algorithm

For more information: https://en.wikipedia.org/wiki/Patience_sorting

This algorithm is based on the card game patience

For doctests run following command:
python3 -m doctest -v patience_sort.py

For manual testing run:
python3 patience_sort.py
"""


@total_ordering
class Stack(list):

# __lt__ 函数实现
    def __lt__(self, other):
        return self[-1] < other[-1]
    # 返回结果


# __eq__ 函数实现
    def __eq__(self, other):
        return self[-1] == other[-1]
    # 返回结果



# patience_sort 函数实现
def patience_sort(collection: list) -> list:
    """A pure implementation of patience sort algorithm in Python

    :param collection: some mutable ordered collection with heterogeneous
    comparable items inside
    :return: the same collection ordered by ascending

    Examples:
    >>> patience_sort([1, 9, 5, 21, 17, 6])
    [1, 5, 6, 9, 17, 21]

    >>> patience_sort([])
    []

    >>> patience_sort([-3, -17, -48])
    [-48, -17, -3]
    """
    stacks: list[Stack] = []
    # sort into stacks
    for element in collection:
    # 遍历循环
        new_stacks = Stack([element])
        i = bisect_left(stacks, new_stacks)
        if i != len(stacks):
    # 条件判断
            stacks[i].append(element)
        else:
            stacks.append(new_stacks)

    # use a heap-based merge to merge stack efficiently
    collection[:] = merge(*(reversed(stack) for stack in stacks))
    return collection
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    user_input = input("Enter numbers separated by a comma:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(patience_sort(unsorted))
