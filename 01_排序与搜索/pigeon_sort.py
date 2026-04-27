# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / pigeon_sort

本文件实现 pigeon_sort 相关的算法功能。
"""

from __future__ import annotations

"""
This is an implementation of Pigeon Hole Sort.
For doctests run following command:

python3 -m doctest -v pigeon_sort.py
or
python -m doctest -v pigeon_sort.py

For manual testing run:
python pigeon_sort.py
"""




# pigeon_sort 函数实现
def pigeon_sort(array: list[int]) -> list[int]:
    """
    Implementation of pigeon hole sort algorithm
    :param array: Collection of comparable items
    :return: Collection sorted in ascending order
    >>> pigeon_sort([0, 5, 3, 2, 2])
    [0, 2, 2, 3, 5]
    >>> pigeon_sort([])
    []
    >>> pigeon_sort([-2, -5, -45])
    [-45, -5, -2]
    """
    if len(array) == 0:
    # 条件判断
        return array
    # 返回结果

    _min, _max = min(array), max(array)

    # Compute the variables
    holes_range = _max - _min + 1
    holes, holes_repeat = [0] * holes_range, [0] * holes_range

    # Make the sorting.
    for i in array:
    # 遍历循环
        index = i - _min
        holes[index] = i
        holes_repeat[index] += 1

    # Makes the array back by replacing the numbers.
    index = 0
    for i in range(holes_range):
    # 遍历循环
        while holes_repeat[i] > 0:
    # 条件循环
            array[index] = holes[i]
            index += 1
            holes_repeat[i] -= 1

    # Returns the sorted array.
    return array
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    user_input = input("Enter numbers separated by comma:\n")
    unsorted = [int(x) for x in user_input.split(",")]
    print(pigeon_sort(unsorted))
